from typing import Dict, Any
from datetime import datetime
from youtube_wrapper.youtube_api import YouTubeAPI
from sentiment_analyzer import SentimentAnalyzer
from storage.base_storage import BaseStorage
from logger_config import get_logger

logger = get_logger("youtube_analyzer")

class CommentAnalysisTask:
    """Class representing a single comment analysis task."""
    
    def __init__(self, url_or_id: str, api: YouTubeAPI, 
                 sentiment_analyzer: SentimentAnalyzer,
                 storage: BaseStorage, 
                 save: bool = True):
        """
        Initialize a comment analysis task.
        
        Args:
            url_or_id: YouTube video URL or ID
            api: YouTube API wrapper instance
            sentiment_analyzer: Sentiment analyzer instance
            storage: Data storage instance
            save: Whether to save results
        """
        self.url_or_id = url_or_id
        self.api = api
        self.sentiment_analyzer = sentiment_analyzer
        self.storage = storage
        self.save = save
        
        # Fields to be populated during execution
        self.video = None
        self.video_id = None
        self.video_title = None
        self.comments = []
        self.sentiment_results = []
        
    def run(self) -> Dict[str, Any]:
        """
        Run the complete analysis task.
        
        Returns:
            Dictionary with analysis results
        """
        self._fetch_video_data()
        self._fetch_comments()
        self._analyze_sentiment()
        return self._prepare_results()
        
    def _fetch_video_data(self):
        """Fetch video metadata."""
        try:
            self.video = self.api.get_video(self.url_or_id)
            self.video_id = self.video.id
            self.video_title = self.video.title
            
            if self.save:
                # Parse the ISO 8601 datetime string from the API
                published_at = datetime.fromisoformat(self.video.publish_date.replace('Z', '+00:00'))
                
                # Save channel data first
                channel_data = {
                    "id": self.video.channel_id,
                    "name": self.video.channel_title,
                    "custom_url": None,  # Not available in video response
                    "subscriber_count": None,  # Not available in video response
                    "video_count": None,  # Not available in video response
                    "view_count": None,  # Not available in video response
                    "published_at": None,  # Not available in video response
                    "country": None,  # Not available in video response
                    "uploads_playlist_id": None  # Not available in video response
                }
                self.storage.save_channel(channel_data)
                
                # Save video data
                video_data = {
                    "id": self.video_id,
                    "title": self.video_title,
                    "description": self.video.description,
                    "published_at": published_at,
                    "channel_id": self.video.channel_id,
                    "view_count": self.video.view_count,
                    "like_count": self.video.like_count,
                    "comment_count": self.video.comment_count
                }
                self.storage.save_video(video_data)
                
            logger.info(f"Fetched video data: {self.video_title} ({self.video_id})")
        except Exception as e:
            logger.error(f"Error fetching video data: {e}")
            raise
            # print(f"Error type: {type(e)}")
            # print(f"Error args: {e.args}")
            # import traceback
            # traceback.print_exc()
            # raise
            
    def _fetch_comments(self):
        """Fetch video comments."""
        try:
            # Get comments from API
            api_comments = self.video.get_comments()
            self.comments = []
            
            # Transform comments into storage format
            for comment in api_comments:
                # Parse the ISO 8601 datetime string from the API
                published_at = datetime.fromisoformat(comment.get("published_at", "").replace('Z', '+00:00'))
                updated_at = datetime.fromisoformat(comment.get("updated_at", "").replace('Z', '+00:00'))
                
                comment_data = {
                    "comment_id": comment.get("comment_id"),
                    "text": comment.get("text", ""),
                    "author": comment.get("author", ""),
                    "author_id": comment.get("author_id", ""),
                    "likes": comment.get("likes", 0),
                    "published_at": published_at,
                    "updated_at": updated_at
                }
                self.comments.append(comment_data)
            
            # Save comments if requested
            if self.save and self.comments:
                self.storage.save_comments(self.comments, self.video_id)
                
            logger.info(f"Processed {len(self.comments)} comments for video {self.video_id}")
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            self.comments = []
            
    def _analyze_sentiment(self):
        """Analyze sentiment of comments."""
        if not self.comments:
            logger.warning(f"No comments to analyze for video {self.video_id}")
            return
            
        try:
            # Extract comment text
            comment_texts = [comment["text"] for comment in self.comments]
            
            # Process sentiment analysis
            analysis_results = self.sentiment_analyzer.analyze_batch(comment_texts)
            
            # Transform results into storage format
            self.sentiment_results = []
            for i, result in enumerate(analysis_results):
                sentiment_data = {
                    "comment_id": self.comments[i]["comment_id"],
                    "label": result["sentiment"],
                    "score": result["score"]
                }
                self.sentiment_results.append(sentiment_data)
            
            # Save sentiment results if requested
            if self.save:
                self.storage.save_sentiment_results(self.sentiment_results)
                
            logger.info(f"Analyzed sentiment for {len(self.sentiment_results)} comments")
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            self.sentiment_results = []
            
    def _prepare_results(self) -> Dict[str, Any]:
        """
        Prepare the final results of the analysis.
        
        Returns:
            Dictionary with analysis results
        """
        # Prepare summary statistics
        comment_count = len(self.comments)
        
        sentiment_counts = {}
        if self.sentiment_results:
            for result in self.sentiment_results:
                sentiment = result["label"]
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        return {
            "video_id": self.video_id,
            "video_title": self.video_title,
            "comment_count": comment_count,
            "sentiment_summary": sentiment_counts,
            "comments": self.comments,
            "sentiment_results": self.sentiment_results
        }