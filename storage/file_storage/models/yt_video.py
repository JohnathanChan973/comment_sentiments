from typing import NamedTuple, Optional
from datetime import datetime

class FileVideo(NamedTuple):
    """File-based storage model for YouTube videos."""
    id: str
    title: str
    description: str
    published_at: datetime
    channel_id: str
    view_count: int
    like_count: int
    comment_count: int
    last_analyzed_at: Optional[datetime] = None 