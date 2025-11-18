import pandas as pd
import string
import random
from app import db, Ayuntamiento, Usuario
from passlib.hash import bcrypt

def generar_password():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=9))

def run():
    df = pd.read_excel("data/ayuntamientos.xlsx")

    for index, row in df.iterrows():
        codigo = f"{index+1:03d}"
        nombre = row["nombre"]
        
        ayto = Ayuntamiento(codigo=codigo, nombre=nombre, datos={})
        db.session.add(ayto)

        pwd = generar_password()
        usuario = Usuario(
            codigo=codigo,
            password_hash=bcrypt.hash(pwd)
        )
        db.session.add(usuario)

        print(f"{nombre} → {codigo} → {pwd}")

    db.session.commit()

if __name__ == "__main__":
    run()
