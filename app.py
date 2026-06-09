import json
import os
import unicodedata

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

def _normalizar(nombre):
    """Lowercase + sin acentos para comparación de nombres de municipio."""
    n = nombre.lower().strip()
    n = unicodedata.normalize("NFD", n)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return n


# Palabras clave para mapear nombre OSM de comarca -> nombre de ZONA del código
_COMARCA_A_ZONA = {
    "alacanti":   "L'Alacantí",
    "vinalopo":   "Vinalopó",
    "vinalop":    "Vinalopó",
    "vega baja":  "Vega Baja",
    "segura":     "Vega Baja",
    "marina alta":"Marina Alta",
    "marina baixa":"Marina Baixa",
    "marina baja":"Marina Baixa",
    "alcoia":     "Interior / Alcoià – Comtat",
    "alcoy":      "Interior / Alcoià – Comtat",
    "comtat":     "Interior / Alcoià – Comtat",
}

def _comarca_a_zona(nombre_osm):
    n = _normalizar(nombre_osm)
    for clave, zona in _COMARCA_A_ZONA.items():
        if clave in n:
            return zona
    return None


@app.route("/api/municipios-geojson")
def municipios_geojson():
    geojson_path = os.path.join(app.root_path, "static", "alicante_zonas.geojson")
    if not os.path.exists(geojson_path):
        return jsonify({"error": "Ejecuta primero: python scripts/descargar_geojson.py"}), 404

    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    # Media por zona
    zona_nivel = {}
    for zona_nombre, municipios_zona in ZONAS.items():
        registros = Ayuntamiento.query.filter(Ayuntamiento.nombre.in_(municipios_zona)).all()
        valores = [a.nivel_digitalizacion for a in registros if a.nivel_digitalizacion is not None]
        zona_nivel[zona_nombre] = round(sum(valores) / len(valores), 2) if valores else None

    for feature in geojson.get("features", []):
        props = feature["properties"]
        nombre_osm = props.get("nombre_es") or props.get("nombre", "")
        zona_nombre = _comarca_a_zona(nombre_osm)
        props["zona"] = zona_nombre
        props["nivel"] = zona_nivel.get(zona_nombre) if zona_nombre else None

    return jsonify(geojson)


@app.route("/api/municipios")
def municipios():

    aytos = Ayuntamiento.query.all()

    return jsonify([{
        "nombre": a.nombre,
        "nivel": a.nivel_digitalizacion,
        "lat": a.latitud,
        "lon": a.longitud
    } for a in aytos if a.latitud and a.longitud])

#######################################
##         DETAILS
#####################################
@app.route("/municipio/<nombre>")
def detalle_municipio(nombre):

    ayto = Ayuntamiento.query.filter_by(nombre=nombre).first()

    if not ayto:
        return "Municipio no encontrado", 404

    return render_template("details.html", ayto=ayto)

@app.route("/api/municipio/<nombre>")
def api_municipio(nombre):

    a = Ayuntamiento.query.filter_by(nombre=nombre).first()

    if not a:
        return jsonify({"error": "No encontrado"}), 404

    return jsonify({
        "nombre": a.nombre,
        "nivel": a.nivel_digitalizacion,
        "areas": {
            "comunicaciones": a.comunicaciones,
            "backoffice": a.backoffice,
            "puestos": a.puestos_trabajo,
            "frontoffice": a.frontoffice,
            "smart": a.smart_city,
            "dti": a.dti,
            "planes": a.planes
        }
    })

@app.route("/api/comparativa/<nombre>")
def comparativa(nombre):

    ayto = Ayuntamiento.query.filter_by(nombre=nombre).first()

    if not ayto:
        return jsonify({"error": "No encontrado"}), 404

    # TOP 2 mejores
    top = Ayuntamiento.query.order_by(
        Ayuntamiento.nivel_digitalizacion.desc()
    ).limit(2).all()

    # TOP 5 ranking
    top5 = Ayuntamiento.query.order_by(
        Ayuntamiento.nivel_digitalizacion.desc()
    ).limit(5).all()

    # TOP 2 peores
    bottom = Ayuntamiento.query.order_by(
        Ayuntamiento.nivel_digitalizacion.asc()
    ).limit(2).all()

    def extraer(a):
        return {
            "nombre": a.nombre,
            "comunicaciones": a.comunicaciones or 0,
            "backoffice": a.backoffice or 0,
            "puestos": a.puestos_trabajo or 0,
            "frontoffice": a.frontoffice or 0,
            "smart": a.smart_city or 0,
            "dti": a.dti or 0,
            "planes": a.planes or 0
        }

    def extraer_ranking(a):
        return {
            "nombre": a.nombre,
            "nivel": round(a.nivel_digitalizacion or 0, 2)
        }

    return jsonify({
        "actual": extraer(ayto),
        "top": [extraer(a) for a in top],
        "bottom": [extraer(a) for a in bottom],
        "top5": [extraer_ranking(a) for a in top5]
    })

from sqlalchemy import func

@app.route("/api/buscar")
def buscar():

    q = request.args.get("q", "").lower()

    if not q:
        return jsonify([])

    resultados = Ayuntamiento.query.filter(
        func.lower(Ayuntamiento.nombre).contains(q)
    ).limit(5).all()

    return jsonify([a.nombre for a in resultados])

#################################
##          MAPA
################################
@app.route("/admin/cargar-coords")
def cargar_coords():

    coords = {
        "Alicante": (38.3452, -0.481),
        "Elche": (38.2699, -0.712),
        "Benidorm": (38.541, -0.122),
        "Alcoy": (38.698, -0.473),
        "Torrevieja": (37.978, -0.683),
        "Orihuela": (38.085, -0.944),
        "Elda": (38.478, -0.791),
        "Villena": (38.636, -0.865),
        "Calpe": (38.644, 0.045),
        "Dénia": (38.840, 0.105)
    }

    aytos = Ayuntamiento.query.all()

    actualizados = 0  # contador

    for a in aytos:
        for nombre, (lat, lon) in coords.items():
            if nombre.lower() in a.nombre.lower():
                a.latitud = lat
                a.longitud = lon
                actualizados += 1

    db.session.commit()

    return f"Actualizados: {actualizados}"

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
