import pytest
from unittest.mock import MagicMock
from youtube_wrapper.youtube_video import YouTubeVideo

@pytest.fixture
def mock_youtube_client():
    """Fixture to create a mock YouTube API client."""
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def mock_video_data():
    """Fixture to provide mock video data."""
    return {
        'items': [{
            'snippet': {
                'title': 'Test Video',
                'description': 'This is a test video description.',
                'publishedAt': '2023-01-01T00:00:00Z',
                'channelId': 'UC123456789',
                'channelTitle': 'Test Channel'
            },
            'statistics': {
                'viewCount': '1000',
                'likeCount': '100',
                'commentCount': '10'
            }
        }]
    }

@pytest.fixture
def youtube_video(mock_youtube_client, mock_video_data):
    """Fixture to create a YouTubeVideo instance with mock data."""
    mock_youtube_client.videos().list().execute.return_value = mock_video_data
    return YouTubeVideo(video_id='test_video_id', youtube_client=mock_youtube_client)

def test_video_title(youtube_video):
    assert youtube_video.title == 'Test Video'

def test_video_description(youtube_video):
    assert youtube_video.description == 'This is a test video description.'

def test_video_publish_date(youtube_video):
    assert youtube_video.publish_date == '2023-01-01T00:00:00Z'

def test_video_channel_id(youtube_video):
    assert youtube_video.channel_id == 'UC123456789'

def test_video_channel_title(youtube_video):
    assert youtube_video.channel_title == 'Test Channel'

def test_video_view_count(youtube_video):
    assert youtube_video.view_count == 1000

def test_video_like_count(youtube_video):
    assert youtube_video.like_count == 100

def test_video_comment_count(youtube_video):
    assert youtube_video.comment_count == 10

def test_get_comments(mock_youtube_client, youtube_video):
    mock_comments_data = {
        'items': [{
            'snippet': {
                'topLevelComment': {
                    'snippet': {
                        'textDisplay': 'Test comment',
                        'authorDisplayName': 'Test User',
                        'authorChannelId': {'value': 'UC987654321'},
                        'likeCount': 5,
                        'publishedAt': '2023-01-02T00:00:00Z',
                        'updatedAt': '2023-01-02T01:00:00Z'
                    }
                }
            },
            'id': 'comment_id_1'
        }]
    }
    mock_youtube_client.commentThreads().list().execute.return_value = mock_comments_data
    comments = youtube_video.get_comments()
    assert len(comments) == 1
    assert comments[0]['text'] == 'Test comment'
    assert comments[0]['author'] == 'Test User'
    assert comments[0]['likes'] == 5