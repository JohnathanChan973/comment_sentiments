import pytest
from unittest.mock import Mock
from youtube_analyzer.comment_analysis_task import CommentAnalysisTask

@pytest.fixture
def mock_api():
    api = Mock()
    # Mock video data
    video = Mock()
    video.id = "test_video_id"
    video.title = "Test Video"
    video.description = "Test Description"
    video.publish_date = "2023-01-01T00:00:00Z"
    video.channel_id = "test_channel_id"
    video.channel_title = "Test Channel"
    video.view_count = 1000
    video.like_count = 100
    video.comment_count = 10
    
    # Mock comments
    video.get_comments.return_value = [
        {
            "comment_id": "comment1",
            "text": "Great video!",
            "author": "User1",
            "author_id": "user1_channel",
            "likes": 5,
            "published_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z"
        }
    ]
    api.get_video.return_value = video
    return api

@pytest.fixture
def mock_sentiment_analyzer():
    analyzer = Mock()
    analyzer.analyze_batch.return_value = [
        {"sentiment": "positive", "score": 0.8}
    ]
    return analyzer

@pytest.fixture
def mock_storage():
    storage = Mock()
    return storage

def test_full_analysis_with_saving(mock_api, mock_sentiment_analyzer, mock_storage):
    """Test complete analysis flow with saving enabled."""
    task = CommentAnalysisTask(
        "test_video_id",
        mock_api,
        mock_sentiment_analyzer,
        mock_storage,
        save=True
    )
    
    result = task.run()
    
    # Verify API calls
    mock_api.get_video.assert_called_once_with("test_video_id")
    mock_api.get_video.return_value.get_comments.assert_called_once()
    
    # Verify storage calls
    mock_storage.save_channel.assert_called_once()
    mock_storage.save_video.assert_called_once()
    mock_storage.save_comments.assert_called_once()
    mock_storage.save_sentiment_results.assert_called_once()
    
    # Verify sentiment analysis
    mock_sentiment_analyzer.analyze_batch.assert_called_once_with(["Great video!"])
    
    # Verify result structure
    assert result["video_id"] == "test_video_id"
    assert result["video_title"] == "Test Video"
    assert result["comment_count"] == 1
    assert result["sentiment_summary"] == {"positive": 1}
    assert len(result["comments"]) == 1
    assert len(result["sentiment_results"]) == 1

def test_analysis_without_saving(mock_api, mock_sentiment_analyzer, mock_storage):
    """Test analysis flow with saving disabled."""
    task = CommentAnalysisTask(
        "test_video_id",
        mock_api,
        mock_sentiment_analyzer,
        mock_storage,
        save=False
    )
    
    result = task.run()
    
    # Verify API calls still happen
    mock_api.get_video.assert_called_once()
    mock_api.get_video.return_value.get_comments.assert_called_once()
    
    # Verify storage is not called
    mock_storage.save_channel.assert_not_called()
    mock_storage.save_video.assert_not_called()
    mock_storage.save_comments.assert_not_called()
    mock_storage.save_sentiment_results.assert_not_called()
    
    # Verify analysis still works
    assert result["video_id"] == "test_video_id"
    assert len(result["comments"]) == 1
    assert len(result["sentiment_results"]) == 1

def test_error_handling_video_fetch(mock_api, mock_sentiment_analyzer, mock_storage):
    """Test error handling when video fetch fails."""
    mock_api.get_video.side_effect = Exception("API Error")
    
    task = CommentAnalysisTask(
        "test_video_id",
        mock_api,
        mock_sentiment_analyzer,
        mock_storage
    )
    
    with pytest.raises(Exception) as exc:
        task.run()
    assert str(exc.value) == "API Error"
    
    # Verify no other operations happened
    mock_storage.save_video.assert_not_called()
    mock_sentiment_analyzer.analyze_batch.assert_not_called()

def test_error_handling_comments_fetch(mock_api, mock_sentiment_analyzer, mock_storage):
    """Test error handling when comments fetch fails."""
    mock_api.get_video.return_value.get_comments.side_effect = Exception("Comments Error")
    
    task = CommentAnalysisTask(
        "test_video_id",
        mock_api,
        mock_sentiment_analyzer,
        mock_storage
    )
    
    result = task.run()
    
    # Verify video was still saved
    mock_storage.save_video.assert_called_once()
    # Verify no sentiment analysis happened
    mock_sentiment_analyzer.analyze_batch.assert_not_called()
    # Verify empty results
    assert result["comment_count"] == 0
    assert result["sentiment_summary"] == {}
