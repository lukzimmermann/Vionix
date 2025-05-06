from app.models import Chunk, Video
from app.worker.chunk import ChunkCreator
from app.utils.database import Database
import time

session = Database().get_session()
videos = session.query(Video).all()
chunk_creator = ChunkCreator()

tokens = 1000
start_time = time.time()
chunks = chunk_creator.token_based(5, 400, 80)
end_time = time.time()

def print_chunk(chunk: Chunk):
    tokens = chunk_creator.tokenizer.encode(chunk.text, add_special_tokens=False)
    print(f"{len(tokens)} @ {chunk.start}-{chunk.end}")

for chunk in chunks:
    print_chunk(chunk)
    
print(f"Time consumption: {(end_time - start_time):.3f}")
print("Number of chunks: ", len(chunks))
