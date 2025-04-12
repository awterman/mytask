from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class TwitterUser(BaseModel):
    """Twitter user information"""
    id: str
    url: HttpUrl
    name: str
    username: str
    followers_count: int
    profile_image_url: Optional[HttpUrl] = None
    created_at: Optional[str] = None  # Make created_at optional


class Media(BaseModel):
    """Twitter media attachment"""
    media_url: HttpUrl
    type: str


class Tweet(BaseModel):
    """Twitter post model representing response from Datura API"""
    id: str
    text: str
    retweet_count: int
    like_count: int
    created_at: str
    url: HttpUrl
    user: TwitterUser
    media: Optional[List[Media]] = Field(default_factory=list)
    hashtags: Optional[List[str]] = Field(default_factory=list)
    
    @property
    def engagement(self) -> int:
        """Calculate total engagement (likes + retweets)"""
        return self.like_count + self.retweet_count
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore"  # Ignore extra fields in input data
    }


class SubnetSentimentAnalysis(BaseModel):
    """Results of subnet sentiment analysis"""
    netuid: int
    tweet_count: int
    date_range: Optional[str] = None
    total_engagement: int = 0
    average_engagement: float = 0
    sentiment: Optional[str] = "neutral"
    sentiment_score: Optional[float] = 0
    tweets: List[dict] = Field(default_factory=list) 