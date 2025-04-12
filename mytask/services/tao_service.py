import asyncio

from aiocache import RedisCache, cached
from bittensor import AsyncSubtensor, Balance
from bittensor.core.async_subtensor import AsyncSubstrateInterface
from bittensor.core.chain_data import decode_account_id
from bittensor.core.settings import SS58_FORMAT
from bittensor_wallet import Wallet
from pydantic import BaseModel


class Dividend(BaseModel):
    netuid: int
    hotkey: str
    dividends: int

class TaoService:
    def __init__(self, cache: RedisCache, wallet: Wallet | None = None):
        self.cache = cache
        self.wallet = wallet or Wallet()

        # TODO: make this configurable
        self.subtensor = AsyncSubtensor(network="test")
        self.substrate = AsyncSubstrateInterface("wss://test.finney.opentensor.ai:443", ss58_format=SS58_FORMAT)

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
        @cached(ttl=60*2, key="all_netuids", cache=self.cache) # type: ignore
        async def _inner() -> list[int]:
            return await self.subtensor.get_subnets()
        return await _inner()

    async def get_cached_dividends(self, netuid: int | None, hotkey: str | None) -> list[Dividend]:
        @cached(ttl=60*2, key_builder=lambda func, args, kwargs: _make_cache_key(kwargs["netuid"], kwargs["hotkey"]), cache=self.cache) # type: ignore
        async def _inner() -> list[Dividend]:
            # TODO: refresh all available cache keys
            return await self.get_dividends(netuid, hotkey)
        return await _inner()

    async def get_dividends(self, netuid: int | None, hotkey: str | None) -> list[Dividend]:
        # FIXME: hotkey param is not working
        if netuid is None:
            netuids = await self._get_cached_all_netuids()
        else:
            netuids = [netuid]

        semaphore = asyncio.Semaphore(50)  # Limit concurrent tasks to 4
        async def query_dividends(netuid: int):
            params: list = [netuid]
            if hotkey is not None:
                params.append(hotkey)

            async with semaphore:
                return await self.substrate.query_map(
                    "SubtensorModule",
                    "TaoDividendsPerSubnet",
                    params,
                )

        tasks = [query_dividends(netuid) for netuid in netuids]
        results = await asyncio.gather(*tasks)

        dividends = []
        for netuid, result in zip(netuids, results):
            async for k, v in result: # type: ignore
                dividends.append(Dividend(netuid=netuid, hotkey=decode_account_id(k), dividends=v.value))
        return dividends

    async def stake(self, netuid: int, amount: Balance):
        # FIXME: stake is not working
        return await self.subtensor.add_stake(
            wallet=self.wallet,
            netuid=netuid,
            amount=amount,
        )

    async def unstake(self, netuid: int, amount: Balance):
        # FIXME: unstake is not working
        return await self.subtensor.unstake(
            wallet=self.wallet,
            netuid=netuid,
            amount=amount,
        )
