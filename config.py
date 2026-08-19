from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"{name} 未設定")
        # return "d"
    return value


# DB_PATH = require_env("DB_PATH")

# FLASK_SECRET_KEY = require_env("FLASK_SECRET_KEY")


def get_db_path():
    return require_env("DB_PATH")

def get_secret_key():
    return require_env("FLASK_SECRET_KEY")

def get_session_time():
    return timedelta(minutes=30)
