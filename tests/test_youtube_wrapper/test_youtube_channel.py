import pytest
from unittest.mock import MagicMock
from youtube_wrapper.youtube_channel import YouTubeChannel

@pytest.fixture
def mock_youtube_client():
    """Fixture to create a mock YouTube API client."""
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def mock_channel_data():
    """Fixture to provide mock video data."""
    return {
        'items': [{
            'snippet': {
                'title': 'Test Channel',
                'description': 'This is a test channel description.',
                'customUrl': '@testchannel',
                'country': 'US',
                'publishedAt': '2023-01-01T00:00:00Z',
            },
            'statistics': {
                'subscriberCount': '1000',
                'videoCount': '10',
                'viewCount': '10000',
            },
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'PL123456789'
                }
            }
        }]
    }

@pytest.fixture
def youtube_channel(mock_youtube_client, mock_channel_data):
    """Fixture to create a YouTubeChannel instance with a mock client."""
    mock_youtube_client.channels().list().execute.return_value = mock_channel_data
    return YouTubeChannel(channel_id="UC123456789", youtube_client=mock_youtube_client)

def test_channel_name(youtube_channel):
    assert youtube_channel.name == 'Test Channel'

def test_channel_description(youtube_channel):
    assert youtube_channel.description == 'This is a test channel description.'

def test_channel_custom_url(youtube_channel):   
    assert youtube_channel.custom_url == '@testchannel'

def test_channel_country(youtube_channel):
    assert youtube_channel.country == 'US'

def test_channel_published_at(youtube_channel):
    assert youtube_channel.published_at == '2023-01-01T00:00:00Z'

def test_channel_subscriber_count(youtube_channel):
    assert youtube_channel.subscriber_count == 1000 

def test_channel_video_count(youtube_channel):
    assert youtube_channel.video_count == 10

def test_channel_view_count(youtube_channel):
    assert youtube_channel.view_count == 10000  

def test_channel_uploads_playlist(youtube_channel):
    assert youtube_channel.uploads_playlist_id == 'PL123456789'



