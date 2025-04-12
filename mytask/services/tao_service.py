import asyncio

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
    def __init__(self, wallet: Wallet | None = None):
        self.wallet = wallet or Wallet()

        # TODO: make this configurable
        self.subtensor = AsyncSubtensor(network="test")
        self.substrate = AsyncSubstrateInterface("wss://test.finney.opentensor.ai:443", ss58_format=SS58_FORMAT)

    async def initialize(self):
        await self.subtensor.initialize()
        await self.substrate.initialize()

    async def get_dividends(self, netuids: list[int] | None, hotkey: str | None) -> list[Dividend]:
        if netuids is None:
            netuids = await self.subtensor.get_subnets()

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
        return await self.subtensor.add_stake(
            wallet=self.wallet,
            netuid=netuid,
            amount=amount,
        )

    async def unstake(self, netuid: int, amount: Balance):
        return await self.subtensor.unstake(
            wallet=self.wallet,
            netuid=netuid,
            amount=amount,
        )
