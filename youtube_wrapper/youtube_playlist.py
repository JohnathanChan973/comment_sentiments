import logging
from googleapiclient.errors import HttpError
from typing import List, Optional
from .youtube_video import YouTubeVideo

class YouTubePlaylist:
    """Class representing a YouTube playlist with lazy-loading properties."""
    
    def __init__(self, playlist_id: str, youtube_client):
        """
        Initialize a YouTube playlist object.
        
        Args:
            playlist_id: YouTube playlist ID
            youtube_client: YouTube API client from googleapiclient.discovery
        """
        self.id = playlist_id
        self._youtube = youtube_client
        
        # Properties to be lazy-loaded
        self._snippet = None
        self._contentDetails = None
        self._video_ids = None
    
    def _ensure_details_loaded(self) -> bool:
        """Fetch playlist details if not already loaded."""
        if self._snippet is not None:
            return True
            
        try:
            request = self._youtube.playlists().list(
                part='snippet,contentDetails',
                id=self.id
            )
            response = request.execute()
            
            items = response.get('items', [])
            if not items:
                logging.warning(f"No playlist found with ID: {self.id}")
                return False
                
            playlist_data = items[0]
            self._snippet = playlist_data.get('snippet', {})
            self._contentDetails = playlist_data.get('contentDetails', {})
            return True
            
        except HttpError as e:
            logging.error(f"Error fetching details for playlist {self.id}: {e}")
            return False
    
    @property
    def title(self) -> Optional[str]:
        """Get the playlist title."""
        if self._ensure_details_loaded():
            return self._snippet.get('title')
        return None
    
    @property
    def description(self) -> Optional[str]:
        """Get the playlist description."""
        if self._ensure_details_loaded():
            return self._snippet.get('description')
        return None
    
    @property
    def published_at(self) -> Optional[str]:
        """Get when the playlist was published."""
        if self._ensure_details_loaded():
            return self._snippet.get('publishedAt')
        return None
    
    @property
    def channel_id(self) -> Optional[str]:
        """Get the channel ID of the playlist."""
        if self._ensure_details_loaded():
            return self._snippet.get('channelId')
        return None
    
    @property
    def channel_title(self) -> Optional[str]:
        """Get the channel title of the playlist."""
        if self._ensure_details_loaded():
            return self._snippet.get('channelTitle')
        return None
    
    @property
    def item_count(self) -> int:
        """Get the number of items in the playlist."""
        if self._ensure_details_loaded():
            count = self._contentDetails.get('itemCount')
            return int(count) if count is not None else 0
        return 0
    
    def get_video_ids(self, max_results: Optional[int] = None) -> List[str]:
        """
        Get IDs of videos in this playlist.
        
        Args:
            max_results: Maximum number of video IDs to retrieve
            
        Returns:
            List of video IDs
        """
        if self._video_ids is None:
            self._video_ids = self._get_video_ids_from_playlist()
            
        return self._video_ids[:max_results] if max_results else self._video_ids
    
    def get_videos(self, max_results: Optional[int] = None) -> List['YouTubeVideo']:
        """
        Get video objects for videos in this playlist.
        
        Args:
            max_results: Maximum number of videos to retrieve
            
        Returns:
            List of YouTubeVideo objects
        """
        video_ids = self.get_video_ids(max_results)
        videos = []
        
        for video_id in video_ids:
            video = YouTubeVideo(video_id, self._youtube)
            videos.append(video)
            
        return videos
    
    def _get_video_ids_from_playlist(self) -> List[str]:
        """
        Get all video IDs from this playlist.
        
        Returns:
            List of video IDs
        """
        video_ids = []
        next_page_token = None
        
        while True:
            try:
                request = self._youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=self.id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                # Extract video IDs
                items = response.get('items', [])
                for item in items:
                    video_id = item['contentDetails'].get('videoId')
                    if video_id:
                        video_ids.append(video_id)
                
                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                logging.error(f"Error fetching video IDs from playlist {self.id}: {e}")
                break
                
        return video_ids
    
    def __str__(self) -> str:
        return f"YouTubePlaylist(id={self.id}, title={self.title})"
    
    def __repr__(self) -> str:
        return self.__str__()