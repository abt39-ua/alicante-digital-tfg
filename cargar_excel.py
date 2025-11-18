import pandas as pd
import random
import string
from werkzeug.security import generate_password_hash
from app import app
from models import db, Ayuntamiento, Usuario

EXCEL_FILE = "Sensitivity_Analysis.xlsx"
COLUMN_NAME = "AYUNTAMIENTO"

def generar_codigo(numero):
    return f"{numero:03d}"

def generar_password():
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=9))

def main():
    df = pd.read_excel(EXCEL_FILE)

    if COLUMN_NAME not in df.columns:
        print(f"❌ ERROR: La columna '{COLUMN_NAME}' no existe en el Excel.")
        return

    print("📥 Importando ayuntamientos...")

    with app.app_context():
        db.session.query(Usuario).delete()
        db.session.query(Ayuntamiento).delete()
        db.session.commit()

        claves = []  # para mostrar luego al usuario

        for index, row in df.iterrows():
            nombre = str(row[COLUMN_NAME]).strip()
            codigo = generar_codigo(index + 1)

            password_plano = generar_password()
            password_hash = generate_password_hash(password_plano)

            ayto = Ayuntamiento(
                codigo=codigo,
                nombre=nombre,
                nivel_digitalizacion=0
            )

            user = Usuario(
                ayuntamiento=ayto,
                password_hash=password_hash
            )

            db.session.add(ayto)
            db.session.add(user)

            claves.append((nombre, codigo, password_plano))

        db.session.commit()

        print("\n✅ Importación completada.\n")
        print("🔑 CREDENCIALES GENERADAS:")
        for nombre, codigo, password in claves:
            print(f"{codigo}  |  {nombre}  |  {password}")

        print("\n💾 Guarda esta información en un archivo seguro.\n")

if __name__ == "__main__":
    main()
