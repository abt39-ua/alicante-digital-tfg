from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Ayuntamiento
from config import Config
from functools import wraps
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# ----------------------------
# Login required decorator
# ----------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "ayuntamiento_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        codigo = request.form.get("codigo")
        password = request.form.get("password")

        ayto = Ayuntamiento.query.filter_by(codigo=codigo).first()

        if ayto and check_password_hash(ayto.password_hash, password):
            session["ayuntamiento_id"] = ayto.id
            return redirect(url_for("dashboard"))

        flash("Código o contraseña incorrectos", "error")

    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    ayto = Ayuntamiento.query.get(session["ayuntamiento_id"])

    if request.method == "POST":
        nuevo_nivel = request.form.get("nivel_digitalizacion")
        if nuevo_nivel:
            ayto.nivel_digitalizacion = int(nuevo_nivel)
            db.session.commit()
            flash("Datos actualizados correctamente", "success")

    return render_template(
        "dashboard.html",
        ayto=ayto,
        nivel_digitalizacion=ayto.nivel_digitalizacion
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ----------------------------
# Crear tablas si no existen
# ----------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)


from flask import jsonify
from sqlalchemy import func

ZONAS = {
    "Marina Alta": ["Dénia", "Xàbia", "Calp", "Teulada", "Benissa"],
    "Marina Baixa": ["Benidorm", "Altea", "La Nucía", "Polop"],
    "Vinalopó": ["Elche", "Elda", "Petrer", "Novelda", "Aspe"],
    "L'Alacantí": ["Alicante", "San Vicente", "Mutxamel", "Sant Joan"],
    "Vega Baja": ["Orihuela", "Torrevieja", "Guardamar", "Pilar de la Horadada"]
}

@app.route("/api/digitalizacion-zonas")
def digitalizacion_por_zonas():
    resultado = []

    for zona, ayuntamientos in ZONAS.items():
        registros = Ayuntamiento.query.filter(
            Ayuntamiento.nombre.in_(ayuntamientos)
        ).all()

        if not registros:
            continue

        media = sum(a.nivel_digitalizacion for a in registros) / len(registros)

        resultado.append({
            "zona": zona,
            "media": round(media, 2),
            "ayuntamientos": [a.nombre for a in registros]
        })

    return jsonify(resultado)


@app.route("/api/media-digitalizacion")
def media_digitalizacion():

    aytos = Ayuntamiento.query.all()

    valores = [a.nivel_digitalizacion for a in aytos if a.nivel_digitalizacion]

    media = sum(valores) / len(valores)

    max_ayto = max(aytos, key=lambda x: x.nivel_digitalizacion)
    min_ayto = min(aytos, key=lambda x: x.nivel_digitalizacion)

    return {
        "media": round(media, 2),
        "max": {
            "nombre": max_ayto.nombre,
            "valor": max_ayto.nivel_digitalizacion
        },
        "min": {
            "nombre": min_ayto.nombre,
            "valor": min_ayto.nivel_digitalizacion
        }
    }


@app.route("/api/ranking")
def ranking():

    aytos = Ayuntamiento.query.order_by(
        Ayuntamiento.nivel_digitalizacion.desc()
    ).limit(10)

    return [{
        "nombre": a.nombre,
        "valor": a.nivel_digitalizacion
    } for a in aytos]


@app.route("/api/media-areas")
def media_areas():

    aytos = Ayuntamiento.query.all()

    campos = [
        "comunicaciones",
        "backoffice",
        "puestos_trabajo",
        "frontoffice",
        "smart_city",
        "dti",
        "planes"
    ]

    resultado = {}

    for campo in campos:
        valores = [getattr(a, campo) for a in aytos if getattr(a, campo) is not None]
        resultado[campo] = round(sum(valores) / len(valores), 2)

    return resultado


@app.route("/api/distribucion")
def distribucion():

    aytos = Ayuntamiento.query.all()

    buckets = {
        "Bajo": 0,
        "Medio-bajo": 0,
        "Medio": 0,
        "Alto": 0
    }

    for a in aytos:

        v = a.nivel_digitalizacion

        if v < 25:
            buckets["Bajo"] += 1
        elif v < 50:
            buckets["Medio-bajo"] += 1
        elif v < 75:
            buckets["Medio"] += 1
        else:
            buckets["Alto"] += 1

    return buckets
