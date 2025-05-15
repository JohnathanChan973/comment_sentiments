from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import pandas as pd
from ..base_storage import BaseStorage
from .models import FileVideo, FileComment, FileSentiment
from logger_config import get_logger

logger = get_logger("storage")

# File-based implementation of the storage interface
class FileStorage(BaseStorage[FileVideo, FileComment, FileSentiment]):
    """File-based implementation of the storage interface."""
    
    def __init__(self, path: str = "./data"):
        """
        Initialize storage with a base path.
        
        Args:
            path: Base directory path for storing data
        """
        self.base_path = Path(path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file storage at: {self.base_path}")
    
    def _get_video_path(self, video_id: str) -> Path:
        """Get the path for storing data for a specific video."""
        return self.base_path / video_id
    
    def save_video(self, video_data: Dict[str, Any]) -> FileVideo:
        """Save video data to JSON file."""
        video_path = self._get_video_path(video_data['id'])
        video_path.mkdir(parents=True, exist_ok=True)
        
        video = FileVideo(
            id=video_data['id'],
            title=video_data.get('title', ''),
            description=video_data.get('description', ''),
            published_at=video_data.get('published_at'),
            channel_id=video_data.get('channel_id', ''),
            view_count=video_data.get('view_count', 0),
            like_count=video_data.get('like_count', 0),
            comment_count=video_data.get('comment_count', 0),
            last_analyzed_at=datetime.now(timezone.utc)
        )
        
        video_file = video_path / f"{video.id}_info.json"
        with open(video_file, 'w', encoding='utf-8') as f:
            # Convert datetime objects to ISO format strings for JSON serialization
            video_dict = video._asdict()
            for key, value in video_dict.items():
                if isinstance(value, datetime):
                    video_dict[key] = value.isoformat()
            json.dump(video_dict, f, indent=4)
            
        logger.info(f"Saved video info: {video.id}")
        return video
    
    def save_channel(self, channel_data: Dict[str, Any]) -> Any:
        """
        Empty implementation of channel saving for file storage.
        Channel data is not persisted in file storage.
        """
        logger.info(f"Channel saving not implemented for file storage. Channel ID: {channel_data.get('id')}")
        pass

    def save_playlist(self, playlist_data: Dict[str, Any]) -> Any:
        """
        Empty implementation of playlist saving for file storage.
        Playlist data is not persisted in file storage.
        """
        logger.info(f"Playlist saving not implemented for file storage. Playlist ID: {playlist_data.get('id')}")
        pass

    def save_comments(self, comments: List[Dict[str, Any]], video_id: str) -> List[FileComment]:
        """Save comments to JSON file."""
        video_path = self._get_video_path(video_id)
        video_path.mkdir(parents=True, exist_ok=True)
        
        saved_comments = []
        for comment_data in comments:
            comment = FileComment(
                comment_id=comment_data['comment_id'],
                video_id=video_id,
                text=comment_data.get('text', ''),
                author=comment_data.get('author', ''),
                author_id=comment_data.get('author_id', ''),
                likes=comment_data.get('likes', 0),
                published_at=comment_data.get('published_at'),
                updated_at=comment_data.get('updated_at'),
                last_analyzed_at=datetime.now(timezone.utc)
            )
            saved_comments.append(comment)
        
        comments_file = video_path / f"{video_id}_comments.json"
        with open(comments_file, 'w', encoding='utf-8') as f:
            comments_list = []
            for comment in saved_comments:
                comment_dict = comment._asdict()
                for key, value in comment_dict.items():
                    if isinstance(value, datetime):
                        comment_dict[key] = value.isoformat()
                comments_list.append(comment_dict)
            json.dump(comments_list, f, indent=4)
            
        logger.info(f"Saved {len(saved_comments)} comments for video {video_id}")
        return saved_comments
    
    def save_sentiment_results(self, results: List[Dict[str, Any]]) -> List[FileSentiment]:
        """Save sentiment results to JSON files."""
        saved_sentiments = []
        
        # Group results by video_id
        by_video = {}
        for result in results:
            comment_id = result['comment_id']
            video_id = comment_id.split('_')[0]  # Assuming comment_ids are prefixed with video_id
            if video_id not in by_video:
                by_video[video_id] = []
            sentiment = FileSentiment(
                comment_id=comment_id,
                label=result['label'],
                score=result['score'],
                last_analyzed_at=datetime.now(timezone.utc)
            )
            by_video[video_id].append(sentiment)
            saved_sentiments.append(sentiment)
        
        # Save sentiments grouped by video
        for video_id, sentiments in by_video.items():
            video_path = self._get_video_path(video_id)
            video_path.mkdir(parents=True, exist_ok=True)
            
            sentiment_file = video_path / f"{video_id}_sentiment.json"
            with open(sentiment_file, 'w', encoding='utf-8') as f:
                sentiment_list = []
                for sentiment in sentiments:
                    sentiment_dict = sentiment._asdict()
                    if sentiment_dict['last_analyzed_at']:
                        sentiment_dict['last_analyzed_at'] = sentiment_dict['last_analyzed_at'].isoformat()
                    sentiment_list.append(sentiment_dict)
                json.dump(sentiment_list, f, indent=4)
        
        logger.info(f"Saved {len(saved_sentiments)} sentiment results")
        return saved_sentiments
    
    def get_video(self, video_id: str) -> Optional[FileVideo]:
        """Load video data from JSON file."""
        video_path = self._get_video_path(video_id)
        video_file = video_path / f"{video_id}_info.json"
        
        if not video_file.exists():
            return None
            
        with open(video_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert ISO format strings back to datetime objects
            for key in ['published_at', 'last_analyzed_at']:
                if data.get(key):
                    data[key] = datetime.fromisoformat(data[key])
            return FileVideo(**data)
    
    def get_video_comments(self, video_id: str) -> List[FileComment]:
        """Load comments from JSON file."""
        video_path = self._get_video_path(video_id)
        comments_file = video_path / f"{video_id}_comments.json"
        
        if not comments_file.exists():
            return []
            
        with open(comments_file, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)
            comments = []
            for data in comments_data:
                # Convert ISO format strings back to datetime objects
                for key in ['published_at', 'updated_at', 'last_analyzed_at']:
                    if data.get(key):
                        data[key] = datetime.fromisoformat(data[key])
                comments.append(FileComment(**data))
            return comments
    
    def get_comment_sentiment(self, comment_id: str) -> Optional[FileSentiment]:
        """Load sentiment data for a comment."""
        video_id = comment_id.split('_')[0]  # Assuming comment_ids are prefixed with video_id
        video_path = self._get_video_path(video_id)
        sentiment_file = video_path / f"{video_id}_sentiment.json"
        
        if not sentiment_file.exists():
            return None
            
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            sentiments_data = json.load(f)
            for data in sentiments_data:
                if data['comment_id'] == comment_id:
                    if data.get('last_analyzed_at'):
                        data['last_analyzed_at'] = datetime.fromisoformat(data['last_analyzed_at'])
                    return FileSentiment(**data)
        return None
    
    def get_videos_needing_analysis(self, max_age_days: int = 30, 
                                  force_recent_days: int = 7) -> List[FileVideo]:
        """Get videos that need reanalysis."""
        videos = []
        now = datetime.now(timezone.utc)
        
        # Scan all video directories
        for video_path in self.base_path.iterdir():
            if not video_path.is_dir():
                continue
                
            video_id = video_path.name
            video = self.get_video(video_id)
            if not video:
                continue
                
            # Check if video needs reanalysis
            if not video.last_analyzed_at:
                videos.append(video)
                continue
                
            video_age = now - video.published_at
            time_since_analysis = now - video.last_analyzed_at
            
            if (video_age.days <= force_recent_days or 
                time_since_analysis.days >= max_age_days):
                videos.append(video)
                
        return videos
    
    def save_combined_data(self, comments: List[Dict[str, Any]], 
                          sentiment_results: List[Dict[str, Any]],
                          video_id: str, video_title: Optional[str] = None) -> str:
        """
        Save combined comments and sentiment data to Excel.
        
        Args:
            comments: List of comment dictionaries
            sentiment_results: List of sentiment analysis dictionaries
            video_id: YouTube video ID
            video_title: Video title (optional, for readable filenames)
            
        Returns:
            Path to the saved Excel file
        """
        video_path = self._get_video_path(video_id)
        excel_file = video_path / f"{video_id}_analysis.xlsx"
        
        # Create DataFrames
        df_comments = pd.DataFrame([
            {"comment": c.text, "author": c.author, 
             "likes": c.likes, "published_at": c.published_at}
            for c in self.get_video_comments(video_id)
        ])
        
        df_sentiment = pd.DataFrame([
            {"sentiment": s.label, "score": s.score}
            for s in self.get_comment_sentiment(video_id)
        ])
        
        # Combine DataFrames if they have the same length
        if len(df_comments) == len(df_sentiment):
            df_combined = pd.concat([df_comments, df_sentiment], axis=1)
            
            # Save to Excel
            with pd.ExcelWriter(excel_file) as writer:
                df_combined.to_excel(writer, sheet_name="Combined", index=False)
                df_comments.to_excel(writer, sheet_name="Comments", index=False)
                df_sentiment.to_excel(writer, sheet_name="Sentiment", index=False)
                
            logger.info(f"Saved combined analysis to {excel_file}")
            return str(excel_file)
        else:
            logger.warning(f"Mismatch in data lengths: {len(df_comments)} comments vs {len(df_sentiment)} sentiment results")
            return ""