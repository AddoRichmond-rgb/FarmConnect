"""Application configuration.

All settings are read from environment variables (see .env.example) so that
secrets never live in source control.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Security -------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    WTF_CSRF_ENABLED = True                  # CSRF protection on every POST
    SESSION_COOKIE_HTTPONLY = True           # JS cannot read the session cookie
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours

    # --- Database (MySQL) ----------------------------------------------
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB = os.getenv("MYSQL_DB", "farmconnect")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # --- Uploads ---------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024      # 5 MB per request

    # --- Business --------------------------------------------------------
    PRODUCTS_PER_PAGE = 12
