from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .analysis_mixin import AnalysisMixin
from .base import Base

class Sentiment(Base, AnalysisMixin):
    """SQLAlchemy model for sentiment analysis results."""
    __tablename__ = 'sentiments'

    comment_id = Column(String, ForeignKey('youtube_comments.comment_id'), primary_key=True)
    label = Column(String, nullable=False)  # e.g., 'positive', 'negative', 'neutral'
    score = Column(Float, nullable=False)   # sentiment score/confidence

    # Relationship to the comment
    comment = relationship("YTComment", back_populates="sentiment")

    def needs_reanalysis(self) -> bool:
        """
        Check if the sentiment needs to be reanalyzed based on its comment's update time.
        
        Returns:
            bool: True if associated comment was updated after sentiment's last analysis
        """
        return self.comment.needs_reanalysis()

    def __repr__(self):
        return f"<Sentiment(comment_id='{self.comment_id}', label='{self.label}', score={self.score})>"
