"""
Carga completa de ayuntamientos desde Sensitivity_Analysis.xlsx

- Guarda todas las dimensiones de digitalización
- Genera códigos y contraseñas
- Pensado para regenerar la BD cuando se pierda (Render free)

EJECUTAR:
python scripts/cargar_ayuntamientos.py
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

import pandas as pd
import random
import string
from werkzeug.security import generate_password_hash
from app import app
from models import db, Ayuntamiento


EXCEL_FILE = "Sensitivity_Analysis.xlsx"

COLUMN_MAP = {
    "AYUNTAMIENTO": "nombre",
    "comunicaciones": "comunicaciones",
    "backoffice": "backoffice",
    "puestos de trabajo": "puestos_trabajo",
    "frontoffice": "frontoffice",
    "smart city": "smart_city",
    "DTI": "dti",
    "planes": "planes",
    "TOTAL": "total"
}


def generar_codigo(n):
    return f"{n:03d}"


def generar_password():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=9))


def run():
    df = pd.read_excel(EXCEL_FILE)

    print("📥 Cargando ayuntamientos desde Excel...\n")

    with app.app_context():
        db.session.query(Ayuntamiento).delete()
        db.session.commit()

        credenciales = []

        for idx, row in df.iterrows():
            data = {}

            for excel_col, model_col in COLUMN_MAP.items():
                data[model_col] = float(row[excel_col]) if excel_col != "AYUNTAMIENTO" else str(row[excel_col]).strip()

            pwd = generar_password()

            ayto = Ayuntamiento(
                codigo=generar_codigo(idx + 1),
                password_hash=generate_password_hash(pwd),
                **data
            )

            db.session.add(ayto)
            credenciales.append((ayto.codigo, ayto.nombre, pwd))

        db.session.commit()

    print("✅ Importación completada\n")
    print("🔑 CREDENCIALES GENERADAS:\n")

    for c, n, p in credenciales:
        print(f"{c} | {n} | {p}")

    print("\n💾 Guarda estas contraseñas en un lugar seguro.\n")


if __name__ == "__main__":
    run()
