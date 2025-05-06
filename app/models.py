from sqlalchemy import (
    Column, Float, Integer, String, DateTime, Enum, ForeignKey, Text, BigInteger, JSON
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import enum

Base = declarative_base()

class SourceType(enum.Enum):
    YOUTUBE_CHANNEL = "youtube_channel"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    MANUAL_UPLOAD = "manual_upload"

# --- Base Source (abstract) ---
class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(SourceType, name="source_type"), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'source',
        'polymorphic_on': type
    }

    videos = relationship("Video", back_populates="source")

# --- YouTube Channel Source ---
class YouTubeChannelSource(Source):
    __tablename__ = 'youtube_channel_sources'
    id = Column(Integer, ForeignKey('sources.id'), primary_key=True)
    channel_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    thumbnail_path = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': SourceType.YOUTUBE_CHANNEL
    }

# --- YouTube Playlist Source ---
class YouTubePlaylistSource(Source):
    __tablename__ = 'youtube_playlist_sources'
    id = Column(Integer, ForeignKey('sources.id'), primary_key=True)
    playlist_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    thumbnail_path  = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': SourceType.YOUTUBE_PLAYLIST
    }

# --- Manual Upload Source ---
class ManualUploadSource(Source):
    __tablename__ = 'manual_upload_sources'
    id = Column(Integer, ForeignKey('sources.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': SourceType.MANUAL_UPLOAD
    }

# --- Video Table ---
class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    external_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    length = Column(Integer, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    thumbnail_path  = Column(String, nullable=True)
    video_path = Column(String, nullable=False)
    audio_path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    transcription = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True), nullable=False)

    source = relationship("Source", back_populates="videos")
    stats = relationship("VideoStat", back_populates="video", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="video", cascade="all, delete-orphan")

# --- VideoStats Table ---
class VideoStat(Base):
    __tablename__ = 'video_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    views = Column(BigInteger, nullable=True)

    video = relationship("Video", back_populates="stats")

# --- Chunks Table ---
class Chunk(Base):
    __tablename__ = 'chunks'

    video_id = Column(Integer, ForeignKey('videos.id'), primary_key=True, nullable=False)
    start = Column(Float, primary_key=True, nullable=False)
    end = Column(Float, nullable=False)
    text = Column(String, nullable=False)
    embedding = Column(Vector(768), nullable=False)

    video = relationship("Video", back_populates="chunks")