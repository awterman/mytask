import json
import os
import re
from typing import Any, Dict, List, Optional, Union

import aiohttp
from pydantic import ValidationError

from mytask.services.chutes_models import (ChuteInput, ChuteResponse,
                                           ChutesHistory, ChutesHistoryItem,
                                           TweetSentimentAnalysis,
                                           TweetSentimentRequest,
                                           TweetSentimentScore)


class ChutesService:
    """
    Async service for interacting with Chutes AI API.
    Based on documentation from https://chutes.ai/app/chute/20acffc0-0c5f-58e3-97af-21fc0b261ec4?tab=api
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Chutes service.
        
        Args:
            api_key: Chutes API key. If not provided, attempts to read from CHUTES_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("CHUTES_API_KEY")
        if not self.api_key:
            raise ValueError("Chutes API key is required. Provide it directly or set CHUTES_API_KEY environment variable.")
        
        self.base_url = "https://api.chutes.ai/v1"
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None):
        """
        Make an async request to the Chutes API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request data for POST requests
            
        Returns:
            Response JSON as a dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            request_method = getattr(session, method.lower())
            
            kwargs = {"headers": headers}
            if data and method.upper() == "POST":
                kwargs["json"] = data
            
            async with request_method(url, **kwargs) as response:
                if response.status not in (200, 201):
                    error_text = await response.text()
                    raise Exception(f"Chutes API error: {response.status} - {error_text}")
                
                return await response.json()
    
    async def ask_question(self, 
                     question: str, 
                     context: Optional[str] = None,
                     model: Optional[str] = None) -> ChuteResponse:
        """
        Ask a question to the Chutes AI.
        
        Args:
            question: The question to ask
            context: Optional context to provide additional information
            model: Optional model to use for answering the question
            
        Returns:
            ChuteResponse object containing the answer
        """
        input_data = ChuteInput(
            question=question,
            context=context,
            model=model
        )
        
        response_data = await self._make_request("POST", "chutes", input_data.model_dump(exclude_none=True))
        
        try:
            return ChuteResponse.model_validate(response_data)
        except ValidationError as e:
            raise ValueError(f"Failed to parse Chutes API response: {e}")
    
    async def get_chute_by_id(self, chute_id: str) -> ChuteResponse:
        """
        Get a specific chute by its ID.
        
        Args:
            chute_id: The ID of the chute to retrieve
            
        Returns:
            ChuteResponse object containing the chute data
        """
        response_data = await self._make_request("GET", f"chutes/{chute_id}")
        
        try:
            return ChuteResponse.model_validate(response_data)
        except ValidationError as e:
            raise ValueError(f"Failed to parse Chutes API response: {e}")
    
    async def get_history(self, limit: int = 10, cursor: Optional[str] = None) -> ChutesHistory:
        """
        Get the history of chutes.
        
        Args:
            limit: Maximum number of items to return
            cursor: Pagination cursor for fetching next page
            
        Returns:
            ChutesHistory object containing the history items
        """
        # Use params dict with str values for query parameters
        params = {
            "limit": str(limit)
        }
        if cursor:
            params["cursor"] = cursor
        
        # Construct query string manually
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        endpoint = f"chutes?{query_string}"
        
        response_data = await self._make_request("GET", endpoint)
        
        try:
            return ChutesHistory.model_validate(response_data)
        except ValidationError as e:
            raise ValueError(f"Failed to parse Chutes API response: {e}")
    
    async def analyze_tweet_sentiment(self, 
                                tweets: List[str], 
                                model: str = "unsloth/Llama-3.2-3B-Instruct") -> TweetSentimentAnalysis:
        """
        Analyze the sentiment of tweets using Chutes AI with LLaMA.
        
        Args:
            tweets: List of tweet texts to analyze
            model: The LLM model to use (default: "llama")
            
        Returns:
            TweetSentimentAnalysis object with sentiment scores for each tweet
        """
        # Create a context with tweets for the prompt
        tweet_context = "\n\n".join([f"Tweet: {tweet}" for tweet in tweets])
        
        # Create the prompt for sentiment analysis
        question = """
        Analyze the sentiment of each tweet below and provide a score from -100 to +100.
        -100 represents extremely negative sentiment
        0 represents neutral sentiment
        +100 represents extremely positive sentiment
        
        Format your response as a JSON array of objects with 'tweet', 'score', and 'explanation' fields:
        [
            {"tweet": "...", "score": 75, "explanation": "..."},
            {"tweet": "...", "score": -42, "explanation": "..."},
            ...
        ]
        """
        
        # Use ask_question to send the request
        response = await self.ask_question(
            question=question,
            context=tweet_context,
            model=model
        )
        
        try:
            # Extract JSON array from the response
            answer_text = response.answer
            json_match = re.search(r'\[.*\]', answer_text, re.DOTALL)
            if not json_match:
                raise ValueError("Failed to extract JSON from LLM response")
                
            json_str = json_match.group(0)
            scores_data = json.loads(json_str)
            
            # Create TweetSentimentScore objects
            scores = [
                TweetSentimentScore(
                    tweet=item.get("tweet", tweets[i] if i < len(tweets) else ""),
                    score=item.get("score", 0),
                    explanation=item.get("explanation")
                )
                for i, item in enumerate(scores_data)
            ]
            
            # Calculate statistics
            total_score = sum(score.score for score in scores)
            average_score = total_score / len(scores) if scores else 0
            
            positive_count = sum(1 for score in scores if score.score > 33)
            negative_count = sum(1 for score in scores if score.score < -33)
            neutral_count = sum(1 for score in scores if -33 <= score.score <= 33)
            
            # Create and return the analysis
            return TweetSentimentAnalysis(
                scores=scores,
                average_score=average_score,
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count
            )
            
        except (json.JSONDecodeError, ValueError, IndexError, KeyError) as e:
            raise ValueError(f"Failed to parse sentiment analysis results: {e}. Raw response: {response.answer}")
