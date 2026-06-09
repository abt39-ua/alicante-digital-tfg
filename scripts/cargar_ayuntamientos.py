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


# Ruta REAL al excel
EXCEL_FILE = os.path.join(BASE_DIR, "Sensitivity_Analysis.xlsx")


COLUMN_MAP = {
    "AYUNTAMIENTO": "nombre",
    "comunicaciones": "comunicaciones",
    "backoffice": "backoffice",
    "puestos de trabajo": "puestos_trabajo",
    "frontoffice": "frontoffice",
    "smart city": "smart_city",
    "DTI": "dti",
    "planes": "planes",
    "TOTAL": "nivel_digitalizacion"
}


def generar_codigo(n):
    return f"{n:03d}"


def generar_password():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=9))


def safe_float(value):
    """
    Convierte a float evitando NaN.
    """
    if pd.isna(value):
        return None
    return float(value)


def run():

    df = pd.read_excel(EXCEL_FILE)

    df.columns = df.columns.str.strip()

    print("\Cargando ayuntamientos desde Excel...\n")

    with app.app_context():

        #  BORRA TODO (esto está bien para seeds)
        db.session.query(Ayuntamiento).delete()
        db.session.commit()

        credenciales = []

        for idx, row in df.iterrows():

            data = {}

            for excel_col, model_col in COLUMN_MAP.items():

                if excel_col == "AYUNTAMIENTO":
                    data[model_col] = str(row[excel_col]).strip()
                else:
                    data[model_col] = safe_float(row.get(excel_col))

            pwd = generar_password()

            ayto = Ayuntamiento(
                codigo=generar_codigo(idx + 1),
                password_hash=generate_password_hash(pwd),
                **data
            )

            db.session.add(ayto)

            credenciales.append({
                "codigo": ayto.codigo,
                "nombre": ayto.nombre,
                "password": pwd
            })

        db.session.commit()

    print(" Importación completada\n")

    print(" CREDENCIALES GENERADAS:\n")

    for c in credenciales:
        print(f"{c['codigo']} | {c['nombre']} | {c['password']}")

    print("\n Guarda estas contraseñas.\n")


if __name__ == "__main__":
    run()
    print(app.config["SQLALCHEMY_DATABASE_URI"])

