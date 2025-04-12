import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from mytask.services.datura_models import SubnetSentimentAnalysis, Tweet
from mytask.services.datura_service import DaturaService

TEST_NETUID = 1
MOCK_TWEET_DATA = [
    {
        "id": "123456789",
        "text": "Excited about Bittensor netuid 1 progress! #TAO #Bittensor",
        "retweet_count": 5,
        "like_count": 10,
        "created_at": "2023-05-01",
        "url": "https://x.com/user/status/123456789",
        "user": {
            "id": "987654321",
            "url": "https://x.com/user",
            "name": "Crypto Enthusiast",
            "username": "crypto_user",
            "followers_count": 500,
            "profile_image_url": "https://pbs.twimg.com/profile_images/1234567890/profile.jpg"
        },
        "media": [],
        "hashtags": ["TAO", "Bittensor"]
    },
    {
        "id": "987654321",
        "text": "Bittensor netuid 1 validators are performing well today! Great rewards.",
        "retweet_count": 3,
        "like_count": 7,
        "created_at": "2023-05-02",
        "url": "https://x.com/user2/status/987654321",
        "user": {
            "id": "123456789",
            "url": "https://x.com/user2",
            "name": "TAO Validator",
            "username": "tao_validator",
            "followers_count": 1200,
            "profile_image_url": "https://pbs.twimg.com/profile_images/0987654321/profile.jpg"
        },
        "media": [],
        "hashtags": []
    }
]


@pytest.fixture
def mock_env_api_key():
    """Set up a mock API key in environment variables"""
    with patch.dict(os.environ, {"DATURA_API_KEY": "test_api_key"}):
        yield


@pytest.fixture
def datura_service():
    """Create a DaturaService instance with a test API key"""
    return DaturaService(api_key="test_api_key")


class MockResponse:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status
    
    async def json(self):
        return self.data
    
    async def text(self):
        return "Error message" if self.status != 200 else ""


@pytest.mark.asyncio
async def test_init_with_direct_api_key():
    """Test initialization with direct API key"""
    service = DaturaService(api_key="direct_test_key")
    assert service.api_key == "direct_test_key"
    assert service.base_url == "https://apis.datura.ai"


@pytest.mark.asyncio
async def test_init_with_env_api_key(mock_env_api_key):
    """Test initialization with API key from environment variable"""
    service = DaturaService()
    assert service.api_key == "test_api_key"


@pytest.mark.asyncio
async def test_init_without_api_key():
    """Test initialization fails without API key"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Datura API key is required"):
            DaturaService()


@pytest.mark.asyncio
async def test_search_twitter(datura_service):
    """Test the search_twitter method with mocked response"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = MockResponse(MOCK_TWEET_DATA)
        mock_get.return_value = mock_context
        
        result = await datura_service.search_twitter(query="Bittensor")
        
        assert len(result) == len(MOCK_TWEET_DATA)
        assert isinstance(result[0], Tweet)
        assert result[0].id == MOCK_TWEET_DATA[0]["id"]
        assert result[0].text == MOCK_TWEET_DATA[0]["text"]
        assert result[0].engagement == 15  # 5 retweets + 10 likes
        
        mock_get.assert_called_once()
        
        # Verify the correct URL and parameters were used
        call_args = mock_get.call_args
        assert "https://apis.datura.ai/twitter" in str(call_args)
        assert "Bittensor" in str(call_args)


@pytest.mark.asyncio
async def test_search_twitter_error(datura_service):
    """Test error handling in search_twitter method"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = MockResponse([], status=404)
        mock_get.return_value = mock_context
        
        with pytest.raises(Exception, match="Datura API error: 404"):
            await datura_service.search_twitter(query="Bittensor")


@pytest.mark.asyncio
async def test_analyze_subnet_sentiment(datura_service):
    """Test the analyze_subnet_sentiment method with mocked search_twitter response"""
    # Mock the search_twitter to return Tweet objects
    tweet_objects = [Tweet.parse_obj(tweet) for tweet in MOCK_TWEET_DATA]
    
    with patch.object(datura_service, "search_twitter", return_value=tweet_objects):
        result = await datura_service.analyze_subnet_sentiment(netuid=TEST_NETUID)
        
        # Verify results structure and content
        assert isinstance(result, SubnetSentimentAnalysis)
        assert result.netuid == TEST_NETUID
        assert result.tweet_count == len(MOCK_TWEET_DATA)
        assert hasattr(result, "date_range")
        assert result.total_engagement == 25  # Sum of all likes and retweets
        assert result.average_engagement == 12.5  # 25 / 2
        assert len(result.tweets) == 2
        
        # Verify date calculation logic by checking if the date range exists
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        assert f"{week_ago} to {today}" == result.date_range
        
        # Verify the search_twitter method was called with the correct parameters
        datura_service.search_twitter.assert_called_once()
        call_args = datura_service.search_twitter.call_args
        assert f"Bittensor netuid {TEST_NETUID}" in str(call_args)
        assert "Latest" in str(call_args)


@pytest.mark.asyncio
async def test_analyze_subnet_sentiment_no_tweets(datura_service):
    """Test the analyze_subnet_sentiment method when no tweets are found"""
    with patch.object(datura_service, "search_twitter", return_value=[]):
        result = await datura_service.analyze_subnet_sentiment(netuid=TEST_NETUID)
        
        # Verify results for empty dataset
        assert isinstance(result, SubnetSentimentAnalysis)
        assert result.netuid == TEST_NETUID
        assert result.tweet_count == 0
        assert result.sentiment == "neutral"
        assert result.sentiment_score == 0
        assert result.tweets == [] 