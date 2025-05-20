from minio import Minio
from app.config import Settings
from app.utils.singleton import singleton

BUCKET = Settings.MINIO_BUCKET

@singleton
class MinioStorage():
    def __init__(self) -> None:
        self.client = Minio(Settings.MINIO_HOST,
            access_key=Settings.MINIO_ACCESS_KEY,
            secret_key=Settings.MINIO_SECRET_KEY,
            secure=False,
        )

    def get_client(self):
        return self.client