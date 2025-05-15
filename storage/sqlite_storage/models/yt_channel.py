from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class YTChannel(Base):
    """SQLAlchemy model for YouTube channels."""
    __tablename__ = 'youtube_channels'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    custom_url = Column(String)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    view_count = Column(Integer)
    published_at = Column(DateTime)
    country = Column(String)
    uploads_playlist_id = Column(String)

    # Relationships
    videos = relationship("YTVideo", back_populates="channel")
    playlists = relationship("YTPlaylist", back_populates="channel")

    def __repr__(self):
        return f"<Channel(id='{self.id}', name='{self.name}')>"
