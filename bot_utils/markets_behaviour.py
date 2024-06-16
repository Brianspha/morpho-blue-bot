import json
import os
import string
import sys
import traceback
from typing import List

import requests
from eth_account import Account
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from bot_utils.helpers import get_cache
from bot_utils.market_behaviour import MarketBehaviour
from models.markets import MarketsResponse, Market
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MarketsBehaviour:
    markets: List[MarketBehaviour]
    url: str
    liquidator_address: str
    multi_call_address: str
    private_key: str
    rpc: str
    markets: List[str]

    def __init__(self, url: str, liquidator_address: str, private_key: str, rpc: str, markets: List[str]):
        """
        @:dev Initializes the MarketsBehaviour class.

        Args:
            url (str): The GraphQL API endpoint URL.
            liquidator_address (str): The address of the liquidator contract.
            private_key (str): The private key for signing transactions.
            rpc (str): The RPC URL for connecting to the blockchain.
            markets (List[str]): List of market addresses to be monitored.
        """
        self.url = url
        self.liquidator_address = liquidator_address
        self.private_key = private_key
        self.rpc = rpc
        self.markets = markets

    async def init(self):
        """
        @:dev Initializes the MarketsBehaviour by fetching and processing market data.
        """
        await self.__get_markets()

    async def __get_markets(self):
        """
        @:dev Fetches market data from the GraphQL endpoint and initializes market behaviours.
        """
        query = self.__build_markets_query()
        print("Fetching markets from GraphQL")
        try:
            response = requests.post(url=self.url, json={"query": query})
            if response.status_code == 200:
                market_data = response.json()
                print(f"Done fetching markets from GraphQL, found any: {len(market_data.get('data', {}).get('items', [])) > 0}")
                markets = MarketsResponse.from_dict(market_data).markets
                new_markets = [market for market in markets if market.collateral_asset is not None and market.collateral_asset.address in self.markets]
                w3 = Web3(Web3.HTTPProvider(self.rpc, request_kwargs={'timeout': 60}))
                w3.strict_bytes_type_checking = False
                account = Account.from_key(self.private_key)
                w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
                script_dir = os.path.dirname(__file__)
                json_path = os.path.join(script_dir, '../out/Liquidator.sol/Liquidator.json')
                with open(json_path) as f:
                    data = json.load(f)
                    liquidator_contract = w3.eth.contract(address=self.liquidator_address, abi=data['abi'])
                    self.account = account
                    self.markets = [
                        MarketBehaviour(market=market, url=self.url, liquidator_contract=liquidator_contract, web3=w3, account=account)
                        for market in new_markets
                    ]
                    db_markets = await get_cache("markets")
                    db_markets = db_markets.get('data', [])
                    if db_markets:
                        dev_markets = [
                            MarketBehaviour(market=Market.from_dict(market), url=self.url, liquidator_contract=liquidator_contract, web3=w3, account=account)
                            for market in db_markets
                        ]
                        self.markets += dev_markets
        except Exception:
            print("Error executing liquidation transactions")
            print(traceback.format_exc())

    @staticmethod
    def __build_markets_query() -> str:
        """
        @:dev Builds the GraphQL query to fetch market data.

        Returns:
            str: The GraphQL query string.
        """
        query = """ 
            query {
              markets(first: 1000) {
                items {
                  uniqueKey
                  lltv
                  oracleAddress
                  irmAddress
                  loanAsset {
                    address
                    symbol
                    decimals
                  }
                  collateralAsset {
                    address
                    symbol
                    decimals
                  }
                  state {
                    borrowApy
                    borrowAssets
                    borrowAssetsUsd
                    supplyApy
                    supplyAssets
                    supplyAssetsUsd
                    fee
                    utilization
                  }
                }
              }
            } 
            """
        return query
