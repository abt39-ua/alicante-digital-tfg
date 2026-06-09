"""
Crea las tablas en la base de datos y migra columnas nuevas.
Ejecutar después de crear una BD nueva o al añadir campos al modelo.

Uso: python scripts/crear_tablas.py
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import inspect, text
from app import app
from models import db

with app.app_context():
    db.create_all()

    inspector = inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns("ayuntamiento")]

    if "comentarios" not in cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE ayuntamiento ADD COLUMN comentarios TEXT"))
            conn.commit()
        print("Columna 'comentarios' añadida.")

    print("Tablas actualizadas correctamente.")
    print("URI:", app.config["SQLALCHEMY_DATABASE_URI"][:60], "...")
