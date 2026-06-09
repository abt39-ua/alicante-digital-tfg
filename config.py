import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:

        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql://",
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"sslmode": "require"}
        }

    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
