"""
SCRIPT DE CARGA / REGENERACIÓN DE AYUNTAMIENTOS

- Lee los ayuntamientos desde el Excel original del TFG
- Genera códigos (001, 002, ...)
- Genera contraseñas aleatorias
- Guarda todo en la base de datos (remota o local)

USAR CUANDO:
- Se pierde la base de datos (Render free)
- Se redepliega el proyecto
- Se empieza desde cero

EJECUTAR:
python scripts/cargar_ayuntamientos.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import random
import string
from werkzeug.security import generate_password_hash
from app import app
from models import db, Ayuntamiento


EXCEL_FILE = "Sensitivity_Analysis.xlsx"
COLUMN_NAME = "AYUNTAMIENTO"


def generar_codigo(numero):
    return f"{numero:03d}"


def generar_password():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=9))


def run():
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ ERROR: No se encuentra el archivo {EXCEL_FILE}")
        return

    df = pd.read_excel(EXCEL_FILE)

    if COLUMN_NAME not in df.columns:
        print(f"❌ ERROR: La columna '{COLUMN_NAME}' no existe en el Excel.")
        return

    print("📥 Importando ayuntamientos desde Excel...\n")

    with app.app_context():
        # ⚠️ BORRADO TOTAL (solo para regeneración)
        db.session.query(Ayuntamiento).delete()
        db.session.commit()

        credenciales = []

        for index, row in df.iterrows():
            nombre = str(row[COLUMN_NAME]).strip()
            codigo = generar_codigo(index + 1)

            password_plano = generar_password()
            password_hash = generate_password_hash(password_plano)

            ayto = Ayuntamiento(
                codigo=codigo,
                nombre=nombre,
                password_hash=password_hash,
                nivel_digitalizacion=0
            )

            db.session.add(ayto)
            credenciales.append((codigo, nombre, password_plano))

        db.session.commit()

    print("✅ Importación completada.\n")
    print("🔑 CREDENCIALES GENERADAS (GUÁRDALAS):\n")

    for codigo, nombre, password in credenciales:
        print(f"{codigo}  |  {nombre}  |  {password}")

    print("\n💾 Guarda esta información en un archivo seguro.\n")


if __name__ == "__main__":
    run()
