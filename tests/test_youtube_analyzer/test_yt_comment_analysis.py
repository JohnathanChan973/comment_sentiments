import pytest
from unittest.mock import Mock, patch, PropertyMock
from datetime import datetime, timezone
from youtube_analyzer.yt_comment_analysis import YouTubeCommentAnalyzer

def create_mock_video():
    video = Mock()
    video.id = "video1"
    video.title = "Test Video 1"
    video.description = "Test Description"
    # Fix: Use PropertyMock for publish_date instead of a regular Mock
    publish_date_prop = PropertyMock(return_value="2023-01-01T00:00:00Z")
    type(video).publish_date = publish_date_prop
    video.channel_id = "test_channel_id"
    video.channel_title = "Test Channel"
    video.view_count = 1000
    video.like_count = 100
    video.comment_count = 10
    video.get_comments = Mock(return_value=[
        {
            "comment_id": "comment1",
            "text": "Great video!",
            "author": "User1",
            "author_id": "user1_channel",
            "likes": 5,
            "published_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z"
        }
    ])
    return video

def create_mock_video2():
    video2 = Mock()
    video2.id = "video2"
    video2.title = "Test Video 2"
    video2.description = "Test Description 2"
    # Fix: Use PropertyMock for publish_date instead of a regular Mock
    publish_date_prop = PropertyMock(return_value="2023-01-01T00:00:00Z")
    type(video2).publish_date = publish_date_prop
    video2.channel_id = "test_channel_id"
    video2.channel_title = "Test Channel"
    video2.view_count = 2000
    video2.like_count = 200
    video2.comment_count = 20
    video2.get_comments = Mock(return_value=[
        {
            "comment_id": "comment2",
            "text": "Another great video!",
            "author": "User2",
            "author_id": "user2_channel",
            "likes": 10,
            "published_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z"
        }
    ])
    return video2

class MockYouTubeAPI:
    def __init__(self, api_key=None, use_cache=True, max_cache_items=100):
        self.api_key = api_key
        self.use_cache = use_cache
        self.max_cache_items = max_cache_items
        
        self.video1 = create_mock_video()
        self.video2 = create_mock_video2()
        
        # Create mock channel
        self.channel = Mock()
        self.channel.id = "test_channel_id"
        self.channel.name = "Test Channel"
        self.channel.custom_url = "test_channel"
        self.channel.subscriber_count = 1000
        self.channel.video_count = 10
        self.channel.view_count = 10000
        self.channel.published_at = "2023-01-01T00:00:00Z"
        self.channel.country = "US"
        self.channel.uploads_playlist_id = "uploads_playlist_id"
        self.channel.get_video_ids = Mock(return_value=["video1", "video2"])
        
        # Create mock playlist
        self.playlist = Mock()
        self.playlist.id = "test_playlist_id"
        self.playlist.title = "Test Playlist"
        self.playlist.channel_id = "test_channel_id"
        self.playlist.channel_title = "Test Channel"
        self.playlist.item_count = 2
        self.playlist.get_video_ids = Mock(return_value=["video1", "video2"])
        
        # Set up mock methods
        self._setup_mock_methods()
    
    def _setup_mock_methods(self):
        def get_video_impl(video_id):
            if video_id == "video1":
                return self.video1
            elif video_id == "video2":
                return self.video2
            raise ValueError(f"Unknown video ID: {video_id}")
        
        def get_channel_impl(channel_id):
            return self.channel
        
        def get_playlist_impl(playlist_id):
            return self.playlist
        
        # Create Mock objects with our implementations
        self.get_video = Mock(side_effect=get_video_impl)
        self.get_channel = Mock(side_effect=get_channel_impl)
        self.get_playlist = Mock(side_effect=get_playlist_impl)

@pytest.fixture
def mock_api():
    with patch('youtube_analyzer.yt_comment_analysis.YouTubeAPI', new=MockYouTubeAPI):
        api = MockYouTubeAPI()
        yield api

