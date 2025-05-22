import os
from dotenv import load_dotenv

ACTIVE_ENV = os.getenv("ACTIVE_ENV", "local")

dotenv_path = os.path.join(os.path.dirname(__file__), f"../.env.{ACTIVE_ENV}")
load_dotenv(dotenv_path=dotenv_path, override=True)

class Settings:
    ENV = os.getenv("ENV", ACTIVE_ENV)
    DATABASE_URL = os.getenv("DATABASE_URL")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET")
    MINIO_HOST = os.getenv("MINIO_HOST")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    PROXY_LIST_PATH = os.getenv("PROXY_LIST_PATH")

