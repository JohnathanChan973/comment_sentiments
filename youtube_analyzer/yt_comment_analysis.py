"""
YouTube Comment Analysis System
-------------------------------
A comprehensive system for analyzing YouTube comments, integrating:
- Enhanced YouTube API Wrapper for data retrieval
- Sentiment analysis capabilities
- Concurrent processing with threading
- Flexible storage options (SQLite and file-based storage)

Built as a modular, extensible system with clean object-oriented design.
"""
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from youtube_wrapper.youtube_api import YouTubeAPI
from sentiment_analyzer import SentimentAnalyzer
from storage.storage_factory import StorageFactory
from .comment_analysis_task import CommentAnalysisTask
from logger_config import get_logger

logger = get_logger("youtube_analyzer")

class YouTubeCommentAnalyzer:
    """Main class for analyzing YouTube comments."""
    
    def __init__(self, api_key: Optional[str] = None, 
             storage_type: str = "sqlite",
             base_storage_path: str = "./data",
             db_name: str = "youtube_analysis",
             save: bool = True,
             max_workers: Optional[int] = None,
             use_api_cache: bool = False,
             max_cache_items: int = 100):
        """
        Initialize the YouTube comment analyzer.
        
        Args:
            api_key: YouTube Data API key (optional, will use environment variable if not provided)
            storage_type: Type of storage to use ('file' or 'sqlite')
            base_storage_path: Base path for storing data and database files
            db_name: Name for the database file (without extension) if using database storage
            save: Whether to save results
            max_workers: Maximum number of worker threads (defaults to CPU count)
            use_api_cache: Whether to cache YouTube API results
            max_cache_items: Maximum number of items to keep in each cache
        """
        self.api = YouTubeAPI(api_key, use_cache=use_api_cache, max_cache_items=max_cache_items)
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Configure storage parameters based on the storage type
        storage_kwargs = {
            "path": base_storage_path,
            "db_name": db_name
        }
        
        # Create the storage instance using the factory
        self.storage = StorageFactory.create_storage(storage_type, **storage_kwargs)
        
        self.save = save
        self.max_workers = max_workers or threading.active_count() * 2
        
    def analyze_video(self, url_or_id: str) -> Dict[str, Any]:
        """
        Analyze comments for a single video.
        
        Args:
            url_or_id: YouTube video URL or ID
            
        Returns:
            Dictionary with analysis results
        """
        # Create a new API instance for this thread
        thread_api = YouTubeAPI(
            api_key=self.api.api_key,
            use_cache=self.api.use_cache,
            max_cache_items=self.api.max_cache_items
        )
        
        task = CommentAnalysisTask(
            url_or_id, thread_api, self.sentiment_analyzer, 
            self.storage, self.save
        )
        return task.run()
        
    def analyze_multiple_videos(self, urls_or_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze comments for multiple videos using thread pool.
        
        Args:
            urls_or_ids: List of YouTube video URLs or IDs
            
        Returns:
            List of dictionaries with analysis results
        """
        if not urls_or_ids:
            logger.warning("No videos provided for analysis")
            return []
            
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.analyze_video, url): url 
                for url in urls_or_ids
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed analysis for {url}")
                except Exception as e:
                    logger.error(f"Analysis failed for {url}: {e}")
                    
        return results
        
    def analyze_channel(self, channel_url_or_id: str, 
                        max_videos: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Analyze comments for all videos in a channel.
        
        Args:
            channel_url_or_id: YouTube channel URL or ID
            max_videos: Maximum number of videos to analyze (None for all)
            
        Returns:
            List of dictionaries with analysis results
        """
        try:
            channel = self.api.get_channel(channel_url_or_id)
            logger.info(f"Analyzing channel: {channel.name} ({channel.id})")
            
            if self.save:
                # Save channel data
                channel_published_at = datetime.fromisoformat(channel.published_at.replace('Z', '+00:00'))
                channel_data = {
                    "id": channel.id,
                    "name": channel.name,
                    "custom_url": channel.custom_url,
                    "subscriber_count": channel.subscriber_count,
                    "video_count": channel.video_count,
                    "view_count": channel.view_count,
                    "published_at": channel_published_at,
                    "country": channel.country,
                    "uploads_playlist_id": channel.uploads_playlist_id
                }
                self.storage.save_channel(channel_data)
                
                # Save uploads playlist if it exists
                if channel.uploads_playlist_id:
                    playlist_data = {
                        "id": channel.uploads_playlist_id,
                        "title": f"{channel.name} - Uploads",
                        "channel_id": channel.id,
                        "published_at": channel_published_at,
                        "video_count": channel.video_count
                    }
                    self.storage.save_playlist(playlist_data)
            
            video_ids = channel.get_video_ids(max_videos)
            logger.info(f"Found {len(video_ids)} videos in channel")
            
            return self.analyze_multiple_videos(video_ids)
        except Exception as e:
            logger.error(f"Error analyzing channel {channel_url_or_id}: {e}")
            return []
            
    def analyze_playlist(self, playlist_url_or_id: str) -> List[Dict[str, Any]]:
        """
        Analyze comments for all videos in a playlist.
        
        Args:
            playlist_url_or_id: YouTube playlist URL or ID
            
        Returns:
            List of dictionaries with analysis results
        """
        try:
            playlist = self.api.get_playlist(playlist_url_or_id)
            logger.info(f"Analyzing playlist: {playlist.title} ({playlist.id})")
            
            if self.save:
                # Save channel data first
                channel_data = {
                    "id": playlist.channel_id,
                    "name": playlist.channel_title,
                    "custom_url": None,  # Not available in playlist response
                    "subscriber_count": None,  # Not available in playlist response
                    "video_count": None,  # Not available in playlist response
                    "view_count": None,  # Not available in playlist response
                    "published_at": None,  # Not available in playlist response
                    "country": None,  # Not available in playlist response
                    "uploads_playlist_id": None  # Not available in playlist response
                }
                self.storage.save_channel(channel_data)
                
                playlist_published_at = datetime.fromisoformat(playlist.published_at.replace('Z', '+00:00'))

                # Save playlist data
                playlist_data = {
                    "id": playlist.id,
                    "title": playlist.title,
                    "channel_id": playlist.channel_id,
                    "published_at": playlist_published_at,
                    "video_count": playlist.item_count
                }
                self.storage.save_playlist(playlist_data)
            
            video_ids = playlist.get_video_ids()
            logger.info(f"Found {len(video_ids)} videos in playlist")
            
            return self.analyze_multiple_videos(video_ids)
        except Exception as e:
            logger.error(f"Error analyzing playlist {playlist_url_or_id}: {e}")
            return []
