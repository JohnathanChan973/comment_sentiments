from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .analysis_mixin import AnalysisMixin
from typing import List, Dict
from .base import Base

class YTComment(Base, AnalysisMixin):
    """SQLAlchemy model for YouTube comments."""
    __tablename__ = 'youtube_comments'

    comment_id = Column(String, primary_key=True)
    video_id = Column(String, ForeignKey('youtube_videos.id'))
    text = Column(String)
    author = Column(String) 
    author_id = Column(String)
    likes = Column(Integer, default=0)
    published_at = Column(DateTime)
    updated_at = Column(DateTime)

    # Relationships
    video = relationship("YTVideo", back_populates="comments")
    sentiment = relationship("Sentiment", back_populates="comment", uselist=False)

    def needs_reanalysis(self) -> bool:
        """
        Check if the comment needs to be reanalyzed based on its update time.
        
        Returns:
            bool: True if comment was updated after its last analysis, False otherwise
        """
        if not self.last_analyzed_at:
            return True
        return self.updated_at and self.updated_at > self.last_analyzed_at

    @classmethod
    def filter_needs_reanalysis(cls, comments: List['YTComment']) -> Dict[str, List['YTComment']]:
        """
        Filter a list of comments into those needing and not needing reanalysis.
        
        This is useful for batch processing comments, especially when:
        1. Processing all comments from a video
        2. Processing comments from multiple videos
        3. Updating sentiment analysis in batches
        
        Args:
            comments: List of YTComment objects to check
            
        Returns:
            Dict with two keys:
                'needs_analysis': List of comments needing reanalysis
                'skip_analysis': List of comments that can be skipped
        """
        needs_analysis = []
        skip_analysis = []
        
        for comment in comments:
            if comment.needs_reanalysis():
                needs_analysis.append(comment)
            else:
                skip_analysis.append(comment)
                
        return {
            'needs_analysis': needs_analysis,
            'skip_analysis': skip_analysis
        }

    def __repr__(self):
        return f"<Comment(id='{self.comment_id}', author='{self.author}')>"