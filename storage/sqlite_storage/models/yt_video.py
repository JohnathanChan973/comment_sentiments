from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .analysis_mixin import AnalysisMixin
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set
from .base import Base

class YTVideo(Base, AnalysisMixin):
    """SQLAlchemy model for YouTube videos."""
    __tablename__ = 'youtube_videos'

    id = Column(String, primary_key=True)  # YouTube video ID
    title = Column(String)
    description = Column(String)
    published_at = Column(DateTime)
    channel_id = Column(String)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0) 
    comment_count = Column(Integer, default=0)

    # Relationships
    comments = relationship("YTComment", back_populates="video", cascade="all, delete-orphan")

    def needs_reanalysis(self, max_age_days: int = 30, force_recent_days: int = 7) -> bool:
        """
        Check if video needs reanalysis based on its age and last analysis time.
        
        Strategy:
        1. Never analyzed videos always need analysis
        2. Recent videos (< force_recent_days old) are always reanalyzed to catch new comments
        3. Older videos are reanalyzed if not analyzed in the last max_age_days
        
        Args:
            max_age_days: Maximum days before requiring reanalysis for older videos
            force_recent_days: Days threshold for considering a video "recent"
            
        Returns:
            bool: True if video needs reanalysis, False otherwise
        """
        if not self.last_analyzed_at:
            return True
            
        now = datetime.now(timezone.utc)
        video_age = now - self.published_at
        time_since_analysis = now - self.last_analyzed_at
        
        # Always reanalyze recent videos to catch new comments
        if video_age.days <= force_recent_days:
            return True
            
        # Reanalyze older videos if they haven't been analyzed recently
        return time_since_analysis.days >= max_age_days

    @classmethod
    def filter_needs_reanalysis(cls, videos: List['YTVideo'], 
                              max_age_days: int = 30,
                              force_recent_days: int = 7) -> Dict[str, List['YTVideo']]:
        """
        Filter a list of videos into those needing and not needing reanalysis.
        
        Args:
            videos: List of YTVideo objects to check
            max_age_days: Maximum days before requiring reanalysis for older videos
            force_recent_days: Days threshold for considering a video "recent"
            
        Returns:
            Dict with two keys:
                'needs_analysis': List of videos needing reanalysis
                'skip_analysis': List of videos that can be skipped
        """
        needs_analysis = []
        skip_analysis = []
        
        for video in videos:
            if video.needs_reanalysis(max_age_days, force_recent_days):
                needs_analysis.append(video)
            else:
                skip_analysis.append(video)
                
        return {
            'needs_analysis': needs_analysis,
            'skip_analysis': skip_analysis
        }

    def __repr__(self):
        return f"<Video(id='{self.id}', title='{self.title}')>"
