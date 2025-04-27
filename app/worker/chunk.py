from math import floor
from app.models import Chunk, Video
from app.utils import database
from app.utils.database import Database
from sentence_transformers import SentenceTransformer


class ChunkCreator():
    def __init__(self):
            self.__database = Database().get_session()
            self.__model = SentenceTransformer('BAAI/bge-base-en-v1.5')

    def create_chunks(self, video_id, length=120):
        video = self.__database.query(Video).where(Video.id == video_id).first()
        chunks = []

        if video.transcription is not None:
            chunk = Chunk()
            chunk.start = 0
            chunk.video_id = video_id
            chunk.text = ""

            for segment in video.transcription['segments']:
                chunk.text += segment['text']
                if floor(segment['end'] / length) > len(chunks):
                    chunk.end = round(segment['end'], 1)
                    chunk.embedding = self.__model.encode(chunk.text, convert_to_tensor=False)
                    chunks.append(chunk)

                    self.__database.add(chunk)
                    self.__database.commit()

                    chunk = Chunk()
                    chunk.start = round(segment['end'], 1)
                    chunk.video_id = video_id
                    chunk.text = ""
                
    
    