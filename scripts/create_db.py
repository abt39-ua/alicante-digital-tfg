import os
import sys

# Permite importar desde la raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from models import db


def run():

    db_path = "database.db"

    # BORRAR BD ANTIGUA (CLAVE)
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Base de datos antigua eliminada")

    with app.app_context():
        db.create_all()
        print("✅ Base de datos creada correctamente")


if __name__ == "__main__":
    run()
