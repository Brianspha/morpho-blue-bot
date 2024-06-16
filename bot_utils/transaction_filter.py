import json
import os
import traceback
from web3 import Web3
from web3.types import HexStr

from bot_utils.helpers import store_cache, get_cache
from models.market_positions import Market, MarketPosition


async def get_events(rpc: str, morpho_address: str):
    """
    Fetch and process events from the Morpho contract on the blockchain.

    This function connects to the blockchain using the provided RPC URL and Morpho contract address.
    It retrieves and processes the latest events related to market creation and supply.

    Args:
        rpc (str): The RPC URL for connecting to the blockchain.
        morpho_address (str): The address of the Morpho contract.

    Returns:
        None
    """
    try:
        # Dynamically construct the path to the morpho_abi.json file
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, '../data/morpho_abi.json')

        # Load the ABI from the JSON file
        with open(json_path) as f:
            data = json.load(f)

        # Create web3 instance
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 60}))
        morpho = w3.eth.contract(address=morpho_address, abi=data)

        # Get the latest block
        block = w3.eth.get_block('latest')
        block_number = block.get('number', 'latest')

        # Create a filter for new market creation events public RPC have 5K limit
        event_filter = morpho.events.CreateMarket.create_filter(
            fromBlock=block_number - 300 if isinstance(block_number, int) else 'latest'
        )

        # Retrieve cached market events
        converted_events = await get_cache("markets")
        converted_events = converted_events.get("markets", [])

        # Get new market creation events
        events = event_filter.get_new_entries()

        for event in events:
            market = dict(event.args['marketParams'])  # Create a mutable copy
            market['uniqueKey'] = w3.to_hex(HexStr(event.args['id']))
            market['irmAddress'] = market['irm']
            market['oracleAddress'] = market['oracle']
            market['loanAsset'] = {"address": market['loanToken'], "symbol": "", "decimals": 0}
            market['collateralAsset'] = {"address": market['collateralToken'], "symbol": "", "decimals": 0}
            market['lltv'] = str(market['lltv'])
            market['state'] = None
            market_obj = Market.from_dict(market)

            # Create a filter for supply events
            supply_event_filter = morpho.events.Supply.create_filter(
                fromBlock=block_number - 300 if isinstance(block_number, int) else 'latest',
                argument_filters={'id': market_obj.unique_key}
            )

            # Get new supply events
            supply_events = supply_event_filter.get_new_entries()
            market_positions = []

            for supply in supply_events:
                supply_converted = MarketPosition.from_dict(
                    obj={"market": market_obj.to_dict(), "user": {"address": supply.args["onBehalf"]}}
                ).to_dict()
                market_positions.append(supply_converted)

            # Store the market positions in the cache
            await store_cache(market_obj.unique_key, market_positions)
            converted_events.append(market_obj.to_dict())

        # Store the converted market events in the cache
        await store_cache("markets", converted_events)
    except Exception:
        print("Error in get_events")
        print(traceback.format_exc())
