from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class ChuteInput(BaseModel):
    """Input for a Chute API request"""
    question: str
    context: Optional[str] = None
    model: Optional[str] = None


class ChuteResponse(BaseModel):
    """Response from a Chute API request"""
    id: str
    question: str
    answer: str
    context: Optional[str] = None
    model: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChutesHistoryItem(BaseModel):
    """Represents a single item in the Chutes history"""
    id: str
    question: str
    answer: str
    model: str
    created_at: str


class ChutesHistory(BaseModel):
    """Response for Chutes history endpoint"""
    items: List[ChutesHistoryItem]
    count: int
    next_cursor: Optional[str] = None


class TweetSentimentRequest(BaseModel):
    """Request body for analyzing sentiment of tweets"""
    tweets: List[str]
    model: Optional[str] = "llama"


class TweetSentimentScore(BaseModel):
    """Sentiment score for a single tweet"""
    tweet: str
    score: int
    explanation: Optional[str] = None


class TweetSentimentAnalysis(BaseModel):
    """Results of sentiment analysis on tweets"""
    scores: List[TweetSentimentScore]
    average_score: float
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    
    @property
    def overall_sentiment(self) -> str:
        """Return the overall sentiment classification based on average score"""
        if self.average_score > 33:
            return "positive"
        elif self.average_score < -33:
            return "negative"
        else:
            return "neutral" 