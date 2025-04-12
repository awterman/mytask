import os
from typing import Any, Dict, List, Optional, Union

import aiohttp
from pydantic import ValidationError

from mytask.services.chutes_models import (ChuteInput, ChuteResponse,
                                           ChutesHistory, ChutesHistoryItem)


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
