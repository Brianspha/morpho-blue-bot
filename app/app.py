import asyncio
import os
import sys
import traceback

import aioredis
from dotenv import load_dotenv
# Add the directory containing bot_utils to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot_utils.helpers import parse_env_array
from bot_utils.market_behaviour import MarketBehaviour
from bot_utils.markets_behaviour import MarketsBehaviour
from bot_utils.transaction_filter import get_events

# Load environment variables from the .env file
load_dotenv("../.env")

# Fetch environment variables
graphql_api_url = os.environ.get("GRAPHQL_API_ENDPOINT")
private_key = os.environ.get("PRIVATE_KEY")
liquidator_address = os.environ.get("LIQUIDATOR_ADDRESS")
rpc = os.environ.get("RPC_URL")
redis_instance = aioredis.from_url(url=os.environ.get("REDIS_HOST"))
markets = parse_env_array(env_var_name="MARKETS")
development = (os.getenv('DEVELOPMENT', 'False') == 'True')
morpho_address = os.environ.get("MORPHO_ADDRESS")


async def main():
    """
    Main entry point for running the periodic events and tasks.
    Retries the main function upon encountering an exception.
    """
    try:
        await run_periodic_tasks(interval_minutes=10)
    except Exception as error:
        print(f"Error running task: {error}")
        asyncio.run(main())  # Retry the main function


async def perform_task(index: int, market: MarketBehaviour):
    """
    Perform tasks for a given market.

    Args:
        index (int): The index of the market.
        market (MarketBehaviour): The market behaviour instance.

    Returns:
        str: The completion message with task data.
    """
    try:
        print(f"Performing task for market {index}: {market.market.unique_key}")
        await market.init()
        market.get_un_healthy_positions()
        await market.start_liquidations()
        return f"Task {index} completed with data: {market.positions}"
    except Exception:
        print(f"Task {index} failed with exception: {traceback.format_exc()}")


async def run_periodic_tasks(interval_minutes: int):
    """
    Run periodic tasks at specified intervals.

    Args:
        interval_minutes (int): Interval in minutes between task executions.
    """
    await get_events(rpc=rpc, morpho_address=morpho_address)
    markets_behaviour = MarketsBehaviour(
        url=graphql_api_url, private_key=private_key,
        liquidator_address=liquidator_address, rpc=rpc, markets=markets
    )
    await markets_behaviour.init()
    while True:
        tasks = [perform_task(index, market) for index, market in enumerate(markets_behaviour.markets)]
        await asyncio.gather(*tasks)
        await asyncio.sleep(interval_minutes * 60)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
