import os
from minio import Minio
from dotenv import load_dotenv
from app.utils.singleton import singleton

load_dotenv()

BUCKET = os.getenv('MINIO_BUCKET')

@singleton
class MinioStorage():
    def __init__(self) -> None:
        self.client = Minio(os.getenv('MINIO_HOST'),
            access_key=os.getenv('MINIO_ACCESS_KEY'),
            secret_key=os.getenv('MINIO_SECRET_KEY'),
            secure=False,
        )

    def get_client(self):
        return self.client