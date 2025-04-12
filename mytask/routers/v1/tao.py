from fastapi import APIRouter, Depends

from mytask.models.tao import GetTaoDividendsResponse, TaoDividendBase
from mytask.services.tao_service import TaoService, get_tao_service

router = APIRouter()


@router.get("/tao_dividends")
async def get_tao_dividends(
    netuid: int | None = None,
    hotkey: str | None = None,
    trade: bool = False,
    tao_service: TaoService = Depends(get_tao_service),
) -> GetTaoDividendsResponse:
    dividends, is_cached = await tao_service.get_cached_dividends(netuid, hotkey)

    dividend_base_list = [
        TaoDividendBase(
            netuid=dividend.netuid,
            hotkey=dividend.hotkey,
            dividend=dividend.dividends,
            cached=is_cached,
            stake_tx_triggered=False,
        )
        for dividend in dividends
    ]

    return GetTaoDividendsResponse(dividends=dividend_base_list)