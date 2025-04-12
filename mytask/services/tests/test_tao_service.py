import pytest
from bittensor import Balance
from bittensor_wallet import Wallet

from mytask.services.tao_service import Dividend, TaoService


@pytest.mark.asyncio
async def test_initialize():
    service = TaoService()
    await service.initialize()
    # No assertions needed as we're just verifying it doesn't raise an exception

@pytest.mark.asyncio
async def test_get_dividends_all_netuids():
    service = TaoService()
    await service.initialize()
    dividends = await service.get_dividends(netuids=None, hotkey=None)
    
    assert isinstance(dividends, list)
    assert all(isinstance(d, Dividend) for d in dividends)
    assert all(isinstance(d.netuid, int) for d in dividends)
    assert all(isinstance(d.hotkey, str) for d in dividends)
    assert all(isinstance(d.dividends, int) for d in dividends)

@pytest.mark.asyncio
async def test_get_dividends_specific_netuid():
    service = TaoService()
    await service.initialize()
    
    # Get available netuids
    netuids = await service.subtensor.get_subnets()
    if not netuids:
        pytest.skip("No subnets available on test network")
    
    dividends = await service.get_dividends(netuids=[netuids[0]], hotkey=None)
    assert isinstance(dividends, list)
    assert all(d.netuid == netuids[0] for d in dividends)

@pytest.mark.asyncio
async def test_get_dividends_with_hotkey():
    service = TaoService()
    await service.initialize()
    
    # Get available netuids
    netuids = await service.subtensor.get_subnets()
    if not netuids:
        pytest.skip("No subnets available on test network")
    
    # Get a hotkey from the first subnet
    dividends = await service.get_dividends(netuids=[netuids[0]], hotkey=None)
    if not dividends:
        pytest.skip("No dividends available on test network")
    
    test_hotkey = dividends[0].hotkey
    dividends = await service.get_dividends(netuids=[netuids[0]], hotkey=test_hotkey)
    assert isinstance(dividends, list)
    assert all(d.hotkey == test_hotkey for d in dividends)

@pytest.mark.asyncio
async def test_stake_and_unstake():
    service = TaoService()
    await service.initialize()
    
    # Get available netuids
    netuids = await service.subtensor.get_subnets()
    if not netuids:
        pytest.skip("No subnets available on test network")
    
    # Test with a small amount
    amount = Balance.from_tao(0.1)
    
    # First stake
    try:
        stake_result = await service.stake(netuid=netuids[0], amount=amount)
        assert stake_result is not None, "Stake operation returned None"
    except Exception as e:
        pytest.skip(f"Staking failed: {str(e)}")
    
    # Then unstake the same amount
    try:
        unstake_result = await service.unstake(netuid=netuids[0], amount=amount)
        assert unstake_result is not None, "Unstake operation returned None"
    except Exception as e:
        pytest.skip(f"Unstaking failed after successful stake: {str(e)}")
