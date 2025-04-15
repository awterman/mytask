import os
from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp

from mytask.services.datura_models import SubnetSentimentAnalysis, Tweet


class DaturaService:
    """
    Async service for interacting with Datura AI APIs, specifically for Twitter search.
    Based on documentation from https://docs.datura.ai/guides/capabilities/twitter-search
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Datura service.

        Args:
            api_key: Datura API key. If not provided, attempts to read from DATURA_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("DATURA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Datura API key is required. Provide it directly or set DATURA_API_KEY environment variable."
            )

        self.base_url = "https://apis.datura.ai"

    async def search_twitter(
        self,
        query: str,
        sort: Optional[str] = "Top",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        lang: Optional[str] = "en",
        verified: Optional[bool] = None,
        blue_verified: Optional[bool] = None,
        is_quote: Optional[bool] = None,
        is_video: Optional[bool] = None,
        is_image: Optional[bool] = None,
        min_retweets: Optional[int] = 0,
        min_replies: Optional[int] = 0,
        min_likes: Optional[int] = 0,
        count: Optional[int] = 10,
    ) -> List[Tweet]:
        """
        Search for tweets using Datura AI's Twitter search API.

        Args:
            query: Search query for tweets
            sort: Sort by "Top" or "Latest"
            start_date: Start date in UTC (YYYY-MM-DD format)
            end_date: End date in UTC (YYYY-MM-DD format)
            lang: Language code (e.g., en, es, fr)
            verified: Filter for verified users
            blue_verified: Filter for blue checkmark verified users
            is_quote: Include only tweets with quotes
            is_video: Include only tweets with videos
            is_image: Include only tweets with images
            min_retweets: Minimum number of retweets
            min_replies: Minimum number of replies
            min_likes: Minimum number of likes
            count: Number of tweets to retrieve

        Returns:
            List of Tweet objects matching the search criteria
        """
        url = f"{self.base_url}/twitter"

        params = {
            "query": query,
            "sort": sort,
            "lang": lang,
            "min_retweets": min_retweets,
            "min_replies": min_replies,
            "min_likes": min_likes,
            "count": count,
        }

        # Add optional parameters only if they are provided
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if verified is not None:
            params["verified"] = verified
        if blue_verified is not None:
            params["blue_verified"] = blue_verified
        if is_quote is not None:
            params["is_quote"] = is_quote
        if is_video is not None:
            params["is_video"] = is_video
        if is_image is not None:
            params["is_image"] = is_image

        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Datura API error: {response.status} - {error_text}"
                    )

                data = await response.json()
                return [Tweet.model_validate(tweet) for tweet in data]