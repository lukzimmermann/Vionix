from math import floor
from turtle import st

from sqlalchemy import over
from app.models import Chunk, Video
from app.utils import database
from app.utils.database import Database
from sentence_transformers import SentenceTransformer


class ChunkCreator():
    def __init__(self):
            self.__database = Database().get_session()
            self.__model = SentenceTransformer('BAAI/bge-base-en-v1.5')
            self.tokenizer = self.__model.tokenizer

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
                    chunk.embedding = self.__model.encode(chunk.text, convert_to_tensor=False, normalize_embeddings=True)
                    chunks.append(chunk)

                    self.__database.add(chunk)
                    self.__database.commit()

                    chunk = Chunk()
                    chunk.start = round(segment['end'], 1)
                    chunk.video_id = video_id
                    chunk.text = ""

    def token_based(self, video_id, size: int, overlap: int):
        video = self.__database.query(Video).where(Video.id == video_id).first()

        chunks = []
        chunks.append(self.create_new_chunk(video.id, 0))
        chunks.append(self.create_new_chunk(video.id, None))
        
        for segment in video.transcription['segments']:
            text = chunks[-2].text + segment['text']
            tokens = self.tokenizer.encode(text, add_special_tokens=False)

            chunks[-2].end = segment['end']
            chunks[-1].end = segment['end']

            if len(tokens) > size - overlap:
                if len(chunks[-1].text) == 0:
                    chunks[-1].start = segment['start']
                chunks[-1].text += segment['text']

            if len(tokens) < size:
                chunks[-2].text += segment['text']
                chunks[-2].embedding = self.__model.encode(chunks[-2].text, convert_to_tensor=False, normalize_embeddings=True)
            else:
                chunks.append(self.create_new_chunk(video.id, None))

        if chunks[-1].start == None or chunks[-1].end == chunks[-1].end:
            chunks.pop()

        if (len(self.tokenizer.encode(chunks[-1].text, add_special_tokens=False)) + len(self.tokenizer.encode(chunks[-2].text, add_special_tokens=False))) < size:
            chunks[-2].text += chunks[-1].text
            chunks.pop()

        return chunks
    
    def create_new_chunk(self, video_id, start):
        chunk = Chunk()
        chunk.video_id = video_id
        chunk.start = start
        chunk.text = ""

        return chunk



                
    
    