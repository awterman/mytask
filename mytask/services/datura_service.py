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

    async def analyze_subnet_sentiment(
        self,
        netuid: int,
        days_back: int = 7,
        tweet_count: int = 50,
        min_engagement: int = 0,
    ) -> SubnetSentimentAnalysis:
        """
        Search for tweets related to a specific Bittensor subnet and analyze sentiment.

        Args:
            netuid: The netuid of the Bittensor subnet to analyze
            days_back: Number of days to look back for tweets (default: 7)
            tweet_count: Number of tweets to retrieve (default: 50)
            min_engagement: Minimum engagement (likes + retweets) for tweets (default: 0)

        Returns:
            A SubnetSentimentAnalysis object containing analysis results
        """
        # Calculate date range for search (last N days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Construct search query for the specific subnet
        query = f"Bittensor netuid {netuid}"

        # Search tweets
        tweets = await self.search_twitter(
            query=query,
            sort="Latest",  # Get most recent tweets
            start_date=start_date,
            end_date=end_date,
            lang="en",
            min_likes=min_engagement,
            min_retweets=min_engagement,
            count=tweet_count,
        )

        # Basic sentiment analysis
        if not tweets:
            return SubnetSentimentAnalysis(
                netuid=netuid,
                tweet_count=0,
                sentiment="neutral",
                sentiment_score=0,
                tweets=[],
            )

        # Process tweets to extract data
        total_engagement = sum(tweet.engagement for tweet in tweets)
        average_engagement = total_engagement / len(tweets) if tweets else 0

        # Convert tweets to dictionaries for the response
        tweet_data = []
        for tweet in tweets:
            tweet_dict = {
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "url": str(tweet.url),
                "username": tweet.user.username,
                "engagement": tweet.engagement,
            }
            tweet_data.append(tweet_dict)

        # TODO: For more accurate sentiment analysis, you might want to integrate
        # with a dedicated NLP service or model to analyze the tweet texts

        return SubnetSentimentAnalysis(
            netuid=netuid,
            tweet_count=len(tweets),
            date_range=f"{start_date} to {end_date}",
            total_engagement=total_engagement,
            average_engagement=average_engagement,
            tweets=tweet_data,
        )