@pytest.fixture
def mock_storage_factory():
    # Create the storage mock
    storage = Mock()
    
    # Set up the storage mock to handle datetime comparisons
    storage.last_analyzed_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    
    # Mock needs_reanalysis to always return True to avoid datetime comparisons
    storage.needs_reanalysis = Mock(return_value=True)
    
    # Mock the save methods to prevent any date comparisons
    storage.save_video = Mock()
    storage.save_channel = Mock()
    storage.save_comments = Mock()
    storage.save_sentiment_results = Mock()
    storage.save_playlist = Mock()
    
    # Create the factory mock
    factory = Mock()
    factory.create_storage = Mock(return_value=storage)
    
    return factory

@pytest.fixture
def mock_sentiment_analyzer():
    analyzer = Mock()
    # Configure the mock analyzer to return one result per comment
    def analyze_batch_impl(comments):
        return [{"sentiment": "positive", "score": 0.8} for _ in comments]
    
    analyzer.analyze_batch = Mock(side_effect=analyze_batch_impl)
    return analyzer

@patch('youtube_analyzer.yt_comment_analysis.StorageFactory')
@patch('youtube_analyzer.yt_comment_analysis.SentimentAnalyzer')
def test_analyze_channel_with_saving(mock_sentiment_cls, mock_factory_cls, mock_api, mock_storage_factory, mock_sentiment_analyzer):
    """Test channel analysis with saving enabled."""
    # Set up the factory to return our storage mock
    mock_factory_cls.return_value = mock_storage_factory
    mock_sentiment_cls.return_value = mock_sentiment_analyzer
    
    analyzer = YouTubeCommentAnalyzer(save=True)
    analyzer.api = mock_api  # Replace the real API with our mock
    
    # Important: Set the storage directly since we're bypassing the factory creation in __init__
    analyzer.storage = mock_storage_factory.create_storage()
    
    results = analyzer.analyze_channel("test_channel_id")
    
    # Verify channel data was fetched
    mock_api.get_channel.assert_called_once_with("test_channel_id")
    
    # Verify storage operations
    storage = mock_storage_factory.create_storage()  # Get the storage mock directly
    assert storage.save_channel.call_count > 0
    assert storage.save_playlist.call_count > 0
    
    # Verify video IDs were fetched
    mock_api.channel.get_video_ids.assert_called_once()
    
    # Verify results
    assert len(results) == 2  # Two videos analyzed

@patch('youtube_analyzer.yt_comment_analysis.StorageFactory')
@patch('youtube_analyzer.yt_comment_analysis.SentimentAnalyzer')
def test_analyze_playlist_with_saving(mock_sentiment_cls, mock_factory_cls, mock_api, mock_storage_factory, mock_sentiment_analyzer):
    """Test playlist analysis with saving enabled."""
    # Set up the factory to return our storage mock
    mock_factory_cls.return_value = mock_storage_factory
    mock_sentiment_cls.return_value = mock_sentiment_analyzer
    
    analyzer = YouTubeCommentAnalyzer(save=True)
    analyzer.api = mock_api  # Replace the real API with our mock
    
    # Important: Set the storage directly since we're bypassing the factory creation in __init__
    analyzer.storage = mock_storage_factory.create_storage()
    
    results = analyzer.analyze_playlist("test_playlist_id")
    
    # Verify playlist data was fetched
    mock_api.get_playlist.assert_called_once_with("test_playlist_id")
    
    # Verify storage operations
    storage = mock_storage_factory.create_storage()  # Get the storage mock directly
    assert storage.save_channel.call_count > 0
    assert storage.save_playlist.call_count > 0
    
    # Verify video IDs were fetched
    mock_api.playlist.get_video_ids.assert_called_once()
    
    # Verify results
    assert len(results) == 2  # Two videos analyzed

