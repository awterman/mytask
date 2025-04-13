from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks

from mytask.models.tao import GetTaoDividendsResponse, TaoDividendBase
from mytask.routers.v1.tao import get_tao_dividends, run_sentiment_task
from mytask.services.tao_service import Dividend


@pytest.fixture
def mock_dividends():
    """Create mock dividend data"""
    return [
        Dividend(netuid=18, hotkey="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", dividends=1000),
        Dividend(netuid=19, hotkey="5GNJqTPyNqANBkUVMN1LPPrxXnFouWXoe2wNSmmEoLctxiZY", dividends=2000),
    ]


@patch('mytask.routers.v1.tao.run_sentiment_task')
@patch('mytask.routers.v1.tao.get_tao_service')
async def test_get_tao_dividends_without_trade(mock_get_tao_service, mock_run_sentiment_task):
    """Test the get_tao_dividends endpoint without trade flag"""
    # Setup mocks
    mock_tao_service = AsyncMock()
    mock_tao_service.get_cached_dividends.return_value = (
        [
            Dividend(netuid=18, hotkey="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", dividends=1000),
            Dividend(netuid=19, hotkey="5GNJqTPyNqANBkUVMN1LPPrxXnFouWXoe2wNSmmEoLctxiZY", dividends=2000),
        ],
        True
    )
    mock_get_tao_service.return_value = mock_tao_service
    
    # Call the endpoint
    response = await get_tao_dividends(
        netuid=18,
        hotkey=None,
        trade=False,
        background_tasks=BackgroundTasks(),
        tao_service=mock_tao_service
    )
    
    # Verify response
    assert isinstance(response, GetTaoDividendsResponse)
    assert len(response.dividends) == 2
    
    # Check dividend data
    for dividend in response.dividends:
        assert isinstance(dividend, TaoDividendBase)
        assert dividend.cached is True
        assert dividend.stake_tx_triggered is False
    
    # Verify no sentiment task was triggered
    mock_run_sentiment_task.assert_not_called()


@patch('mytask.routers.v1.tao.run_sentiment_task')
@patch('mytask.routers.v1.tao.get_tao_service')
async def test_get_tao_dividends_with_trade(mock_get_tao_service, mock_run_sentiment_task):
    """Test the get_tao_dividends endpoint with trade flag"""
    # Setup mocks
    mock_tao_service = AsyncMock()
    mock_tao_service.get_cached_dividends.return_value = (
        [
            Dividend(netuid=18, hotkey="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", dividends=1000),
            Dividend(netuid=19, hotkey="5GNJqTPyNqANBkUVMN1LPPrxXnFouWXoe2wNSmmEoLctxiZY", dividends=2000),
        ],
        True
    )
    mock_get_tao_service.return_value = mock_tao_service
    
    # Call the endpoint
    background_tasks = BackgroundTasks()
    response = await get_tao_dividends(
        netuid=18,
        hotkey="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v",
        trade=True,
        background_tasks=background_tasks,
        tao_service=mock_tao_service
    )
    
    # Verify response
    assert isinstance(response, GetTaoDividendsResponse)
    assert len(response.dividends) == 2
    
    # Check dividend data - the one matching our netuid and hotkey should have task_id and stake_tx_triggered=True
    for dividend in response.dividends:
        assert isinstance(dividend, TaoDividendBase)
        assert dividend.cached is True
        assert dividend.stake_tx_triggered is True
        
    # Verify the sentiment task was added to background tasks
    assert len(background_tasks.tasks) == 1


# We'll test the run_sentiment_task function integration directly
def test_run_sentiment_task():
    """Test the run_sentiment_task function with mocks for celery task"""
    # Use patch context instead of decorator since we need to access the mock
    with patch('mytask.routers.v1.tao.analyze_sentiment_and_stake') as mock_analyze_sentiment_and_stake:
        # Make the mock return a sample result
        mock_analyze_sentiment_and_stake.return_value = {
            "status": "completed", 
            "netuid": 18, 
            "hotkey": "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
        }
        
        # Call the function with test values
        run_sentiment_task(18, "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v")
        
        # Verify that the mock was called with correct parameters
        mock_analyze_sentiment_and_stake.assert_called_once_with(18, "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v") 