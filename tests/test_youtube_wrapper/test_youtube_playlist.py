import pytest
from unittest.mock import MagicMock
from youtube_wrapper.youtube_playlist import YouTubePlaylist

@pytest.fixture
def mock_youtube_client():
    """Fixture to create a mock YouTube API client."""
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def mock_playlist_data():
    """Fixture to provide mock video data."""
    return {
        'items': [{
            'snippet': {
                'title': 'Test Playlist',
                'description': 'This is a test playlist description.',
                'channelId': 'UC123456789',
                'channelTitle': 'Test Channel',
            },
            'contentDetails': {
                'itemCount': 10
            }
        }]
    }

@pytest.fixture
def youtube_playlist(mock_youtube_client, mock_playlist_data):
    """Fixture to create a YouTubePlaylist instance with a mock client."""
    mock_youtube_client.playlists().list().execute.return_value = mock_playlist_data
    return YouTubePlaylist(playlist_id="PL123456789", youtube_client=mock_youtube_client)

def test_playlist_name(youtube_playlist):
    assert youtube_playlist.title == 'Test Playlist'

def test_playlist_description(youtube_playlist):
    assert youtube_playlist.description == 'This is a test playlist description.'

def test_playlist_channel_id(youtube_playlist):   
    assert youtube_playlist.channel_id == 'UC123456789'

def test_playlist_channel_title(youtube_playlist):
    assert youtube_playlist.channel_title == 'Test Channel'

def test_playlist_item_count(youtube_playlist):
    assert youtube_playlist.item_count == 10

def test_get_videos(mock_youtube_client, youtube_playlist):
    # Mock playlist items response
    mock_playlist_items = {
        'items': [{
            'contentDetails': {
                'videoId': 'video123'
            }
        }],
        'nextPageToken': None
    }
    mock_youtube_client.playlistItems().list().execute.return_value = mock_playlist_items

    # Mock video details response
    mock_video_details = {
        'items': [{
            'id': 'video123',
            'snippet': {
                'title': 'Test Video',
                'description': 'Test Description',
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
    mock_youtube_client.videos().list().execute.return_value = mock_video_details

    videos = youtube_playlist.get_videos()
    assert len(videos) == 1
    assert videos[0].id == 'video123'
    assert videos[0].title == 'Test Video'
    assert videos[0].description == 'Test Description'
    assert videos[0].publish_date == '2023-01-01T00:00:00Z'
    assert videos[0].view_count == 1000
    assert videos[0].like_count == 100
    assert videos[0].comment_count == 10