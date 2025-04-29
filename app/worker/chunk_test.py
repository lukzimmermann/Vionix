from app.models import Video
from app.worker.chunk import ChunkCreator
from app.utils.database import Database

session = Database().get_session()
videos = session.query(Video).all()
chunk_creator = ChunkCreator()

tokens = 1000
chunks = chunk_creator.token_based(5, tokens, tokens*0.25)
