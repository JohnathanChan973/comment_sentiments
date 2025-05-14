import logging
from datetime import datetime
from googleapiclient.errors import HttpError
from typing import List, Optional
from .youtube_video import YouTubeVideo

class YouTubeChannel:
    """Class representing a YouTube channel with lazy-loading properties."""
    
    def __init__(self, channel_id: str, youtube_client):
        """
        Initialize a YouTube channel object.
        
        Args:
            channel_id: YouTube channel ID
            youtube_client: YouTube API client from googleapiclient.discovery
        """
        self.id = channel_id
        self._youtube = youtube_client
        
        # Properties to be lazy-loaded
        self._snippet = None
        self._statistics = None
        self._contentDetails = None
        self._uploads_playlist_id = None
        self._video_ids = None
    
    def _ensure_details_loaded(self) -> bool:
        """Fetch channel details if not already loaded."""
        if self._snippet is not None:
            return True
            
        try:
            request = self._youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=self.id
            )
            response = request.execute()
            
            items = response.get('items', [])
            if not items:
                logging.warning(f"No channel found with ID: {self.id}")
                return False
                
            channel_data = items[0]
            self._snippet = channel_data.get('snippet', {})
            self._statistics = channel_data.get('statistics', {})
            self._contentDetails = channel_data.get('contentDetails', {})
            
            # Extract uploads playlist ID
            related_playlists = self._contentDetails.get('relatedPlaylists', {})
            self._uploads_playlist_id = related_playlists.get('uploads')
            
            return True
            
        except HttpError as e:
            logging.error(f"Error fetching details for channel {self.id}: {e}")
            return False
    
    @property
    def name(self) -> Optional[str]:
        """Get the channel title."""
        if self._ensure_details_loaded():
            return self._snippet.get('title')
        return None
    
    @property
    def description(self) -> Optional[str]:
        """Get the channel description."""
        if self._ensure_details_loaded():
            return self._snippet.get('description')
        return None
    
    @property
    def custom_url(self) -> Optional[str]:
        """Get the channel's custom URL."""
        if self._ensure_details_loaded():
            return self._snippet.get('customUrl')
        return None
    
    @property   
    def country(self) -> Optional[str]:
        """Get the channel's country."""
        if self._ensure_details_loaded():
            return self._snippet.get('country')
        return None
    
    @property
    def subscriber_count(self) -> int:
        """Get the channel's subscriber count."""
        if self._ensure_details_loaded():
            count = self._statistics.get('subscriberCount')
            return int(count) if count is not None else 0
        return 0
    
    @property
    def video_count(self) -> int:
        """Get the channel's video count."""
        if self._ensure_details_loaded():
            count = self._statistics.get('videoCount')
            return int(count) if count is not None else 0
        return 0
    
    @property
    def view_count(self) -> int:
        """Get the channel's total view count."""
        if self._ensure_details_loaded():
            count = self._statistics.get('viewCount')
            return int(count) if count is not None else 0
        return 0
    
    @property   
    def published_at(self) -> Optional[datetime]:
        """Get the channel's published date."""
        if self._ensure_details_loaded():
            return self._snippet.get('publishedAt')
        return None
    
    @property
    def uploads_playlist_id(self) -> Optional[str]:
        """Get the channel's uploads playlist ID."""
        if self._ensure_details_loaded():
            return self._uploads_playlist_id
        return None
    
    def get_video_ids(self, max_results: Optional[int] = None) -> List[str]:
        """
        Get IDs of videos uploaded by this channel.
        
        Args:
            max_results: Maximum number of video IDs to retrieve
            
        Returns:
            List of video IDs
        """
        if self._video_ids is None:
            if not self._ensure_details_loaded() or not self._uploads_playlist_id:
                return []
                
            self._video_ids = self._get_video_ids_from_playlist(self._uploads_playlist_id)
            
        return self._video_ids[:max_results] if max_results else self._video_ids
    
    def get_videos(self, max_results: Optional[int] = None) -> List['YouTubeVideo']:
        """
        Get video objects for videos uploaded by this channel.
        
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
    
    def _get_video_ids_from_playlist(self, playlist_id: str) -> List[str]:
        """
        Get all video IDs from a playlist ID.
        
        Args:
            playlist_id: YouTube playlist ID
            
        Returns:
            List of video IDs
        """
        video_ids = []
        next_page_token = None
        
        while True:
            try:
                request = self._youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
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
                logging.error(f"Error fetching video IDs from playlist {playlist_id}: {e}")
                break
                
        return video_ids
    
    def __str__(self) -> str:
        return f"YouTubeChannel(id={self.id}, title={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()