from typing import NamedTuple, Optional
from datetime import datetime

class FileComment(NamedTuple):
    """File-based storage model for YouTube comments."""
    comment_id: str
    video_id: str
    text: str
    author: str
    author_id: str
    likes: int
    published_at: datetime
    updated_at: Optional[datetime] = None
    last_analyzed_at: Optional[datetime] = None 