from enum import Enum
from dataclasses import dataclass
from typing import Any, Union, List, TypeVar, Type, cast, Callable, Mapping

from models.markets import State

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def to_enum(c: Type[EnumT], x: Any) -> Callable[[], Any]:
    assert isinstance(x, c)
    return x.value


def from_str(x: Any) -> str:
    if isinstance(x, str):
        return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_int(x: Any) -> int:
    if isinstance(x, int) and not isinstance(x, bool):
        return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_float(x: Any) -> float:
    if isinstance(x, (float, int)) and not isinstance(x, bool):
        return float(x)


def to_float(x: Any) -> float:
    if isinstance(x, (int, float)):
        return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


@dataclass
class Asset:
    address: str
    symbol: str

    @staticmethod
    def from_dict(obj: Any) -> 'Asset':
        if isinstance(obj, dict):
            address = from_str(obj.get("address"))
            symbol = from_str(obj.get("symbol"))
            return Asset(address, symbol)

    def to_dict(self) -> dict:
        result: dict = {"address": from_str(self.address), "symbol": from_str(self.symbol)}
        return result


@dataclass
class Market:
    unique_key: str
    lltv: str
    oracle_address: str
    irm_address: str
    loan_asset: Asset
    collateral_asset: Asset
    state: State

    @staticmethod
    def from_dict(obj: Any) -> 'Market':
        if isinstance(obj, dict):
            unique_key = from_str(obj.get("uniqueKey"))
            lltv = from_str(obj.get("lltv"))
            oracle_address = from_str(obj.get("oracleAddress"))
            irm_address = from_str(obj.get("irmAddress"))
            loan_asset = Asset.from_dict(obj.get("loanAsset"))
            collateral_asset = Asset.from_dict(obj.get("collateralAsset"))
            state = State.from_dict(obj.get("state"))
            return Market(unique_key, lltv, oracle_address, irm_address, loan_asset,
                          collateral_asset, state=state)

    def to_dict(self) -> dict:
        result: dict = {"uniqueKey": from_str(self.unique_key), "lltv": from_str(self.lltv),
                        "oracleAddress": from_str(self.oracle_address),
                        "irmAddress": from_str(self.irm_address),
                        "loanAsset": to_class(Asset, self.loan_asset),
                        "collateralAsset": to_class(Asset, self.collateral_asset)}
        return result

    def to_market_param(self):
        result = (from_str(self.loan_asset.address),
                  from_str(self.collateral_asset.address),
                  from_str(self.oracle_address),
                  from_str(self.irm_address),
                  int(self.lltv),
                  )
        return result


@dataclass
class User:
    address: str

    @staticmethod
    def from_dict(obj: Any) -> 'User':
        assert isinstance(obj, dict)
        address = from_str(obj.get("address"))
        return User(address)

    def to_dict(self) -> dict:
        result: dict = {"address": from_str(self.address)}
        return result


@dataclass
class MarketPosition:
    supply_shares: Union[int, str]
    supply_assets: Union[int, str]
    supply_assets_usd: float
    borrow_shares: Union[int, str]
    borrow_assets: Union[int, str]
    borrow_assets_usd: float
    collateral: Union[int, str]
    collateral_usd: float
    market: Market
    user: User
    liquidated: bool
    health_factor: float
    healthy: bool

    @staticmethod
    def from_dict(obj: Any) -> 'MarketPosition':
        if isinstance(obj, Mapping):
            supply_shares = from_union([from_int, from_str], obj.get("supplyShares"))
            supply_assets = from_union([from_int, from_str], obj.get("supplyAssets"))
            supply_assets_usd = from_float(obj.get("supplyAssetsUsd"))
            borrow_shares = from_union([from_int, from_str], obj.get("borrowShares"))
            borrow_assets = from_union([from_int, from_str], obj.get("borrowAssets"))
            borrow_assets_usd = from_float(obj.get("borrowAssetsUsd"))
            collateral = from_union([from_int, from_str], obj.get("collateral"))
            collateral_usd = from_float(obj.get("collateralUsd"))
            market = Market.from_dict(obj.get("market"))
            user = User.from_dict(obj.get("user"))
            liquidated = obj.get("liquidated", False)
            healthy = obj.get("healthy", False)
            health_factor = from_float(obj.get("health_factor", 10000.0))
            market_position = MarketPosition(supply_shares=supply_shares,
                                             supply_assets=supply_assets,
                                             supply_assets_usd=supply_assets_usd,
                                             borrow_shares=borrow_shares,
                                             borrow_assets=borrow_assets,
                                             borrow_assets_usd=borrow_assets_usd,
                                             collateral=collateral, collateral_usd=collateral_usd,
                                             market=market,
                                             user=user, liquidated=liquidated,
                                             health_factor=health_factor, healthy=healthy)
            return market_position

    def to_dict(self) -> dict:
        result: dict = {"supplyShares": from_union([from_int, from_str], self.supply_shares),
                        "supplyAssets": from_union([from_int, from_str], self.supply_assets),
                        "supplyAssetsUsd": to_float(self.supply_assets_usd),
                        "borrowShares": from_union([from_int, from_str], self.borrow_shares),
                        "borrowAssets": from_union([from_int, from_str], self.borrow_assets),
                        "borrowAssetsUsd": to_float(self.borrow_assets_usd),
                        "collateral": from_union([from_int, from_str], self.collateral),
                        "collateralUsd": to_float(self.collateral_usd),
                        "healthy": self.healthy,
                        "health_factor": from_union([from_int, from_str],self.health_factor),
                        "market": to_class(Market, self.market), "user": to_class(User, self.user)}
        return result


@dataclass
class MarketPositions:
    items: List[MarketPosition]

    @staticmethod
    def from_dict(obj: Any) -> 'MarketPositions':
        assert isinstance(obj, dict)
        items = from_list(MarketPosition.from_dict, obj.get("items"))
        return MarketPositions(items)

    def to_dict(self) -> dict:
        result: dict = {"items": from_list(lambda x: to_class(MarketPosition, x), self.items)}
        return result


@dataclass
class Data:
    market_positions: MarketPositions

    @staticmethod
    def from_dict(obj: Any) -> 'Data':
        assert isinstance(obj, dict)
        market_positions = MarketPositions.from_dict(obj.get("marketPositions"))
        return Data(market_positions)

    def to_dict(self) -> dict:
        result: dict = {"marketPositions": to_class(MarketPositions, self.market_positions)}
        return result


@dataclass
class MarketsPositionResponse:
    market_positions: List[MarketPosition]

    @staticmethod
    def from_dict(obj: Any) -> 'MarketsPositionResponse':
        assert isinstance(obj, dict)
        data = Data.from_dict(obj.get("data"))
        return MarketsPositionResponse(data.market_positions.items)

    def to_dict(self) -> dict:
        result: dict = {"data": to_class(Data, self.market_positions)}
        return result


def markets_position_response_from_dict(s: Any) -> MarketsPositionResponse:
    return MarketsPositionResponse.from_dict(s)


def markets_position_response_to_dict(x: MarketsPositionResponse) -> Any:
    return to_class(MarketsPositionResponse, x)
