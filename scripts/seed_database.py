"""
Script para inicializar la base de datos desde cero.

⚠️ USAR SOLO CUANDO LA BASE DE DATOS ESTÉ VACÍA
⚠️ Se puede volver a ejecutar si Render borra la BD

Ejecutar con:
python scripts/seed_database.py
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app import app
from models import db, Ayuntamiento, Usuario
from werkzeug.security import generate_password_hash
import random
import string


def generar_password():
    """Genera una contraseña de 9 caracteres (letras y números)"""
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=9)
    )


def crear_usuarios_y_ayuntamientos():
    """
    Crea los ayuntamientos y sus usuarios asociados.
    Modifica aquí la lista si cambia el Excel.
    """

    ayuntamientos = [
        "Alicante",
        "Elche",
        "Benidorm",
        "Torrevieja",
        "Orihuela",
        "Alcoy",
        "San Vicente del Raspeig",
        # añade los que quieras
    ]

    with app.app_context():
        for i, nombre in enumerate(ayuntamientos, start=1):
            codigo = f"{i:03d}"  # 001, 002, 003...

            # Evitar duplicados
            if Ayuntamiento.query.filter_by(codigo=codigo).first():
                continue

            ayto = Ayuntamiento(
                nombre=nombre,
                codigo=codigo,
                nivel_digitalizacion=0
            )
            db.session.add(ayto)
            db.session.flush()  # para obtener ayto.id

            password_plana = generar_password()
            usuario = Usuario(
                ayuntamiento_id=ayto.id,
                password_hash=generate_password_hash(password_plana)
            )
            db.session.add(usuario)

            print(
                f"Ayuntamiento: {nombre} | Código: {codigo} | Password: {password_plana}"
            )

        db.session.commit()
        print("✅ Base de datos inicializada correctamente")


if __name__ == "__main__":
    crear_usuarios_y_ayuntamientos()
