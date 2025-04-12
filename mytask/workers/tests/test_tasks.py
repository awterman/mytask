import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bittensor import Balance
from pydantic import HttpUrl

from mytask.services.chutes_service import (TweetSentimentAnalysis,
                                            TweetSentimentScore)
from mytask.services.datura_models import Tweet, TwitterUser
from mytask.workers.tasks import analyze_sentiment_and_stake


@pytest.fixture
def mock_twitter_user():
    """Create a sample Twitter user for testing"""
    return TwitterUser(
        id="12345",
        username="test_user",
        name="Test User",
        url=HttpUrl("https://twitter.com/test_user"),
        followers_count=1000
    )


@pytest.fixture
def mock_another_twitter_user():
    """Create another sample Twitter user for testing"""
    return TwitterUser(
        id="67890",
        username="another_user",
        name="Another User",
        url=HttpUrl("https://twitter.com/another_user"),
        followers_count=2000
    )


@pytest.fixture
def mock_tweet(mock_twitter_user):
    """Create a sample tweet for testing"""
    return Tweet(
        id="1234567890",
        text="Bittensor netuid 18 is looking really promising! Great tech and community.",
        retweet_count=5,
        like_count=10,
        created_at="2023-01-01T12:00:00Z",
        url=HttpUrl("https://twitter.com/user/status/1234567890"),
        user=mock_twitter_user
    )


@pytest.fixture
def mock_tweets(mock_tweet, mock_another_twitter_user):
    """Create a list of sample tweets for testing"""
    return [
        mock_tweet,
        Tweet(
            id="9876543210",
            text="Bittensor netuid 18 has some challenges but overall positive outlook!",
            retweet_count=3,
            like_count=8,
            created_at="2023-01-02T12:00:00Z",
            url=HttpUrl("https://twitter.com/user/status/9876543210"),
            user=mock_another_twitter_user
        )
    ]


@pytest.fixture
def mock_positive_sentiment():
    """Create a positive sentiment analysis result"""
    return TweetSentimentAnalysis(
        scores=[
            TweetSentimentScore(
                tweet="Bittensor netuid 18 is looking really promising! Great tech and community.",
                score=75,
                explanation="Very positive sentiment about the technology and community."
            ),
            TweetSentimentScore(
                tweet="Bittensor netuid 18 has some challenges but overall positive outlook!",
                score=25,
                explanation="Acknowledges challenges but maintains a positive outlook."
            )
        ],
        average_score=50,
        positive_count=2,
        negative_count=0,
        neutral_count=0
    )


@pytest.fixture
def mock_negative_sentiment():
    """Create a negative sentiment analysis result"""
    return TweetSentimentAnalysis(
        scores=[
            TweetSentimentScore(
                tweet="Bittensor netuid 18 is facing significant issues with scalability.",
                score=-60,
                explanation="Negative sentiment about technical problems."
            ),
            TweetSentimentScore(
                tweet="Not happy with the direction of Bittensor netuid 18 lately.",
                score=-40,
                explanation="General dissatisfaction with the project direction."
            )
        ],
        average_score=-50,
        positive_count=0,
        negative_count=2,
        neutral_count=0
    )


@patch('mytask.workers.tasks.get_tao_service')
@patch('mytask.workers.tasks.ChutesService')
@patch('mytask.workers.tasks.DaturaService')
def test_analyze_sentiment_and_stake_positive(
    mock_datura_service_class, 
    mock_chutes_service_class, 
    mock_get_tao_service,
    mock_tweets,
    mock_positive_sentiment
):
    """Test the sentiment analysis task with positive sentiment"""
    # Setup mocks
    mock_datura_service = AsyncMock()
    mock_datura_service.search_twitter.return_value = mock_tweets
    mock_datura_service_class.return_value = mock_datura_service
    
    mock_chutes_service = AsyncMock()
    mock_chutes_service.analyze_tweet_sentiment.return_value = mock_positive_sentiment
    mock_chutes_service_class.return_value = mock_chutes_service
    
    mock_tao_service = AsyncMock()
    mock_tao_service.initialize = AsyncMock()
    mock_tao_service.stake.return_value = "transaction_hash_12345"
    
    # Make get_tao_service return the service directly instead of requiring await
    mock_get_tao_service.return_value = mock_tao_service
    
    # Call the task
    result = analyze_sentiment_and_stake(18, "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v")
    
    # Verify the result
    assert result["status"] == "completed"
    assert result["sentiment_score"] == 50
    assert result["action"] == "stake"
    assert result["amount"] == 0.5  # 0.01 * 50
    assert result["tx_result"] == "transaction_hash_12345"
    
    # Verify service calls
    mock_datura_service.search_twitter.assert_called_once()
    mock_chutes_service.analyze_tweet_sentiment.assert_called_once()
    
    # Verify stake was called with correct parameters
    mock_tao_service.stake.assert_called_once()
    _, kwargs = mock_tao_service.stake.call_args
    assert kwargs["netuid"] == 18
    assert isinstance(kwargs["amount"], Balance)
    assert float(kwargs["amount"]) == 0.5


