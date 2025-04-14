from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends

from mytask.common.logger import get_logger
from mytask.models.tao import GetTaoDividendsResponse, TaoDividendResponseItem
from mytask.services.tao_service import TaoService, get_tao_service
from mytask.workers.tasks import analyze_sentiment_and_stake

router = APIRouter()
logger = get_logger()

# Function to run the sentiment analysis task
def run_sentiment_task(netuid: int, hotkey: str):
    # This function will be called by FastAPI's background task
    # It then calls our Celery task
    analyze_sentiment_and_stake(netuid, hotkey)


@router.get("/tao_dividends")
async def get_tao_dividends(
    netuid: int | None = None,
    hotkey: str | None = None,
    trade: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    tao_service: TaoService = Depends(get_tao_service),
) -> GetTaoDividendsResponse:
    logger.info(f"Getting TAO dividends for {netuid} and {hotkey}")

    # Get dividends data
    dividends, is_cached = await tao_service.get_cached_dividends(netuid, hotkey)

    # Set default values if they're None
    default_netuid = 18
    default_hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
    
    netuid_to_use = netuid or default_netuid
    hotkey_to_use = hotkey or default_hotkey
    
    # If trade flag is set, trigger sentiment analysis and stake/unstake
    if trade:
        # Add the task to FastAPI background tasks
        # This will run the function after the response is sent
        background_tasks.add_task(run_sentiment_task, netuid_to_use, hotkey_to_use)
    
    # Create response objects
    dividend_base_list = [
        TaoDividendResponseItem(
            netuid=dividend.netuid,
            hotkey=dividend.hotkey,
            dividend=dividend.dividends,
            cached=is_cached,
            stake_tx_triggered=trade,
        )
        for dividend in dividends
    ]

    return GetTaoDividendsResponse(dividends=dividend_base_list)