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