@patch('mytask.workers.tasks.get_tao_service')
@patch('mytask.workers.tasks.ChutesService')
@patch('mytask.workers.tasks.DaturaService')
def test_analyze_sentiment_and_stake_negative(
    mock_datura_service_class, 
    mock_chutes_service_class, 
    mock_get_tao_service,
    mock_tweets,
    mock_negative_sentiment
):
    """Test the sentiment analysis task with negative sentiment"""
    # Setup mocks
    mock_datura_service = AsyncMock()
    mock_datura_service.search_twitter.return_value = mock_tweets
    mock_datura_service_class.return_value = mock_datura_service
    
    mock_chutes_service = AsyncMock()
    mock_chutes_service.analyze_tweet_sentiment.return_value = mock_negative_sentiment
    mock_chutes_service_class.return_value = mock_chutes_service
    
    mock_tao_service = AsyncMock()
    mock_tao_service.initialize = AsyncMock()
    mock_tao_service.unstake.return_value = "transaction_hash_67890"
    
    # Make get_tao_service return the service directly instead of requiring await
    mock_get_tao_service.return_value = mock_tao_service
    
    # Call the task
    result = analyze_sentiment_and_stake(18, "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v")
    
    # Verify the result
    assert result["status"] == "completed"
    assert result["sentiment_score"] == -50
    assert result["action"] == "unstake"
    assert result["amount"] == 0.5  # 0.01 * abs(-50)
    assert result["tx_result"] == "transaction_hash_67890"
    
    # Verify service calls
    mock_datura_service.search_twitter.assert_called_once()
    mock_chutes_service.analyze_tweet_sentiment.assert_called_once()
    
    # Verify unstake was called with correct parameters
    mock_tao_service.unstake.assert_called_once()
    _, kwargs = mock_tao_service.unstake.call_args
    assert kwargs["netuid"] == 18
    assert isinstance(kwargs["amount"], Balance)
    assert float(kwargs["amount"]) == 0.5


@patch('mytask.workers.tasks.get_tao_service')
@patch('mytask.workers.tasks.ChutesService')
@patch('mytask.workers.tasks.DaturaService')
def test_analyze_sentiment_and_stake_no_tweets(
    mock_datura_service_class, 
    mock_chutes_service_class, 
    mock_get_tao_service
):
    """Test the sentiment analysis task when no tweets are found"""
    # Setup mocks
    mock_datura_service = AsyncMock()
    mock_datura_service.search_twitter.return_value = []
    mock_datura_service_class.return_value = mock_datura_service
    
    mock_chutes_service = AsyncMock()
    
    mock_tao_service = AsyncMock()
    mock_tao_service.initialize = AsyncMock()
    
    # Make get_tao_service return the service directly instead of requiring await
    mock_get_tao_service.return_value = mock_tao_service
    
    # Call the task
    result = analyze_sentiment_and_stake(18, "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v")
    
    # Verify the result
    assert result["status"] == "no_tweets"
    assert result["netuid"] == 18
    assert result["hotkey"] == "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
    
    # Verify service calls
    mock_datura_service.search_twitter.assert_called_once()
    mock_chutes_service.analyze_tweet_sentiment.assert_not_called()
    
    # Verify no stake/unstake calls were made
    mock_tao_service.stake.assert_not_called()
    mock_tao_service.unstake.assert_not_called()


@patch('mytask.workers.tasks.get_tao_service')
@patch('mytask.workers.tasks.ChutesService')
@patch('mytask.workers.tasks.DaturaService')
def test_analyze_sentiment_and_stake_default_values(
    mock_datura_service_class, 
    mock_chutes_service_class, 
    mock_get_tao_service,
    mock_tweets,
    mock_positive_sentiment
):
    """Test the sentiment analysis task with default parameter values"""
    # Setup mocks
    mock_datura_service = AsyncMock()
    mock_datura_service.search_twitter.return_value = mock_tweets
    mock_datura_service_class.return_value = mock_datura_service
    
    mock_chutes_service = AsyncMock()
    mock_chutes_service.analyze_tweet_sentiment.return_value = mock_positive_sentiment
    mock_chutes_service_class.return_value = mock_chutes_service
    
    mock_tao_service = AsyncMock()
    mock_tao_service.initialize = AsyncMock()
    mock_tao_service.stake.return_value = "transaction_hash_default"
    
    # Make get_tao_service return the service directly instead of requiring await
    mock_get_tao_service.return_value = mock_tao_service
    
    # Call the task with None values
    result = analyze_sentiment_and_stake(None, None)
    
    # Verify default values were used
    mock_datura_service.search_twitter.assert_called_once()
    query_args = mock_datura_service.search_twitter.call_args[1]
    assert "Bittensor netuid 18" in query_args["query"]
    
    # Verify stake was called with default parameters
    mock_tao_service.stake.assert_called_once()
    _, kwargs = mock_tao_service.stake.call_args
    assert kwargs["netuid"] == 18
    assert isinstance(kwargs["amount"], Balance)
    assert float(kwargs["amount"]) == 0.5 