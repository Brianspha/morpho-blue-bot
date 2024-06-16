import traceback
from typing import List, Union, Type

import requests
from eth_account.signers.local import LocalAccount
from eth_typing import HexStr
from web3 import Web3
from web3.contract import Contract

from bot_utils.helpers import get_cache, div_down_wad, store_cache
from models.market_positions import MarketPosition, MarketsPositionResponse
from models.markets import Market


class MarketBehaviour:
    market: Market
    positions: List[MarketPosition]
    url: str
    liquidator_contract: Union[Type[Contract], Contract]
    web3: Web3
    account: LocalAccount

    def __init__(self, market: Market, url: str, web3: Web3,
                 liquidator_contract: Contract,
                 account: LocalAccount):
        """
        @:dev Initialize the MarketBehaviour instance with market data, URL, Web3 instance,
        liquidator contract, multi-call contract, and account.
        Args:
         market: Market data
         url: URL for API requests
         web3: Web3 instance for blockchain interactions
         liquidator_contract: Contract instance for liquidations
         account: LocalAccount instance for transactions
        """
        self.market = market
        self.url = url
        self.web3 = web3
        self.liquidator_contract = liquidator_contract
        self.account = account
        self.positions = []

    async def init(self):
        """
        @:dev Initialize the market positions by fetching them from the API.
        """
        await self.get_positions()
        await self.get_positions_db()
        self.positions = [position for position in self.positions if not position.liquidated]

    async def start_liquidations(self):
        """
        @:dev Initiate the liquidation process for unhealthy positions.

        @:dev This function encodes liquidation calls for each unhealthy position and
        executes them using a multi-call function within the liquidation contract via delegatecall.
        """
        print("Attempting to liquidate {} positions".format(len(self.positions)))
        if len(self.positions) == 0:
            return

        calls = []
        liquidated_positions = []

        for index, position in enumerate(self.positions):
            try:
                if (position.user is None
                        or position.market is None
                        or position.market.loan_asset is None
                        or position.market.collateral_asset is None
                        or position.market.irm_address is None
                        or position.market.lltv is None):
                    continue

                market_param = position.market.to_market_param()
                call = self.liquidator_contract.encodeABI(fn_name='fullLiquidationWithoutCollat',
                                                          args=[market_param,
                                                                position.user.address, True])
                calls.append((self.liquidator_contract.address, call))
            except Exception as e:
                print(f"Error processing position {index} for liquidation: {e}")
                print(traceback.format_exc())
                continue

        try:
            block = self.web3.eth.get_block('latest')
            block_number = block.get('number', 'latest')
            multi_call_tx = self.liquidator_contract.functions.aggregate(calls).transact(
                transaction={
                    "from": self.account.address,
                    "nonce": self.web3.eth.get_transaction_count(self.account.address),
                    "gas": 30000000
                })
            receipt = self.web3.eth.get_transaction_receipt(transaction_hash=multi_call_tx)
            events = self.liquidator_contract.events.LiquidationResults.get_logs(
                fromBlock=block_number - 300 if isinstance(block_number, int) else 'latest')
            print("liquidation transaction status: ", receipt.get('status', 0), " events: ", events)

            for event in events:
                liquidated_user = event['args']['borrower']
                for position in self.positions:
                    if position.user.address == liquidated_user:
                        position.liquidated = True
                        liquidated_positions.append(position.to_dict())

            await store_cache(self.market.unique_key, liquidated_positions)
        except Exception:
            print("Error executing liquidation transactions")
            print(traceback.format_exc())

    async def get_positions(self):
        """
        @:dev Fetch market positions from the API and update the instance's positions
        attribute.

        This function also handles any exceptions that occur during the process and prints traceback
        information for debugging.
        """
        try:
            query = self.__build_market_query()
            variables = {"uniqueKey": self.market.unique_key}
            response = requests.post(url=self.url, json={"query": query, "variables": variables})
            if response.status_code == 200:
                position_data = response.json()
                positions = MarketsPositionResponse.from_dict(position_data).market_positions
                self.positions += positions
                print(f"Found {len(self.positions)} positions on market {self.market.unique_key}")
            else:
                print(f"Error fetching positions: {response.status_code}, {response.text}")
        except Exception:
            print("Error in get_positions")
            print(traceback.format_exc())

    async def get_positions_db(self):
        """
        @:dev Fetch market positions from the the cache/db

        @:dev This function also handles any exceptions that occur during the process and prints traceback
        information for debugging.
        """
        try:
            db_positions = await get_cache(self.market.unique_key)
            db_positions = db_positions.get('data', [])
            positions = [MarketPosition.from_dict(position) for position in db_positions]
            self.positions += positions
        except Exception:
            print("Error in get_positions_db")
            print(traceback.format_exc())

    def get_un_healthy_positions(self):
        """
        @:dev Evaluate all positions to determine if they are unhealthy and should be considered for
        liquidation.
        @:dev A position is said to be unhealthy if its health factor is less than 1 and
        healthy if its health factor greater than 0 This method iterates through the positions,
        checks for the required attributes, and calculates whether each position is healthy or
        not based on the borrow assets and the maximum borrowable amount.
         @:dev A Position deemed unhealthy are retained for potential liquidation.
         @:dev Processing of positions is done in batches of 100 to optimise for contract calls

        Attributes checked:
        - position.market
        - position.market.oracle_address
        - position.borrow_shares
        - position.borrow_assets
        - position.market.state
        - position.collateral

        Finally, the list of positions is filtered to retain only those that are unhealthy.
        """
        if len(self.positions) > 0:
            batch_size = 100
            calls = []
            for index, position in enumerate(self.positions):
                try:
                    if position.market is None or position.market.loan_asset is None or position.market.collateral_asset is None or position.market.irm_address is None:
                        continue
                    market_param = position.market.to_market_param()
                    call = self.liquidator_contract.encodeABI(
                        fn_name='userHealthFactor',
                        args=[
                            market_param,
                            self.web3.to_bytes(hexstr=HexStr(self.market.unique_key)),
                            position.user.address,
                        ]
                    )
                    calls.append((self.liquidator_contract.address, call))
                    if len(calls) >= batch_size:
                        results = self.liquidator_contract.functions.aggregate(calls).call()
                        return_data = results[1]
                        for idx, result in enumerate(return_data):
                            self.positions[
                                index - batch_size + 1 + idx].health_factor = self.web3.to_int(
                                primitive=result)
                        calls = []
                except Exception:
                    print(f"Error processing position")
                    print(traceback.format_exc())
                    continue

            if calls:
                try:
                    results = self.liquidator_contract.functions.aggregate(calls).call()
                    return_data = results[1]
                    for idx, result in enumerate(return_data):
                        self.positions[
                            len(self.positions) - len(calls) + idx].health_factor = div_down_wad(
                            self.web3.to_int(
                                primitive=result))
                except Exception:
                    print(f"Error processing remaining positions")
                    print(traceback.format_exc())
                    if calls:
                        results = self.liquidator_contract.functions.aggregate(calls).call()
                        return_data = results[1]
                        for idx, result in enumerate(return_data):
                            self.positions[
                                len(self.positions) - len(
                                    calls) + idx].health_factor = div_down_wad(self.web3.to_int(
                                primitive=result))
                except Exception as e:
                    print(f"Error in final batch of health checks: {e}")
                    print(traceback.format_exc())

            self.positions = [position for position in self.positions if position.health_factor < 1]
            print("Market {} has {} potential positions to be liquidated".format(
                self.market.unique_key,
                len(self.positions)))

    def __build_market_query(self) -> str:
        """
        Build the GraphQL query string to fetch market positions.

        :return: A formatted GraphQL query string
        """
        query = f"""
        query  {{
          marketPositions(
            first: 1000
            orderBy: SupplyShares
            orderDirection: Desc
            where: {{
              marketUniqueKey_in: ["{self.market.unique_key}"]
            }}
          ) {{
            items {{
              supplyShares
              supplyAssets
              supplyAssetsUsd
              borrowShares
              borrowAssets
              borrowAssetsUsd
              collateral
              collateralUsd
              market {{
                uniqueKey
                lltv
                oracleAddress
                irmAddress
                loanAsset {{
                  address
                  symbol
                }}
                collateralAsset {{
                  address
                  symbol
                }}
                state {{
                  borrowApy
                  borrowAssets
                  borrowAssetsUsd
                  supplyApy
                  supplyAssets
                  supplyAssetsUsd
                  fee
                  utilization
                }}
              }}
              user {{
                address
              }}
            }}
          }}
        }}
        """
        return query

