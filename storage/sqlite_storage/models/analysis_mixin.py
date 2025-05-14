from sqlalchemy import Column, DateTime
from datetime import datetime, timezone

class AnalysisMixin:
    """Mixin class to add last_analyzed_at tracking to models."""
    
    last_analyzed_at = Column(DateTime, nullable=True)

    def update_analyzed_at(self):
        """Update the last_analyzed_at timestamp to current time."""
        self.last_analyzed_at = datetime.now(timezone.utc) 