import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL")

# --- JWT ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# --- App ---
APP_NAME = os.getenv("APP_NAME")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

# --- Admin seed ---
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# --- SCORM storage ---
_raw_path = os.getenv("SCORM_STORAGE_PATH")
SCORM_STORAGE_PATH: Path = Path(_raw_path)
if not SCORM_STORAGE_PATH.is_absolute():
    # Resolve relative paths from the backend root (one level above app/)
    SCORM_STORAGE_PATH = Path(__file__).resolve().parent.parent / _raw_path

SCORM_MAX_ZIP_BYTES = int(os.getenv("SCORM_MAX_ZIP_BYTES"))
