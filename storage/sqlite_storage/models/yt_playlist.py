from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class YTPlaylist(Base):
    """SQLAlchemy model for YouTube playlists."""
    __tablename__ = 'youtube_playlists'

    id = Column(String, primary_key=True)  # YouTube playlist ID
    title = Column(String)
    channel_id = Column(String, ForeignKey('channels.id'))
    published_at = Column(DateTime)
    video_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Playlist(id='{self.id}', title='{self.title}')>"
