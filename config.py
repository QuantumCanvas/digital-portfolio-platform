import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _database_url():
    """Return a SQLAlchemy URL that works locally and on Vercel.

    Vercel's deployment filesystem is not persistent, so production should set
    DATABASE_URL to a managed PostgreSQL database (Neon/Supabase/etc.).
    Without it, Vercel uses /tmp only as a demo fallback.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        # SQLAlchemy + psycopg 3 driver.
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/skillpulse.db"

    return f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
