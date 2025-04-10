from bittensor import AsyncSubtensor, wallet


class TaoService:
    def __init__(self, subtensor: AsyncSubtensor, wallet: wallet, netuid: int = 18):
        self.netuid = netuid
        self.subtensor = subtensor
        self.wallet = wallet

    async def get_dividends(self, hotkey: str):
        return await self.subtensor.get_tao_for_subnet(
            netuid=self.netuid, hotkey=hotkey
        )

    async def get_stake(self, hotkey: str):
        return await self.subtensor.get_stake_for_hotkey(
            netuid=self.netuid, hotkey=hotkey
        )

    async def get_balance(self):
        return await self.subtensor.get_balance(self.wallet.hotkey.ss58_address)

    async def stake(self, amount: float):
        return await self.subtensor.add_stake(
            wallet=self.wallet,
            netuid=self.netuid,
            hotkey=self.wallet.hotkey.ss58_address,
            amount=amount,
        )

    async def unstake(self, amount: float):
        return await self.subtensor.unstake(
            wallet=self.wallet,
            netuid=self.netuid,
            hotkey=self.wallet.hotkey.ss58_address,
            amount=amount,
        )
