from typing import Dict, Type, TypeVar
from .base_storage import BaseStorage
from .sqlite_storage import SQLiteStorage
from .file_storage import FileStorage
from logger_config import get_logger

logger = get_logger("storage")

# Type variables for the storage models
T_Video = TypeVar('T_Video')
T_Comment = TypeVar('T_Comment')
T_Sentiment = TypeVar('T_Sentiment')

class StorageFactory(BaseStorage[T_Video, T_Comment, T_Sentiment]):
    """
    Registry-based Factory class that implements the BaseStorage interface.
    This factory dynamically delegates calls to the appropriate storage implementation.
    New storage types can be registered without modifying the factory code.
    """
    # Class-level registry of storage types to their implementation classes
    _storage_registry: Dict[str, Type[BaseStorage]] = {}
    
    @classmethod
    def register_storage_type(cls, storage_type: str, storage_class: Type[BaseStorage]):
        """
        Register a new storage type and its implementation class.
        
        Args:
            storage_type: The name of the storage type (e.g., 'file', 'sqlite')
            storage_class: The class to instantiate for this storage type
        """
        cls._storage_registry[storage_type.lower()] = storage_class
        logger.info(f"Registered storage type: {storage_type}")
    
    def __init__(self, storage_type: str = "sqlite", **kwargs):
        """
        Initialize the storage factory with the specified storage type.
        
        Args:
            storage_type: Type of storage registered in the _storage_registry
            **kwargs: Additional arguments for the storage implementation
        """
        self.storage_type = storage_type.lower()
        self.kwargs = kwargs
        
        # Get the class from the registry
        if self.storage_type in self._storage_registry:
            storage_class = self._storage_registry[self.storage_type]
            self._storage = storage_class(**kwargs)
        else:
            registered_types = ", ".join(self._storage_registry.keys())
            raise ValueError(f"Unknown storage type: {storage_type}. Registered types: {registered_types}")
    
    # Delegate all interface methods to the concrete storage implementation
    def save_video(self, video_data):
        return self._storage.save_video(video_data)
    
    def save_comments(self, comments, video_id):
        return self._storage.save_comments(comments, video_id)
    
    def save_sentiment_results(self, results):
        return self._storage.save_sentiment_results(results)
    
    def get_video(self, video_id):
        return self._storage.get_video(video_id)
    
    def get_video_comments(self, video_id):
        return self._storage.get_video_comments(video_id)
    
    def get_comment_sentiment(self, comment_id):
        return self._storage.get_comment_sentiment(comment_id)
    
    def get_videos_needing_analysis(self, max_age_days=30, force_recent_days=7):
        return self._storage.get_videos_needing_analysis(max_age_days, force_recent_days)
    
    # Static method to create a storage instance (Alternative to constructor)
    @staticmethod
    def create_storage(storage_type: str = "sqlite", **kwargs) -> BaseStorage:
        """
        Create a storage implementation of the specified type.
        
        Args:
            storage_type: Type of storage registered in the _storage_registry
            **kwargs: Additional arguments for the storage implementation
            
        Returns:
            Storage implementation
        """
        return StorageFactory(storage_type, **kwargs)

# Register the built-in storage types
StorageFactory.register_storage_type("file", FileStorage)
StorageFactory.register_storage_type("sqlite", SQLiteStorage)
