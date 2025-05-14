from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from ..base_storage import BaseStorage
from ..file_util import FileUtils
from .models.yt_video import YTVideo
from .models.yt_comment import YTComment
from .models.sentiment import Sentiment
from .models import Base
from logger_config import get_logger

logger = get_logger("storage")

class SQLiteStorage(BaseStorage[YTVideo, YTComment, Sentiment]):
    """SQLAlchemy-based implementation of storage interface using SQLite."""
    
    def __init__(self, path: str = "./data", db_name: str = "youtube_analysis"):
        """
        Initialize SQLAlchemy engine and session for SQLite storage.
        
        Args:
            path: Directory path for the database file
            db_name: Name of the database file (without extension)
        """
        # Ensure directory exists
        db_dir = Path(path)
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database URL
        db_file = db_dir / f"{FileUtils.sanitize_filename(db_name)}.db"
        db_url = f"sqlite:///{db_file}"
        
        # Initialize SQLAlchemy
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Initialized SQLite database at: {db_file}")
        
    def save_video(self, video_data: Dict[str, Any]) -> YTVideo:
        """
        Save or update a video record.
        
        Args:
            video_data: Dictionary containing video information
            
        Returns:
            YTVideo: The saved video object
        """
        with self.Session() as session:
            try:
                video = session.get(YTVideo, video_data['id'])
                if not video:
                    video = YTVideo(id=video_data['id'])
                
                # Update video attributes
                video.title = video_data.get('title', '')
                video.description = video_data.get('description', '')
                video.published_at = video_data.get('published_at')
                video.channel_id = video_data.get('channel_id', '')
                video.view_count = video_data.get('view_count', 0)
                video.like_count = video_data.get('like_count', 0)
                video.comment_count = video_data.get('comment_count', 0)
                video.update_analyzed_at()
                
                session.add(video)
                session.commit()
                logger.info(f"Saved video: {video.id} - {video.title}")
                return video
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error saving video {video_data.get('id')}: {e}")
                raise
    
    def save_comments(self, comments: List[Dict[str, Any]], video_id: str) -> List[YTComment]:
        """
        Save or update multiple comments for a video.
        
        Args:
            comments: List of comment dictionaries
            video_id: ID of the video these comments belong to
            
        Returns:
            List[YTComment]: List of saved comment objects
        """
        with self.Session() as session:
            try:
                saved_comments = []
                for comment_data in comments:
                    comment = session.get(YTComment, comment_data['comment_id'])
                    if not comment:
                        comment = YTComment(comment_id=comment_data['comment_id'])
                    
                    # Update comment attributes
                    comment.video_id = video_id
                    comment.text = comment_data.get('text', '')
                    comment.author = comment_data.get('author', '')
                    comment.author_id = comment_data.get('author_id', '')
                    comment.likes = comment_data.get('likes', 0)
                    comment.published_at = comment_data.get('published_at')
                    comment.updated_at = comment_data.get('updated_at')
                    comment.update_analyzed_at()
                    
                    session.add(comment)
                    saved_comments.append(comment)
                
                session.commit()
                logger.info(f"Saved {len(saved_comments)} comments for video {video_id}")
                return saved_comments
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error saving comments for video {video_id}: {e}")
                raise
    
    def save_sentiment_results(self, results: List[Dict[str, Any]]) -> List[Sentiment]:
        """
        Save or update sentiment analysis results.
        
        Args:
            results: List of sentiment analysis result dictionaries
            
        Returns:
            List[Sentiment]: List of saved sentiment objects
        """
        with self.Session() as session:
            try:
                saved_sentiments = []
                for result in results:
                    sentiment = session.get(Sentiment, result['comment_id'])
                    if not sentiment:
                        sentiment = Sentiment(comment_id=result['comment_id'])
                    
                    # Update sentiment attributes
                    sentiment.label = result['label']
                    sentiment.score = result['score']
                    sentiment.update_analyzed_at()
                    
                    session.add(sentiment)
                    saved_sentiments.append(sentiment)
                
                session.commit()
                logger.info(f"Saved {len(saved_sentiments)} sentiment results")
                return saved_sentiments
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error saving sentiment results: {e}")
                raise
    
    def get_video(self, video_id: str) -> Optional[YTVideo]:
        """
        Retrieve a video by its ID.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Optional[YTVideo]: Video object if found, None otherwise
        """
        with self.Session() as session:
            return session.get(YTVideo, video_id)
    
    def get_video_comments(self, video_id: str) -> List[YTComment]:
        """
        Retrieve all comments for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List[YTComment]: List of comment objects
        """
        with self.Session() as session:
            return session.query(YTComment).filter(YTComment.video_id == video_id).all()
    
    def get_comment_sentiment(self, comment_id: str) -> Optional[Sentiment]:
        """
        Retrieve sentiment analysis for a comment.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            Optional[Sentiment]: Sentiment object if found, None otherwise
        """
        with self.Session() as session:
            return session.get(Sentiment, comment_id)
    
    def get_videos_needing_analysis(self, max_age_days: int = 30, 
                                  force_recent_days: int = 7) -> List[YTVideo]:
        """
        Get all videos that need reanalysis based on age and last analysis time.
        
        Args:
            max_age_days: Maximum days before requiring reanalysis for older videos
            force_recent_days: Days threshold for considering a video "recent"
            
        Returns:
            List[YTVideo]: List of videos needing analysis
        """
        with self.Session() as session:
            videos = session.query(YTVideo).all()
            result = YTVideo.filter_needs_reanalysis(videos, max_age_days, force_recent_days)
            return result['needs_analysis']
    
    def __del__(self):
        """Cleanup SQLAlchemy engine when object is destroyed."""
        if hasattr(self, 'engine'):
            self.engine.dispose()