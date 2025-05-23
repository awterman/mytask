import asyncio

from bittensor import AsyncSubtensor, Balance
from bittensor.core.async_subtensor import AsyncSubstrateInterface
from bittensor.core.chain_data import decode_account_id
from bittensor.core.settings import SS58_FORMAT
from bittensor_wallet import Wallet
from pydantic import BaseModel

from mytask.common.logger import get_logger
from mytask.common.redis_cache import RedisCache, redis_cache
from mytask.common.singleton import async_singleton
from mytask.models.tao import TaoDividendDAO
from mytask.services.redis_cache import get_redis_cache
from mytask.tables.tao import TaoDividendTable

logger = get_logger()


class Dividend(BaseModel):
    netuid: int
    hotkey: str
    dividends: int


class TaoService:
    def __init__(self, cache: RedisCache, wallet: Wallet | None = None):
        """
        Initialize the TaoService.

        Args:
            cache (RedisCache): The cache to use for caching.
            wallet (Wallet): The wallet to use for staking. The wallet must have a hotkey and registered on the network.
        """
        self.cache = cache
        self.wallet = wallet or Wallet()

        # TODO: make this configurable
        self.subtensor = AsyncSubtensor(network="test")
        self.substrate = AsyncSubstrateInterface(
            "wss://test.finney.opentensor.ai:443", ss58_format=SS58_FORMAT
        )

    async def initialize(self):
        await self.subtensor.initialize()
        await self.substrate.initialize()

    def _make_cache_key(self, netuid: int | None, hotkey: str | None) -> str:
        # both none
        if netuid is None and hotkey is None:
            return "all"
        # netuids none
        if netuid is None:
            return f"hotkey:{hotkey}"
        # hotkey none
        if hotkey is None:
            return f"netuid:{netuid}"
        # both not none
        return f"netuid:{netuid},hotkey:{hotkey}"

    async def _get_cached_all_netuids(self) -> list[int]:
        logger.info("Getting cached all netuids")

        # Due to the slow network, we cache for 1 hour instead of 2 minutes
        @redis_cache(
            redis_cache=self.cache,
            ttl=60 * 60,
            key_builder=lambda *args, **kwargs: "all_netuids",
        )
        async def _inner() -> list[int]:
            logger.info("Cache miss, getting all netuids")
            return await self.subtensor.get_subnets()

        return await _inner()

    async def get_cached_dividends(
        self, netuid: int | None, hotkey: str | None
    ) -> tuple[list[Dividend], bool]:
        logger.info(f"Getting cached dividends for {netuid} and {hotkey}")

        cache_key = self._make_cache_key(netuid, hotkey)
        is_cached = True

        logger.info(f"Cache key: {cache_key}")

        # Due to the slow network, we cache for 1 hour instead of 2 minutes
        @redis_cache(
            redis_cache=self.cache,
            ttl=60 * 60,
            key_builder=lambda *args, **kwargs: cache_key,
        )
        async def _inner() -> list[Dividend]:
            # TODO: refresh all available cache keys
            nonlocal is_cached
            is_cached = False

            logger.info("Cache miss, getting dividends")
            dividends = await self.get_dividends(netuid, hotkey)
            logger.info(f"Got {len(dividends)} dividends for {netuid} and {hotkey}")

            tao_table = TaoDividendTable()
            logger.info(f"Creating {len(dividends)} dividends in table")
            try:
                for dividend in dividends:
                    await tao_table.create(
                        TaoDividendDAO(
                            netuid=dividend.netuid,
                            hotkey=dividend.hotkey,
                            dividend=dividend.dividends,
                        )
                    )
            except Exception as e:
                logger.error(f"Error creating dividends: {e}")

            return dividends

        dividends = await _inner()
        return dividends, is_cached

    async def get_dividends(
        self, netuid: int | None, hotkey: str | None
    ) -> list[Dividend]:
        if netuid is None:
            logger.info("Getting all netuids")
            netuids = await self._get_cached_all_netuids()
        else:
            netuids = [netuid]

        semaphore = asyncio.Semaphore(100)  # Limit concurrent tasks to 4

        async def query_dividends(netuid: int):
            params: list = [netuid]

            async with semaphore:
                return await self.substrate.query_map(
                    "SubtensorModule",
                    "TaoDividendsPerSubnet",
                    params,
                )

        logger.info(f"Querying dividends for {netuids}")
        tasks = [query_dividends(netuid) for netuid in netuids]
        results = await asyncio.gather(*tasks)

        dividends = []
        for netuid, result in zip(netuids, results):
            async for k, v in result:  # type: ignore
                dividends.append(
                    Dividend(
                        netuid=netuid, hotkey=decode_account_id(k), dividends=v.value
                    )
                )

        if hotkey is not None:
            dividends = [dividend for dividend in dividends if dividend.hotkey == hotkey]

        return dividends

    async def stake(self, netuid: int, amount: Balance) -> bool:
        """
        Stake TAO on a subnet.

        Args:
            netuid (int): The subnet ID to stake on.
            amount (Balance): The amount of TAO to stake.

        Returns:
            bool: True if the stake was successful, False otherwise.
        """
        logger.info(f"Staking {amount} TAO on netuid {netuid}")

        return await self.subtensor.add_stake(
            wallet=self.wallet,
            netuid=netuid,
            amount=amount,
        )

    async def unstake(self, netuid: int, amount: Balance) -> bool:
        """
        Unstake TAO from a subnet.

        Args:
            netuid (int): The subnet ID to unstake from.
            amount (Balance): The amount of TAO to unstake.

        Returns:
            bool: True if the unstake was successful, False otherwise.
        """
        logger.info(f"Unstaking {amount} TAO from netuid {netuid}")

        return await self.subtensor.unstake(
            wallet=self.wallet,
            netuid=netuid,
            amount=amount,
        )


@async_singleton
async def get_tao_service() -> TaoService:
    cache = get_redis_cache()
    tao_service = TaoService(cache)
    logger.info("Initializing TaoService")
    await tao_service.initialize()
    logger.info("TaoService initialized")
    return tao_service
