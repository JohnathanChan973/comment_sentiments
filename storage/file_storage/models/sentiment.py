from typing import NamedTuple, Optional
from datetime import datetime

class FileSentiment(NamedTuple):
    """File-based storage model for sentiment analysis results."""
    comment_id: str
    label: str
    score: float
    last_analyzed_at: Optional[datetime] = None 