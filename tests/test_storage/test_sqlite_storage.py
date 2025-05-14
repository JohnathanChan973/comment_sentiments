from datetime import datetime, timezone
import os
import shutil
from pathlib import Path
from storage.sqlite_storage import SQLiteStorage

def setup_test_db():
    """Setup a fresh test database inside the test package directory."""
    # Get the path of the current test file's directory
    test_dir = Path(__file__).resolve().parent  # Resolves the current file's directory
    
    # Define the test_data path relative to the test directory
    test_data_dir = test_dir / "test_data"
    
    if test_data_dir.exists():
        try:
            shutil.rmtree(test_data_dir)
        except PermissionError:
            print("Warning: Could not remove test database directory. It may be in use.")
    os.makedirs(test_data_dir, exist_ok=True)
    return SQLiteStorage(path=test_data_dir, db_name="test_youtube_analysis")

def teardown_storage(storage):
    """Properly cleanup storage connections."""
    if hasattr(storage, 'engine'):
        storage.engine.dispose()

def test_video_creation():
    """Test creating and retrieving a video."""
    storage = setup_test_db()
    try:
        # Test data
        video_data = {
            "id": "test123",
            "title": "Test Video",
            "description": "A test video description",
            "published_at": datetime.now(timezone.utc),
            "channel_id": "test_channel",
            "view_count": 1000,
            "like_count": 100,
            "comment_count": 10
        }
        
        # Save video
        saved_video = storage.save_video(video_data)
        print(f"Saved video: {saved_video}")
        
        # Retrieve video
        retrieved_video = storage.get_video("test123")
        print(f"Retrieved video: {retrieved_video}")
        assert retrieved_video.id == video_data["id"]
        assert retrieved_video.title == video_data["title"]
    finally:
        teardown_storage(storage)
    
def test_comments_creation():
    """Test creating and retrieving comments."""
    storage = setup_test_db()
    try:
        # First create a video
        video_data = {
            "id": "test456",
            "title": "Test Video for Comments",
            "published_at": datetime.now(timezone.utc)
        }
        storage.save_video(video_data)
        
        # Test comments
        comments_data = [
            {
                "comment_id": "comment1",
                "text": "Great video!",
                "author": "User1",
                "author_id": "user1_id",
                "likes": 5,
                "published_at": datetime.now(timezone.utc)
            },
            {
                "comment_id": "comment2",
                "text": "Very informative",
                "author": "User2",
                "author_id": "user2_id",
                "likes": 3,
                "published_at": datetime.now(timezone.utc)
            }
        ]
        
        # Save comments
        saved_comments = storage.save_comments(comments_data, "test456")
        print(f"Saved {len(saved_comments)} comments")
        
        # Retrieve comments
        retrieved_comments = storage.get_video_comments("test456")
        print(f"Retrieved {len(retrieved_comments)} comments")
        assert len(retrieved_comments) == 2
    finally:
        teardown_storage(storage)
    
def test_sentiment_creation():
    """Test creating and retrieving sentiment analysis."""
    storage = setup_test_db()
    try:
        # Create video and comment first
        video_data = {"id": "test789", "title": "Test Video for Sentiment", "published_at": datetime.now(timezone.utc)}
        storage.save_video(video_data)
        
        comment_data = [{
            "comment_id": "comment_for_sentiment",
            "text": "Amazing content!",
            "author": "User3",
            "published_at": datetime.now(timezone.utc)
        }]
        storage.save_comments(comment_data, "test789")
        
        # Test sentiment
        sentiment_data = [{
            "comment_id": "comment_for_sentiment",
            "label": "positive",
            "score": 0.95
        }]
        
        # Save and verify sentiment in the same session
        with storage.Session() as session:
            saved_sentiments = storage.save_sentiment_results(sentiment_data)
            
            # Refresh the sentiment object to ensure it's bound to the session
            sentiment = session.merge(saved_sentiments[0])
            print(f"Saved sentiment: {sentiment}")
            
            # Retrieve and verify sentiment
            retrieved_sentiment = session.get(type(sentiment), "comment_for_sentiment")
            print(f"Retrieved sentiment: {retrieved_sentiment}")
            assert retrieved_sentiment.label == "positive"
            assert retrieved_sentiment.score == 0.95
    finally:
        teardown_storage(storage)

def test_relationships():
    """Test that relationships between models work correctly."""
    storage = setup_test_db()
    try:
        # Create test data
        video_data = {
            "id": "test_rel",
            "title": "Test Relationships",
            "published_at": datetime.now(timezone.utc)
        }
        storage.save_video(video_data)
        
        comment_data = [{
            "comment_id": "comment_rel",
            "text": "Testing relationships",
            "author": "User4",
            "published_at": datetime.now(timezone.utc)
        }]
        storage.save_comments(comment_data, "test_rel")
        
        sentiment_data = [{
            "comment_id": "comment_rel",
            "label": "neutral",
            "score": 0.5
        }]
        storage.save_sentiment_results(sentiment_data)
        
        with storage.Session() as session:
            # Test video -> comments relationship
            video = session.get(storage.get_video("test_rel").__class__, "test_rel")
            print(f"Video comments: {video.comments}")
            assert len(video.comments) == 1
            assert video.comments[0].comment_id == "comment_rel"
            
            # Test comment -> sentiment relationship
            comment = video.comments[0]
            print(f"Comment sentiment: {comment.sentiment}")
            assert comment.sentiment.label == "neutral"
            
            # Test sentiment -> comment relationship
            sentiment = session.get(comment.sentiment.__class__, "comment_rel")
            print(f"Sentiment's comment: {sentiment.comment}")
            assert sentiment.comment.text == "Testing relationships"
    finally:
        teardown_storage(storage)

if __name__ == "__main__":
    print("Testing video creation...")
    test_video_creation()
    
    print("\nTesting comments creation...")
    test_comments_creation()
    
    print("\nTesting sentiment creation...")
    test_sentiment_creation()
    
    print("\nTesting relationships...")
    test_relationships()
    
    print("\nAll tests completed successfully!") 