import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mytask.services.chutes_models import (ChuteResponse, ChutesHistory,
                                           TweetSentimentAnalysis)
from mytask.services.chutes_service import ChutesService


@pytest.mark.asyncio
async def test_ask_question():
    """Test asking a question to Chutes API"""
    # Mock response data
    mock_response = {
        "id": "chute-123456",
        "question": "What is Chutes AI?",
        "answer": "Chutes AI is a service that provides AI-powered question answering capabilities.",
        "model": "gpt-4",
        "created_at": "2023-07-15T12:00:00Z",
        "metadata": {}
    }
    
    # Create a mock for _make_request that we can inspect
    mock_make_request = AsyncMock(return_value=mock_response)
    
    # Create service instance with mocked _make_request method
    with patch.object(ChutesService, '_make_request', mock_make_request):
        service = ChutesService(api_key="dummy_key")
        
        # Call the method being tested
        result = await service.ask_question(
            question="What is Chutes AI?", 
            context="Looking for information about AI services"
        )
        
        # Verify the result
        assert isinstance(result, ChuteResponse)
        assert result.id == "chute-123456"
        assert result.question == "What is Chutes AI?"
        assert result.model == "gpt-4"
        
        # Verify the mocked method was called correctly
        assert mock_make_request.call_count == 1
        # Access args from call_args tuple (args, kwargs)
        args = mock_make_request.call_args[0]
        assert args[0] == "POST"
        assert args[1] == "chutes"


@pytest.mark.asyncio
async def test_get_chute_by_id():
    """Test retrieving a specific chute by ID"""
    # Mock response data
    mock_response = {
        "id": "chute-123456",
        "question": "What is Chutes AI?",
        "answer": "Chutes AI is a service that provides AI-powered question answering capabilities.",
        "model": "gpt-4",
        "created_at": "2023-07-15T12:00:00Z",
        "metadata": {}
    }
    
    # Create a mock for _make_request that we can inspect
    mock_make_request = AsyncMock(return_value=mock_response)
    
    # Create service instance with mocked _make_request method
    with patch.object(ChutesService, '_make_request', mock_make_request):
        service = ChutesService(api_key="dummy_key")
        
        # Call the method being tested
        result = await service.get_chute_by_id("chute-123456")
        
        # Verify the result
        assert isinstance(result, ChuteResponse)
        assert result.id == "chute-123456"
        
        # Verify the mocked method was called correctly
        assert mock_make_request.call_count == 1
        # Access args from call_args tuple (args, kwargs)
        args = mock_make_request.call_args[0]
        assert args[0] == "GET"
        assert args[1] == "chutes/chute-123456"


@pytest.mark.asyncio
async def test_get_history():
    """Test retrieving chutes history"""
    # Mock response data
    mock_response = {
        "items": [
            {
                "id": "chute-123456",
                "question": "What is Chutes AI?",
                "answer": "Chutes AI is a service that provides AI-powered question answering capabilities.",
                "model": "gpt-4",
                "created_at": "2023-07-15T12:00:00Z"
            },
            {
                "id": "chute-789012",
                "question": "How does Chutes AI work?",
                "answer": "Chutes AI uses large language models to provide answers to questions.",
                "model": "gpt-4",
                "created_at": "2023-07-14T10:30:00Z"
            }
        ],
        "count": 2,
        "next_cursor": "cursor_token_123"
    }
    
    # Create a mock for _make_request that we can inspect
    mock_make_request = AsyncMock(return_value=mock_response)
    
    # Create service instance with mocked _make_request method
    with patch.object(ChutesService, '_make_request', mock_make_request):
        service = ChutesService(api_key="dummy_key")
        
        # Call the method being tested
        result = await service.get_history(limit=5)
        
        # Verify the result
        assert isinstance(result, ChutesHistory)
        assert len(result.items) == 2
        assert result.count == 2
        assert result.next_cursor == "cursor_token_123"
        
        # Verify the mocked method was called correctly
        assert mock_make_request.call_count == 1
        # Access args from call_args tuple (args, kwargs)
        args = mock_make_request.call_args[0]
        assert args[0] == "GET"
        assert "chutes?limit=5" in args[1]


@pytest.mark.asyncio
async def test_analyze_tweet_sentiment():
    """Test analyzing sentiment of tweets"""
    # Mock tweets
    tweets = [
        "I'm loving the new features in this app! Great job team!",
        "This service is terrible. I've been waiting for hours with no response.",
        "Just tried the new product, it's okay but nothing special."
    ]
    
    # Mock response from ask_question method
    mock_ask_response = MagicMock()
    mock_ask_response.answer = """
    Here's my sentiment analysis of the tweets:
    
    [
        {
            "tweet": "I'm loving the new features in this app! Great job team!",
            "score": 85,
            "explanation": "Very positive language with exclamation marks"
        },
        {
            "tweet": "This service is terrible. I've been waiting for hours with no response.",
            "score": -75,
            "explanation": "Strong negative words like 'terrible'"
        },
        {
            "tweet": "Just tried the new product, it's okay but nothing special.",
            "score": 10,
            "explanation": "Mostly neutral with slight positive tone"
        }
    ]
    """
    
    # Create service instance with mocked ask_question method
    with patch.object(ChutesService, 'ask_question', AsyncMock(return_value=mock_ask_response)):
        service = ChutesService(api_key="dummy_key")
        
        # Call the method being tested
        result = await service.analyze_tweet_sentiment(tweets, model="llama")
        
        # Verify the result
        assert isinstance(result, TweetSentimentAnalysis)
        assert len(result.scores) == 3
        assert result.scores[0].score == 85
        assert result.scores[1].score == -75
        assert result.scores[2].score == 10
        
        # Verify calculated fields
        assert result.average_score == (85 - 75 + 10) / 3
        assert result.positive_count == 1
        assert result.negative_count == 1
        assert result.neutral_count == 1
        assert result.overall_sentiment == "neutral"  # Average is close to 0


@pytest.mark.asyncio
async def test_missing_api_key():
    """Test initialization with missing API key"""
    # Temporarily clear the environment variable
    with patch.dict(os.environ, {"CHUTES_API_KEY": ""}, clear=True):
        # Attempt to create the service without an API key
        with pytest.raises(ValueError) as excinfo:
            ChutesService()
        
        # Verify the error message
        assert "Chutes API key is required" in str(excinfo.value) 