import os
import time
import whisper
import logging
from app.models import Video
from app.utils.database import Database
from app.utils.logger import get_logger
from app.utils.singleton import singleton
from app.utils.minioStorage import MinioStorage, BUCKET

logger = get_logger('worker_logger', logging.DEBUG)

@singleton
class Transcription():
    def __init__(self, model="medium"):
        self.__model = whisper.load_model(model, device="cpu")
        self.__database = Database().get_session()
        self.__minio_client = MinioStorage().get_client()
        self.__temp_directory = "./temp/"

    def transcribe(self, video_id: int):
        try:
            start_time = time.time()
            logger.debug(f"Start transcription of video: {video_id}")

            video = self.__database.query(Video).where(Video.id == video_id).first()

            self.download_audio(video.audio_path)
            transcription = self.transcribe_audio(self.__temp_directory+video.audio_path)
            self.save_in_database(video.id, transcription)

            logger.info(f"Finished transcription of {video_id} after {time.time()-start_time:.1f}s")

        except Exception as e:
            logger.error(f"Error during transcription of video ({video_id})", exc_info=True)
        finally:
            self.clean_up(self.__temp_directory+video.audio_path)


    def transcribe_audio(self, filename):
        return self.__model.transcribe(filename)
    
    def save_in_database(self, video_id, transcription):
        video = self.__database.query(Video).filter_by(id=video_id).first()

        if video:
            video.language = transcription['language']
            video.transcription = transcription
            self.__database.commit()

    def download_audio(self, filename: str):
        objects = self.__minio_client.get_object(BUCKET, filename)
        file_path = self.__temp_directory+filename

        with open(file_path, "wb") as file_data:
            for data in objects.stream(32*1024):
                file_data.write(data)
    
    def clean_up(self, filename: str):
        os.remove(filename)

    