@patch('youtube_analyzer.yt_comment_analysis.StorageFactory')
@patch('youtube_analyzer.yt_comment_analysis.SentimentAnalyzer')
def test_analyze_channel_without_saving(mock_sentiment_cls, mock_factory_cls, mock_api, mock_storage_factory, mock_sentiment_analyzer):
    """Test channel analysis with saving disabled."""
    mock_factory_cls.return_value = mock_storage_factory
    mock_sentiment_cls.return_value = mock_sentiment_analyzer
    
    analyzer = YouTubeCommentAnalyzer(save=False)
    analyzer.api = mock_api
    
    results = analyzer.analyze_channel("test_channel_id")
    
    # Verify API calls still happen
    mock_api.get_channel.assert_called_once()
    
    # Verify storage is not called
    storage = mock_storage_factory.create_storage()  # Get the storage mock directly
    storage.save_channel.assert_not_called()
    storage.save_playlist.assert_not_called()

@patch('youtube_analyzer.yt_comment_analysis.StorageFactory')
@patch('youtube_analyzer.yt_comment_analysis.SentimentAnalyzer')
def test_error_handling_channel_fetch(mock_sentiment_cls, mock_factory_cls, mock_api, mock_storage_factory, mock_sentiment_analyzer):
    """Test error handling when channel fetch fails."""
    mock_factory_cls.return_value = mock_storage_factory
    mock_sentiment_cls.return_value = mock_sentiment_analyzer
    
    # Temporarily modify the mock to raise an exception
    original_get_channel = mock_api.get_channel
    mock_api.get_channel = Mock(side_effect=Exception("API Error"))
    
    analyzer = YouTubeCommentAnalyzer()
    analyzer.api = mock_api
    
    results = analyzer.analyze_channel("test_channel_id")
    
    assert results == []  # Should return empty list on error
    
    # Verify no storage operations happened
    storage = mock_storage_factory.create_storage()  # Get the storage mock directly
    storage.save_channel.assert_not_called()
    storage.save_playlist.assert_not_called()
    
    # Restore the original mock
    mock_api.get_channel = original_get_channel

@patch('youtube_analyzer.yt_comment_analysis.StorageFactory')
@patch('youtube_analyzer.yt_comment_analysis.SentimentAnalyzer')
def test_concurrent_video_analysis(mock_sentiment_cls, mock_factory_cls, mock_api, mock_storage_factory, mock_sentiment_analyzer):
    """Test concurrent analysis of multiple videos."""
    mock_factory_cls.return_value = mock_storage_factory
    mock_sentiment_cls.return_value = mock_sentiment_analyzer
    
    analyzer = YouTubeCommentAnalyzer(max_workers=2)
    analyzer.api = mock_api
    
    results = analyzer.analyze_multiple_videos(["video1", "video2"])
    
    # Verify results were collected from both videos
    assert len(results) == 2

@patch('youtube_analyzer.yt_comment_analysis.StorageFactory')
@patch('youtube_analyzer.yt_comment_analysis.SentimentAnalyzer')
def test_storage_datetime_handling(mock_sentiment_cls, mock_factory_cls, mock_api, mock_storage_factory, mock_sentiment_analyzer):
    """Test that storage operations handle datetime values correctly."""
    mock_factory_cls.return_value = mock_storage_factory
    mock_sentiment_cls.return_value = mock_sentiment_analyzer
    
    analyzer = YouTubeCommentAnalyzer(save=True)
    analyzer.api = mock_api
    
    # Important: Set the storage directly since we're bypassing the factory creation in __init__
    analyzer.storage = mock_storage_factory.create_storage()
    
    # Analyze a single video to trigger storage operations
    result = analyzer.analyze_video("video1")
    
    # Get the storage mock
    storage = mock_storage_factory.create_storage()  # Get the storage mock directly
    
    # Verify storage operations were called
    storage.save_video.assert_called_once()
    storage.save_channel.assert_called_once()
    
    # Verify the video data was passed correctly - modified this section to be more flexible
    video_data = storage.save_video.call_args[0][0]  # Get first positional argument
    
    # Check if publish_date is present and in the correct format
    assert "published_at" in video_data
    assert isinstance(video_data["published_at"], datetime)