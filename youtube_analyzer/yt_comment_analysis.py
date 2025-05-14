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
             db_name: str = "youtube_comments",
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
            
            video_ids = playlist.get_video_ids()
            logger.info(f"Found {len(video_ids)} videos in playlist")
            
            return self.analyze_multiple_videos(video_ids)
        except Exception as e:
            logger.error(f"Error analyzing playlist {playlist_url_or_id}: {e}")
            return []

def main():
    # """Example usage of the YouTube Comment Analyzer."""
    # import os
    
    # # Get API key from environment variable
    # api_key = os.getenv("YOUTUBE_API_KEY")
    
    # # Initialize the analyzer
    analyzer = YouTubeCommentAnalyzer()
    
    # # Example 1: Analyze a single video
    # video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # print(f"\nAnalyzing video: {video_url}")
    # video_result = analyzer.analyze_video(video_url)
    # print(f"Video title: {video_result['video_title']}")
    # print(f"Comment count: {video_result['comment_count']}")
    # print(f"Sentiment summary: {video_result['sentiment_summary']}")
    
    # Example 2: Analyze a channel (limit to 5 videos)
    channel_url = "https://www.youtube.com/@SapphireDragon9189"
    print(f"\nAnalyzing channel: {channel_url}")
    channel_results = analyzer.analyze_channel(channel_url)
    print(f"Analyzed {len(channel_results)} videos from channel")
    
    # # Example 3: Analyze a playlist
    # playlist_url = "https://www.youtube.com/playlist?list=PLHFlHpPjgk713fMv5O4s4Fv7k6yTkXwkV"
    # print(f"\nAnalyzing playlist: {playlist_url}")
    # playlist_results = analyzer.analyze_playlist(playlist_url)
    # print(f"Analyzed {len(playlist_results)} videos from playlist")
    pass

if __name__ == "__main__":
    # import concurrent.futures
    main()