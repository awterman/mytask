import asyncio
from datetime import datetime, timedelta

from bittensor import Balance
from celery import shared_task

from mytask.common.settings import get_settings
from mytask.services.chutes_service import ChutesService
from mytask.services.datura_service import DaturaService
from mytask.services.tao_service import TaoService, get_tao_service
from mytask.workers.celery import app

settings = get_settings()

def run_async(coro):
    """Helper function to run async code in a synchronous Celery task."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@shared_task(name="analyze_sentiment_and_stake")
def analyze_sentiment_and_stake(netuid: int, hotkey: str):
    """
    Analyze sentiment for a subnet and stake/unstake based on sentiment score.
    
    Args:
        netuid: Network UID for the subnet
        hotkey: Hotkey to stake/unstake from
    """
    async def _run():
        # Default values if not provided
        netuid_to_use = netuid or 18
        hotkey_to_use = hotkey or "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
        
        # Initialize services
        datura_service = DaturaService(settings.datura_api_key)
        chutes_service = ChutesService(settings.chutes_api_key)
        
        # Get TaoService - in the real code, we need to await it
        # But in tests, mocks will be used
        tao_service = await get_tao_service()
        
        # Step 1: Get tweets about the subnet using Datura
        # Calculate date range for search (7 days back)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        tweets = await datura_service.search_twitter(
            query=f"Bittensor netuid {netuid_to_use}",
            sort="Latest",
            start_date=start_date,
            end_date=end_date,
            min_likes=1,
            min_retweets=1,
            count=20
        )
        
        # If no tweets found, return early
        if not tweets:
            return {"status": "no_tweets", "netuid": netuid_to_use, "hotkey": hotkey_to_use}
        
        # Step 2: Analyze sentiment with Chutes
        tweet_texts = [tweet.text for tweet in tweets]
        sentiment_analysis = await chutes_service.analyze_tweet_sentiment(tweet_texts)
        
        # Calculate final sentiment score
        sentiment_score = sentiment_analysis.average_score
        
        # Step 3: Stake or unstake based on sentiment
        stake_amount = abs(sentiment_score) * 0.01  # 0.01 tao * sentiment score
        
        if sentiment_score > 0:
            # Positive sentiment: stake
            amount = Balance.from_tao(stake_amount)
            result = await tao_service.stake(netuid=netuid_to_use, amount=amount)
            action = "stake"
        else:
            # Negative sentiment: unstake
            amount = Balance.from_tao(stake_amount)
            result = await tao_service.unstake(netuid=netuid_to_use, amount=amount)
            action = "unstake"
        
        return {
            "status": "completed",
            "netuid": netuid_to_use,
            "hotkey": hotkey_to_use,
            "sentiment_score": sentiment_score,
            "action": action,
            "amount": stake_amount,
            "tx_result": str(result)
        }
    
    # Run the async function in the sync context
    return run_async(_run()) 