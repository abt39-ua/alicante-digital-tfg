from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ayuntamiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(3), unique=True, nullable=False)
    nombre = db.Column(db.String(255), unique=True, nullable=False)
    nivel_digitalizacion = db.Column(db.Integer, default=0)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ayuntamiento_id = db.Column(db.Integer, db.ForeignKey("ayuntamiento.id"))
    password_hash = db.Column(db.String(255), nullable=False)

    ayuntamiento = db.relationship("Ayuntamiento", backref="usuarios")
