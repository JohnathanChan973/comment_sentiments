from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from logger_config import get_logger

logger = get_logger("storage")

# Type variables for the storage models
T_Video = TypeVar('T_Video')
T_Comment = TypeVar('T_Comment')
T_Sentiment = TypeVar('T_Sentiment')

# Abstract base class defining the storage interface
class BaseStorage(ABC, Generic[T_Video, T_Comment, T_Sentiment]):
    """
    Abstract base class for different storage implementations.
    Generic type parameters allow different storage implementations to use different model types.
    """
    
    @abstractmethod
    def save_video(self, video_data: Dict[str, Any]) -> T_Video:
        """
        Save or update a video record.
        
        Args:
            video_data: Dictionary containing video information
            
        Returns:
            The saved video object
        """
        pass
    
    @abstractmethod
    def save_comments(self, comments: List[Dict[str, Any]], video_id: str) -> List[T_Comment]:
        """
        Save or update multiple comments for a video.
        
        Args:
            comments: List of comment dictionaries
            video_id: ID of the video these comments belong to
            
        Returns:
            List of saved comment objects
        """
        pass
    
    @abstractmethod
    def save_sentiment_results(self, results: List[Dict[str, Any]]) -> List[T_Sentiment]:
        """
        Save or update sentiment analysis results.
        
        Args:
            results: List of sentiment analysis result dictionaries
            
        Returns:
            List of saved sentiment objects
        """
        pass
    
    @abstractmethod
    def get_video(self, video_id: str) -> Optional[T_Video]:
        """
        Retrieve a video by its ID.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_video_comments(self, video_id: str) -> List[T_Comment]:
        """
        Retrieve all comments for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of comment objects
        """
        pass
    
    @abstractmethod
    def get_comment_sentiment(self, comment_id: str) -> Optional[T_Sentiment]:
        """
        Retrieve sentiment analysis for a comment.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            Sentiment object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_videos_needing_analysis(self, max_age_days: int = 30, 
                                  force_recent_days: int = 7) -> List[T_Video]:
        """
        Get all videos that need reanalysis based on age and last analysis time.
        
        Args:
            max_age_days: Maximum days before requiring reanalysis for older videos
            force_recent_days: Days threshold for considering a video "recent"
            
        Returns:
            List of videos needing analysis
        """
        pass