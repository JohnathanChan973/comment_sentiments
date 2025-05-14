import logging
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional

class YouTubeVideo:
    """Class representing a YouTube video with lazy-loading properties."""
    
    def __init__(self, video_id: str, youtube_client):
        """
        Initialize a YouTube video object.
        
        Args:
            video_id: YouTube video ID
            youtube_client: YouTube API client from googleapiclient.discovery
        """
        self.id = video_id
        self._youtube = youtube_client
        
        # Properties to be lazy-loaded
        self._snippet = None
        self._statistics = None
        self._comments = None
    
    def _ensure_details_loaded(self) -> bool:
        """Fetch video details if not already loaded."""
        if self._snippet is not None:
            return True
            
        try:
            request = self._youtube.videos().list(
                part='snippet,statistics',
                id=self.id
            )
            response = request.execute()
            
            items = response.get('items', [])
            if not items:
                logging.warning(f"No video found with ID: {self.id}")
                return False
                
            self._snippet = items[0]['snippet']
            self._statistics = items[0]['statistics']
            return True
            
        except HttpError as e:
            logging.error(f"Error fetching details for video {self.id}: {e}")
            return False
    
    @property
    def title(self) -> Optional[str]:
        """Get the video title."""
        if self._ensure_details_loaded():
            return self._snippet.get('title')
        return None
    
    @property
    def description(self) -> Optional[str]:
        """Get the video description."""
        if self._ensure_details_loaded():
            return self._snippet.get('description')
        return None
    
    @property
    def publish_date(self) -> Optional[str]:
        """Get the video publish date."""
        if self._ensure_details_loaded():
            return self._snippet.get('publishedAt')
        return None
    
    @property
    def channel_id(self) -> Optional[str]:
        """Get the channel ID of the video."""
        if self._ensure_details_loaded():
            return self._snippet.get('channelId')
        return None
    
    @property
    def channel_title(self) -> Optional[str]:
        """Get the channel title of the video."""
        if self._ensure_details_loaded():
            return self._snippet.get('channelTitle')
        return None
    
    @property
    def view_count(self) -> int:
        """Get the view count of the video."""
        if self._ensure_details_loaded():
            return int(self._statistics.get('viewCount', 0))
        return 0
    
    @property
    def like_count(self) -> int:
        """Get the like count of the video."""
        if self._ensure_details_loaded():
            return int(self._statistics.get('likeCount', 0))
        return 0
    
    @property
    def comment_count(self) -> int:
        """Get the comment count of the video."""
        if self._ensure_details_loaded():
            return int(self._statistics.get('commentCount', 0))
        return 0
    
    def get_comments(self, max_comments: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get comments for this video with optional limit.
        
        Args:
            max_comments: Maximum number of comments to retrieve
            
        Returns:
            List of comment dictionaries
        """
        if self._comments is None:
            self._comments = self._fetch_comments_in_batches(max_comments=max_comments)
        
        return self._comments[:max_comments] if max_comments else self._comments
    
    def _fetch_comments_in_batches(self, batch_size: int = 100, max_comments: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch comments in batches with optional limit.
        
        Args:
            batch_size: Number of comments to fetch per API request
            max_comments: Maximum total comments to fetch
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        next_page_token = None
        
        while True:
            try:
                request = self._youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=self.id,
                    textFormat='plainText',
                    pageToken=next_page_token,
                    maxResults=batch_size
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    # Process top-level comment
                    comment_snippet = item['snippet']['topLevelComment']['snippet']
                    comment = {
                        'text': comment_snippet['textDisplay'],
                        'author': comment_snippet['authorDisplayName'],
                        'author_id': comment_snippet['authorChannelId']['value'],
                        'likes': comment_snippet['likeCount'],
                        'published_at': comment_snippet['publishedAt'],
                        'updated_at': comment_snippet['updatedAt'], # This matters in case a comment was edited
                        'comment_id': item['id']  # Using consistent field name
                    }
                    comments.append(comment)
                    
                    # Process replies
                    replies = item.get('replies', {}).get('comments', [])
                    for reply in replies:
                        reply_snippet = reply['snippet']
                        reply_comment = {
                            'text': reply_snippet['textDisplay'],
                            'author': reply_snippet['authorDisplayName'],
                            'author_id': reply_snippet['authorChannelId']['value'],
                            'likes': reply_snippet['likeCount'],
                            'published_at': reply_snippet['publishedAt'],
                            'updated_at': reply_snippet['updatedAt'],
                            'comment_id': reply['id']  # Using consistent field name
                        }
                        comments.append(reply_comment)
                
                # Check if we've reached the requested limit
                if max_comments and len(comments) >= max_comments:
                    return comments[:max_comments]
                
                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                error_message = e._get_reason() if hasattr(e, '_get_reason') else str(e)
                if 'commentsDisabled' in error_message:
                    logging.warning(f"Comments are disabled for video ID: {self.id}")
                else:
                    logging.error(f"Error fetching comments for {self.id}: {error_message}")
                break
                
        return comments
    
    def __str__(self) -> str:
        return f"YouTubeVideo(id={self.id}, title={self.title})"
    
    def __repr__(self) -> str:
        return self.__str__()