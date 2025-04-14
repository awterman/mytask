import pytest
from bittensor import Balance
from redis.asyncio import Redis

from mytask.common.redis_cache import RedisCache
from mytask.services.tao_service import Dividend, TaoService

TEST_NETUID = 1
TEST_HOTKEY = "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ"

redis_cache = RedisCache(redis=Redis(host="localhost", port=6379, password=""))


async def test_initialize():
    service = TaoService(redis_cache)
    await service.initialize()
    # No assertions needed as we're just verifying it doesn't raise an exception


async def test_get_dividends_all_netuids():
    service = TaoService(redis_cache)
    await service.initialize()
    dividends, is_cached = await service.get_cached_dividends(netuid=None, hotkey=None)

    assert isinstance(dividends, list)
    assert all(isinstance(d, Dividend) for d in dividends)
    assert all(isinstance(d.netuid, int) for d in dividends)
    assert all(isinstance(d.hotkey, str) for d in dividends)
    assert all(isinstance(d.dividends, int) for d in dividends)


async def test_get_dividends_specific_netuid():
    service = TaoService(redis_cache)
    await service.initialize()

    dividends, is_cached = await service.get_cached_dividends(
        netuid=TEST_NETUID, hotkey=None
    )
    assert isinstance(dividends, list)
    assert all(d.netuid == TEST_NETUID for d in dividends)


async def test_get_dividends_with_hotkey():
    service = TaoService(redis_cache)
    await service.initialize()

    dividends, is_cached = await service.get_cached_dividends(
        netuid=TEST_NETUID, hotkey=TEST_HOTKEY
    )
    assert isinstance(dividends, list)
    assert all(d.hotkey == TEST_HOTKEY for d in dividends)


async def test_stake_and_unstake():
    service = TaoService(redis_cache)
    await service.initialize()

    amount = Balance.from_tao(0.1)

    try:
        stake_result = await service.stake(netuid=TEST_NETUID, amount=amount)
        assert stake_result is not None, "Stake operation returned None"
    except Exception as e:
        pytest.fail(f"Staking failed: {str(e)}")

    unstake_result = await service.unstake(netuid=TEST_NETUID, amount=amount)
    assert unstake_result is not None, "Unstake operation returned None"
