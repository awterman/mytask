import json
import os
import re
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI
from openai.types.chat.chat_completion_system_message_param import \
    ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_user_message_param import \
    ChatCompletionUserMessageParam
from openai.types.shared_params.response_format_json_object import \
    ResponseFormatJSONObject


class ChutesService:
    """
    Async service for interacting with Chutes AI API.
    Based on documentation from https://chutes.ai/app/chute/20acffc0-0c5f-58e3-97af-21fc0b261ec4?tab=api
    """
    
    def __init__(self, api_key: str):
        base_url = "https://llm.chutes.ai/v1"

        # Local testing because Chutes is unreachable
        api_key = "sk-71MDVSXD1Hkjguu9kqWP8g"
        base_url = "http://192.168.50.213:4000"

        self.llm = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def score_tweet_sentiment(self, 
                                tweets: List[str], 
                                model: str = "unsloth/Llama-3.2-3B-Instruct") -> int:
        """
        Analyze the sentiment of tweets using Chutes AI with LLaMA.
        
        Args:
            tweets: List of tweet texts to analyze
            model: The LLM model to use (default: "unsloth/Llama-3.2-3B-Instruct")
            
        Returns:
            int: The sentiment score for the tweets
        """
        model = "openrouter/google/gemini-2.0-flash-001"
        # Create a context with tweets for the prompt
        tweet_context = "\n\n".join([f"Tweet: {tweet}" for tweet in tweets])
        
        # Create the prompt for sentiment analysis
        prompt = f"""
        Analyze the sentiment of the tweets below and provide a score from -100 to +100.
        -100 represents extremely negative sentiment
        0 represents neutral sentiment
        +100 represents extremely positive sentiment
        
        Tweets:
        {tweet_context}

        Output in JSON format:
        {{
            "score": int,
        }}
        
        """

        response = await self.llm.chat.completions.create(
            model=model,
            messages=[
                ChatCompletionUserMessageParam(
                    role="user",
                    content=prompt,
                ),
            ],
            temperature=0.0,
            response_format=ResponseFormatJSONObject(
                type="json_object",
            ),
        )

        output = response.choices[0].message.content
        assert output is not None
        return json.loads(output)["score"]