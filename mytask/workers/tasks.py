import asyncio
from datetime import datetime, timedelta

from bittensor import Balance
from celery import shared_task

from mytask.common.logger import get_logger
from mytask.common.settings import get_settings
from mytask.services.chutes_service import ChutesService
from mytask.services.datura_service import DaturaService
from mytask.services.tao_service import get_tao_service
from mytask.workers.celery import app

logger = get_logger()
settings = get_settings()


def run_async(coro):
    """Helper function to run async code in a synchronous Celery task."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Create a new event loop if one doesn't exist in the current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        # Close the loop if we created a new one
        if loop != asyncio.get_event_loop_policy().get_event_loop():
            loop.close()


@app.task
def analyze_sentiment_and_stake(netuid: int, hotkey: str):
    """
    Analyze sentiment for a subnet and stake/unstake based on sentiment score.

    Args:
        netuid: Network UID for the subnet
        hotkey: Hotkey to stake/unstake from
    """
    logger.info(
        f"Starting analyze_sentiment_and_stake task for netuid={netuid}, hotkey={hotkey}"
    )

    async def _run():
        # Default values if not provided
        netuid_to_use = netuid or 18
        hotkey_to_use = hotkey or "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"

        logger.debug(f"Using netuid={netuid_to_use}, hotkey={hotkey_to_use}")

        # Initialize services
        logger.info("Initializing services")
        datura_service = DaturaService(settings.datura_api_key)
        chutes_service = ChutesService(settings.chutes_api_key)

        # Get TaoService - in the real code, we need to await it
        # But in tests, mocks will be used
        tao_service = await get_tao_service()

        # Step 1: Get tweets about the subnet using Datura
        # Calculate date range for search (7 days back)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        logger.info(
            f"Searching tweets from {start_date} to {end_date} for subnet {netuid_to_use}"
        )
        tweets = await datura_service.search_twitter(
            query=f"Bittensor netuid {netuid_to_use}",
            sort="Latest",
            start_date=start_date,
            end_date=end_date,
            min_likes=1,
            min_retweets=1,
            count=3,
        )

        # If no tweets found, return early
        if not tweets:
            logger.warning(f"No tweets found for netuid {netuid_to_use}")
            return {
                "status": "no_tweets",
                "netuid": netuid_to_use,
                "hotkey": hotkey_to_use,
            }
        if len(tweets) > 3:
            logger.warning(f"Found {len(tweets)} tweets for analysis, truncating to 3")
            tweets = tweets[:3]

        logger.info(f"Found {len(tweets)} tweets for analysis")

        # Step 2: Analyze sentiment with Chutes
        logger.info("Analyzing tweet sentiment")
        tweet_texts = [tweet.text for tweet in tweets]
        sentiment_score = await chutes_service.score_tweet_sentiment(tweet_texts)
        logger.info(f"Sentiment score: {sentiment_score}")

        # Step 3: Stake or unstake based on sentiment
        stake_amount = abs(sentiment_score) * 0.01  # 0.01 tao * sentiment score
        if stake_amount == 0:
            logger.warning("No stake amount, skipping transaction")
            return {
                "status": "no_stake_amount",
                "netuid": netuid_to_use,
                "hotkey": hotkey_to_use,
            }

        if sentiment_score > 0:
            # Positive sentiment: stake
            amount = Balance.from_tao(stake_amount)
            logger.info(
                f"Positive sentiment detected. Staking {stake_amount} TAO to netuid {netuid_to_use}"
            )
            result = await tao_service.stake(netuid=netuid_to_use, amount=amount)
            action = "stake"
        else:
            # Negative sentiment: unstake
            amount = Balance.from_tao(stake_amount)
            logger.info(
                f"Negative sentiment detected. Unstaking {stake_amount} TAO from netuid {netuid_to_use}"
            )
            result = await tao_service.unstake(netuid=netuid_to_use, amount=amount)
            action = "unstake"

        logger.info(f"Transaction completed: {action} action with result: {result}")

        return {
            "status": "completed",
            "netuid": netuid_to_use,
            "hotkey": hotkey_to_use,
            "sentiment_score": sentiment_score,
            "action": action,
            "amount": stake_amount,
            "tx_result": str(result),
        }

    try:
        # Run the async function in the sync context
        result = run_async(_run())
        logger.info(f"Task completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(
            f"Error in analyze_sentiment_and_stake task: {str(e)}", exc_info=True
        )
        raise
