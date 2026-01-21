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
