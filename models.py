from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ayuntamiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    codigo = db.Column(db.String(3), unique=True, nullable=False)
    nombre = db.Column(db.String(255), unique=True, nullable=False)

    # Dimensiones de digitalización
    comunicaciones = db.Column(db.Float)
    backoffice = db.Column(db.Float)
    puestos_trabajo = db.Column(db.Float)
    frontoffice = db.Column(db.Float)
    smart_city = db.Column(db.Float)
    dti = db.Column(db.Float)
    planes = db.Column(db.Float)

    # Nivel global
    total = db.Column(db.Float)

    # Acceso
    password_hash = db.Column(db.String(255), nullable=False)

