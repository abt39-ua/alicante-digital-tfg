from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Ayuntamiento
from config import Config
from functools import wraps
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

############################################
# LOGIN REQUIRED
############################################

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "ayuntamiento_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


############################################
# ZONAS COMPLETAS (79 municipios)
############################################

ZONAS = {

"L’Alacantí": [
"Alicante","San Vicente del Raspeig","San Juan","Mutxamel",
"El Campello","Aigües","Busot"
],

"Vinalopó": [
"Elche","Elda","Petrer","Novelda","Monóvar","Aspe","Sax",
"Villena","Pinoso","Hondón de las Nieves","Hondón de los Frailes","Salinas"
],

"Vega Baja": [
"Orihuela","Torrevieja","Guardamar","Pilar de la Horadada","Rojales",
"Almoradí","Callosa de Segura","Dolores","Cox","Catral","Redován",
"Bigastro","San Fulgencio","Formentera del Segura","Daya Vieja",
"Daya Nueva","Algorfa","Benejúzar","Benferri","Rafal"
],

"Marina Alta": [
"Dénia","Jávea","Calpe","Teulada","Benissa","Pego","Gata de Gorgos",
"Ondara","Pedreguer","El Verger","Els Poblets","Beniarbeig","Orba",
"Alcalalí","Parcent","Benigembla","Murla","Sanet y Negrals"
],

"Marina Baixa": [
"Benidorm","Altea","La Nucía","Alfaz del Pi","Polop",
"Callosa d’en Sarrià","Finestrat","Bolulla","Tàrbena",
"Castell de Guadalest","Beniardà","Benifato","Confrides",
"Relleu","Sella","Orxeta"
],

"Interior / Alcoià – Comtat": [
"Alcoy","Ibi","Cocentaina","Muro","Banyeres","Castalla","Onil",
"Agres","Biar","Beneixama","Planes","L’Orxa","Quatretondeta",
"Benilloba","Benimarfull","Benifallim","Tollos"
]
}

############################################
# RUTAS PUBLICAS
############################################

@app.route("/")
def index():
    return render_template("index.html")


############################################
# LOGIN
############################################

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        codigo = request.form.get("codigo")
        password = request.form.get("password")

        ayto = Ayuntamiento.query.filter_by(codigo=codigo).first()

        if ayto and check_password_hash(ayto.password_hash, password):
            session["ayuntamiento_id"] = ayto.id
            return redirect(url_for("panel"))

        flash("Código o contraseña incorrectos", "error")

    return render_template("login.html")


############################################
# PANEL PRIVADO
############################################

@app.route("/panel", methods=["GET", "POST"])
@login_required
def panel():

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


############################################
# APIs PARA GRÁFICOS
############################################

# MEDIA GLOBAL

@app.route("/api/media-digitalizacion")
def media_digitalizacion():

    aytos = Ayuntamiento.query.all()

    valores = [a.nivel_digitalizacion for a in aytos if a.nivel_digitalizacion is not None]

    if not valores:
        return jsonify({"media": 0})

    media = sum(valores) / len(valores)

    max_ayto = max(aytos, key=lambda x: x.nivel_digitalizacion or 0)
    min_ayto = min(aytos, key=lambda x: x.nivel_digitalizacion or 0)

    return jsonify({
        "media": round(media, 2),
        "max": {
            "nombre": max_ayto.nombre,
            "valor": round(max_ayto.nivel_digitalizacion, 2)
        },
        "min": {
            "nombre": min_ayto.nombre,
            "valor": min_ayto.nivel_digitalizacion
        }
    })


############################################
# RANKING TOP 10
############################################

@app.route("/api/ranking")
def ranking():

    aytos = Ayuntamiento.query.order_by(
        Ayuntamiento.nivel_digitalizacion.desc()
    ).limit(10)

    return jsonify([
        {
            "nombre": a.nombre,
            "comunicaciones": a.comunicaciones or 0,
            "backoffice": a.backoffice or 0,
            "puestos_trabajo": a.puestos_trabajo or 0,
            "frontoffice": a.frontoffice or 0,
            "smart": a.smart_city or 0,
            "dti": a.dti or 0,
            "planes": a.planes or 0
        }
        for a in aytos
    ])


############################################
# MEDIA POR AREAS
############################################

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

        valores = [
            getattr(a, campo)
            for a in aytos
            if getattr(a, campo) is not None
        ]

        resultado[campo] = round(sum(valores) / len(valores), 2) if valores else 0

    return jsonify(resultado)


############################################
# DISTRIBUCION DE MADUREZ DIGITAL
############################################

@app.route("/api/distribucion")
def distribucion():

    aytos = Ayuntamiento.query.all()

    rangos = [(30,40),(40,50),(50,60),(60,70),(70,80),(80,90)]

    buckets = {
        f"{r[0]}-{r[1]}": {
            "total": 0,
            "municipios": []
        }
        for r in rangos
    }

    for a in aytos:

        v = a.nivel_digitalizacion

        if v is None:
            continue

        for r in rangos:

            if r[0] <= v < r[1]:

                bucket = buckets[f"{r[0]}-{r[1]}"]

                bucket["total"] += 1
                bucket["municipios"].append(a.nombre)

                break

    # eliminar vacíos
    buckets = {k:v for k,v in buckets.items() if v["total"]>0}

    return jsonify(buckets)




############################################
# MEDIA POR ZONAS (EL GRAFICO IMPORTANTE)
############################################

@app.route("/api/digitalizacion-zonas")
def digitalizacion_por_zonas():

    resultado = []

    for zona, municipios in ZONAS.items():

        registros = Ayuntamiento.query.filter(
            Ayuntamiento.nombre.in_(municipios)
        ).all()

        if not registros:
            continue

        valores = [a.nivel_digitalizacion for a in registros if a.nivel_digitalizacion is not None]

        if not valores:
            continue

        media = sum(valores) / len(valores)

        resultado.append({
            "zona": zona,
            "media": round(media, 2),
            "ayuntamientos": [a.nombre for a in registros]
        })

    return jsonify(resultado)

@app.route("/api/municipios")
def municipios():

    aytos = Ayuntamiento.query.all()

    return jsonify([{
        "nombre": a.nombre,
        "nivel": a.nivel_digitalizacion,
        "lat": a.latitud,
        "lon": a.longitud
    } for a in aytos if a.latitud and a.longitud])


############################################
# CREAR TABLAS
############################################

with app.app_context():
    db.create_all()


############################################
# RUN
############################################

if __name__ == "__main__":
    app.run(debug=True)
