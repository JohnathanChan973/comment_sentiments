import pytest
from sentiment_analyzer import SentimentAnalyzer

@pytest.fixture(scope="module")
def analyzer():
    return SentimentAnalyzer()

def test_neutral_sentiment(analyzer):
    """Test neutral sentiment analysis."""
    result = analyzer.analyze_text("I just entered the casino")
    assert result['sentiment'] == 'neutral'
    assert 1.0 > result['score'] > 0.5

def test_positive_sentiment(analyzer):
    """Test positive sentiment analysis."""
    result = analyzer.analyze_text("I just won the lottery!")
    assert result['sentiment'] == 'positive'
    assert 1.0 > result['score'] > 0.5

def test_negative_sentiment(analyzer):
    """Test negative sentiment analysis."""
    result = analyzer.analyze_text("I just lost my house...")
    assert result['sentiment'] == 'negative'
    assert 1.0 > result['score'] > 0.5
