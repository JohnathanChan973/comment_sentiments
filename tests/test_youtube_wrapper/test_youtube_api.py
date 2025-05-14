import pytest
from unittest.mock import MagicMock, patch
from youtube_wrapper.youtube_api import YouTubeAPI
from youtube_wrapper.youtube_video import YouTubeVideo
from youtube_wrapper.youtube_channel import YouTubeChannel
from youtube_wrapper.youtube_playlist import YouTubePlaylist

@pytest.fixture
def mock_youtube_client():
    """Fixture to create a mock YouTube API client."""
    with patch('youtube_wrapper.youtube_api.build') as mock_build:
        mock_client = MagicMock()
        mock_build.return_value = mock_client
        yield mock_client

@pytest.fixture
def youtube_api(mock_youtube_client):
    """Fixture to create a YouTubeAPI instance with mock client."""
    with patch.dict('os.environ', {'API_KEY': 'test_api_key'}):
        return YouTubeAPI()

@pytest.fixture
def mock_channel_search_response():
    """Fixture for mocking channel search responses"""
    def _make_response(channel_id=None):
        if channel_id:
            return {
                'items': [{
                    'id': {
                        'channelId': channel_id
                    }
                }]
            }
        return {'items': []}  # Empty response for invalid handles
    return _make_response

@pytest.fixture
def mock_channel_response():
    """Fixture for mocking direct channel responses"""
    def _make_response(channel_id=None):
        if channel_id:
            return {
                'items': [{
                    'id': channel_id,
                    'snippet': {'title': 'Test Channel'},
                    'statistics': {'subscriberCount': '1000'}
                }]
            }
        return {'items': []}
    return _make_response

# Test initialization
def test_init_with_api_key():
    api = YouTubeAPI(api_key='test_key')
    assert api.api_key == 'test_key'

def test_init_with_env_var():
    with patch.dict('os.environ', {'API_KEY': 'test_env_key'}):
        api = YouTubeAPI()
        assert api.api_key == 'test_env_key'

def test_init_without_api_key():
    with patch.dict('os.environ', clear=True):
        with pytest.raises(ValueError):
            YouTubeAPI()

# Test video ID extraction
@pytest.mark.parametrize('url,expected_id', [
    ('https://www.youtube.com/watch?v=jrgOiiE3VT8', 'jrgOiiE3VT8'),
    ('https://youtu.be/jrgOiiE3VT8', 'jrgOiiE3VT8'),
    ('https://www.youtube.com/shorts/jrgOiiE3VT8', 'jrgOiiE3VT8'),
    ('jrgOiiE3VT8', 'jrgOiiE3VT8'),
    ('https://youtube.com/watch?v=jrgOiiE3VT8&feature=share', 'jrgOiiE3VT8'),
    ('https://www.google.com/search?q=test', None), # Invalid URL
])
def test_extract_video_id(youtube_api, url, expected_id):
    assert youtube_api.extract_video_id(url) == expected_id

# Test channel ID extraction
@pytest.mark.parametrize('url,expected_id,mock_id', [
    ('https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw', 'UC_x5XG1OV2P6uZZ5FSM9Ttw', None),
    ('https://www.youtube.com/@GoogleDevelopers', 'UC_test_handle', 'UC_test_handle'),
    ('UC_x5XG1OV2P6uZZ5FSM9Ttw', 'UC_x5XG1OV2P6uZZ5FSM9Ttw', None),
    ('invalid_url', None, None),
])
def test_extract_channel_id(youtube_api, mock_youtube_client, mock_channel_search_response, url, expected_id, mock_id):
    # Configure mock for handle lookup
    mock_youtube_client.search().list().execute.return_value = mock_channel_search_response(mock_id)
    
    result = youtube_api.extract_channel_id(url)
    assert result == expected_id

# Test playlist ID extraction
@pytest.mark.parametrize('url,expected_id', [
    ('https://www.youtube.com/playlist?list=PL8DxiWy2Jgidoxn8piMOoE5fKnkMwCP4K', 'PL8DxiWy2Jgidoxn8piMOoE5fKnkMwCP4K'),
    ('PL8DxiWy2Jgidoxn8piMOoE5fKnkMwCP4K', 'PL8DxiWy2Jgidoxn8piMOoE5fKnkMwCP4K'),
    ('invalid_url', None),
])
def test_extract_playlist_id(youtube_api, url, expected_id):
    assert youtube_api.extract_playlist_id(url) == expected_id

# Test get_video
def test_get_video(youtube_api, mock_youtube_client):
    video_id = 'test_video_id'
    mock_youtube_client.videos().list().execute.return_value = {
        'items': [{
            'snippet': {'title': 'Test Video'},
            'statistics': {'viewCount': '100'}
        }]
    }
    
    video = youtube_api.get_video(video_id)
    assert isinstance(video, YouTubeVideo)
    assert video.id == video_id

# Test get_channel
def test_get_channel(youtube_api, mock_youtube_client, mock_channel_search_response, mock_channel_response):
    channel_id = 'UC_test_channel'
    
    # Mock the search response for handle resolution
    mock_youtube_client.search().list().execute.return_value = mock_channel_search_response(channel_id)
    
    # Mock the channel details response
    mock_youtube_client.channels().list().execute.return_value = mock_channel_response(channel_id)
    
    channel = youtube_api.get_channel(channel_id)
    assert isinstance(channel, YouTubeChannel)
    assert channel.id == channel_id

# Test get_playlist
def test_get_playlist(youtube_api, mock_youtube_client):
    playlist_id = 'PL_test_playlist'
    mock_youtube_client.playlists().list().execute.return_value = {
        'items': [{
            'snippet': {'title': 'Test Playlist'},
            'contentDetails': {'itemCount': '10'}
        }]
    }
    
    playlist = youtube_api.get_playlist(playlist_id)
    assert isinstance(playlist, YouTubePlaylist)
    assert playlist.id == playlist_id

# Test caching
def test_caching_enabled(youtube_api):
    assert youtube_api.use_cache == True
    assert youtube_api._video_cache == {}
    assert youtube_api._channel_cache == {}
    assert youtube_api._playlist_cache == {}

def test_cache_video(youtube_api, mock_youtube_client):
    video_id = 'test_video_id'
    mock_youtube_client.videos().list().execute.return_value = {
        'items': [{
            'snippet': {'title': 'Test Video'},
            'statistics': {'viewCount': '100'}
        }]
    }
    
    # First call should create cache entry
    video1 = youtube_api.get_video(video_id)
    # Second call should return cached object
    video2 = youtube_api.get_video(video_id)
    assert video1 is video2

def test_clear_caches(youtube_api):
    youtube_api._video_cache['test'] = 'data'
    youtube_api._channel_cache['test'] = 'data'
    youtube_api._playlist_cache['test'] = 'data'
    
    youtube_api.clear_caches()
    assert len(youtube_api._video_cache) == 0
    assert len(youtube_api._channel_cache) == 0
    assert len(youtube_api._playlist_cache) == 0

def test_cache_stats(youtube_api):
    youtube_api._video_cache['test'] = 'data'
    stats = youtube_api.get_cache_stats()
    
    assert stats['caching_enabled'] == True
    assert stats['video_cache_size'] == 1
    assert stats['channel_cache_size'] == 0
    assert stats['playlist_cache_size'] == 0