"""
Enhanced YouTube API Wrapper
----------------------------
A comprehensive wrapper for the YouTube Data API that provides organized access to:
- Video data and comments
- Channel information and uploads
- Playlist contents
- URL parsing utilities

All with efficient API usage, caching, and a clean object-oriented design.
"""
from googleapiclient.discovery import build
import os
import re
from urllib.parse import urlparse, parse_qs
from typing import Optional
from .youtube_video import YouTubeVideo
from .youtube_channel import YouTubeChannel
from .youtube_playlist import YouTubePlaylist
from logger_config import get_logger

logger = get_logger("youtube_api")
        
class YouTubeAPI:
    """Main YouTube API wrapper class that serves as the entry point for all operations."""
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True, max_cache_items: int = 100):
        """
        Initialize the YouTube API client.
        
        Args:
            api_key: YouTube Data API key. If None, will try to get from environment variable.
            use_cache: Whether to cache API results
            max_cache_items: Maximum number of items to keep in each cache
        """
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set as API_KEY environment variable")
            
        self.youtube = build('youtube', 'v3', developerKey=self.api_key, cache_discovery=False)
        
        # Cache configuration
        self.use_cache = use_cache
        self.max_cache_items = max_cache_items
        
        # Initialize caches if enabled
        self._video_cache = {} if use_cache else None
        self._channel_cache = {} if use_cache else None
        self._playlist_cache = {} if use_cache else None
        
    # =====================
    # Video-related methods
    # =====================
    
    def get_video(self, url_or_id: str) -> 'YouTubeVideo':
        """
        Get a YouTubeVideo object for the specified URL or ID.
        
        Args:
            url_or_id: YouTube video URL or ID
            
        Returns:
            YouTubeVideo object
        """
        video_id = self.extract_video_id(url_or_id)
        if not video_id:
            raise ValueError(f"Could not extract valid video ID from: {url_or_id}")
            
        # Return from cache if available
        if self.use_cache and self._video_cache is not None and video_id in self._video_cache:
            return self._video_cache[video_id]
        
        # Create new video object
        video = YouTubeVideo(video_id, self.youtube)
        
        # Store in cache if enabled
        if self.use_cache and self._video_cache is not None:
            self._add_to_cache(self._video_cache, video_id, video)
        return video
    
    def extract_video_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract video ID from a YouTube URL or return the ID if already provided.
        
        Args:
            url_or_id: YouTube video URL or ID
            
        Returns:
            Video ID or None if not found
        """
        # Check if it's already just an ID (simple string without URL components)
        if '/' not in url_or_id and '?' not in url_or_id and len(url_or_id) < 30:
            return url_or_id.strip()
            
        parsed_url = urlparse(url_or_id)
        hostname = parsed_url.hostname
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if not hostname:  # Not a URL
            return url_or_id.strip()
        
        video_id = None
        
        if hostname in ('www.youtube.com', 'youtube.com'):
            if path.startswith('/shorts/'):
                video_id = path.split('/shorts/')[1]
            elif path.startswith('/watch'):
                video_id = query_params.get('v', [None])[0]
        elif hostname == 'youtu.be':
            video_id = path.lstrip('/')
        
        if video_id:
            # Handle additional parameters after the ID
            if '&' in video_id:
                video_id = video_id.split('&')[0]
            return video_id.strip()
            
        return None
    
    # ======================
    # Channel-related methods
    # ======================
    
    def get_channel(self, url_or_id: str) -> 'YouTubeChannel':
        """
        Get a YouTubeChannel object for the specified URL, ID, or handle.
        
        Args:
            url_or_id: YouTube channel URL, ID, handle, or username
            
        Returns:
            YouTubeChannel object
        """
        channel_id = self.extract_channel_id(url_or_id)
        if not channel_id:
            raise ValueError(f"Could not extract valid channel ID from: {url_or_id}")
            
        # Return from cache if available
        if self.use_cache and self._channel_cache is not None and channel_id in self._channel_cache:
            return self._channel_cache[channel_id]
        
        # Create new channel object
        channel = YouTubeChannel(channel_id, self.youtube)
        
        # Store in cache if enabled
        if self.use_cache and self._channel_cache is not None:
            self._add_to_cache(self._channel_cache, channel_id, channel)

        return channel
    
    def extract_channel_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract channel ID from various formats (URL, handle, custom URL, username).
        
        Args:
            url_or_id: YouTube channel URL, ID, handle, or username
            
        Returns:
            Channel ID or None if not found
        """
        # Check if it's already a channel ID
        if url_or_id.startswith('UC') and len(url_or_id) == 24 and '/' not in url_or_id:
            return url_or_id
        
        # Try to parse as URL
        parsed_url = urlparse(url_or_id)
        
        # Not a URL - could be a handle without the @ symbol
        if not parsed_url.netloc:
            if url_or_id.startswith('@'):
                return self._get_channel_id_from_handle(url_or_id)
            return self._get_channel_id_from_handle(f"@{url_or_id}")
            
        # It's a URL
        path = parsed_url.path
        
        # Direct channel URL
        match = re.match(r'^/channel/([A-Za-z0-9_-]+)', path)
        if match:
            return match.group(1)
        
        # Handle URL
        if path.startswith('/@'):
            handle = path.lstrip('/@')
            return self._get_channel_id_from_handle(f"@{handle}")
        
        # Custom URL path
        if '/c/' in path:
            custom_url = path.split('/c/')[1]
            return self._get_channel_id_from_custom_url(custom_url)
            
        # Username path
        if '/user/' in path:
            username = path.split('/user/')[1]
            return self._get_channel_id_from_username(username)
            
        return None
    
    def _get_channel_id_from_handle(self, handle: str) -> Optional[str]:
        """Get channel ID from a handle (e.g., @ChannelName)."""
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=handle,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            items = response.get('items', [])
            if items:
                return items[0]['id']['channelId']
        except Exception as e:
            logger.error(f"Error fetching channel ID for handle {handle}: {e}")
        return None
    
    def _get_channel_id_from_custom_url(self, custom_url: str) -> Optional[str]:
        """Get channel ID from a custom URL."""
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=custom_url,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            items = response.get('items', [])
            if items:
                return items[0]['id']['channelId']
        except Exception as e:
            logger.error(f"Error fetching channel ID for custom URL {custom_url}: {e}")
        return None
    
    def _get_channel_id_from_username(self, username: str) -> Optional[str]:
        """Get channel ID from a username."""
        try:
            request = self.youtube.channels().list(
                part='id',
                forUsername=username
            )
            response = request.execute()
            items = response.get('items', [])
            if items:
                return items[0]['id']
        except Exception as e:
            logger.error(f"Error fetching channel ID for username {username}: {e}")
        return None
    
    # =======================
    # Playlist-related methods
    # =======================
    
    def get_playlist(self, url_or_id: str) -> 'YouTubePlaylist':
        """
        Get a YouTubePlaylist object for the specified URL or ID.
        
        Args:
            url_or_id: YouTube playlist URL or ID
            
        Returns:
            YouTubePlaylist object
        """
        playlist_id = self.extract_playlist_id(url_or_id)
        if not playlist_id:
            raise ValueError(f"Could not extract valid playlist ID from: {url_or_id}")
            
        # Return from cache if available
        if self.use_cache and self._playlist_cache is not None and playlist_id in self._playlist_cache:
            return self._playlist_cache[playlist_id]
        
        # Create new playlist object
        playlist = YouTubePlaylist(playlist_id, self.youtube)
        
        # Store in cache if enabled
        if self.use_cache and self._playlist_cache is not None:
            self._add_to_cache(self._playlist_cache, playlist_id, playlist)

        return playlist
    
    def extract_playlist_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract playlist ID from a YouTube URL or return the ID if already provided.
        
        Args:
            url_or_id: YouTube playlist URL or ID
            
        Returns:
            Playlist ID or None if not found
        """
        # Check if it's already just an ID
        if url_or_id.startswith('PL') and '/' not in url_or_id:
            return url_or_id
            
        parsed_url = urlparse(url_or_id)
        
        # Not a URL
        if not parsed_url.netloc:
            if url_or_id.startswith('PL'):
                return url_or_id
            return None
            
        # Extract from URL
        query_params = parse_qs(parsed_url.query)
        playlist_id = query_params.get('list', [None])[0]
        
        return playlist_id

    # =======================
    # Cache-related methods
    # =======================

    def _add_to_cache(self, cache_dict, key, value):
        """Add an item to a cache dictionary, respecting max size limit."""
        if not self.use_cache or cache_dict is None:
            return
            
        # If cache is full, remove oldest item
        if len(cache_dict) >= self.max_cache_items:
            # Remove oldest item (first inserted in Python 3.7+)
            oldest_key = next(iter(cache_dict))
            del cache_dict[oldest_key]
            
        # Add new item
        cache_dict[key] = value
    
    def clear_caches(self):
        """Clear all cached data."""
        if self.use_cache:
            self._video_cache = {}
            self._channel_cache = {}
            self._playlist_cache = {}

    def get_cache_stats(self):
        """Get statistics about the caches."""
        if not self.use_cache:
            return {"caching_enabled": False}
            
        return {
            "caching_enabled": True,
            "max_items_per_cache": self.max_cache_items,
            "video_cache_size": len(self._video_cache) if self._video_cache else 0,
            "channel_cache_size": len(self._channel_cache) if self._channel_cache else 0,
            "playlist_cache_size": len(self._playlist_cache) if self._playlist_cache else 0
        }
