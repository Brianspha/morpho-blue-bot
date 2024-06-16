from dataclasses import dataclass
from typing import Any, Union, Optional, List, TypeVar, Type, cast, Callable
from enum import Enum

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_none(x: Any) -> Any:
    assert x is None
    return x


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def to_enum(c: Type[EnumT], x: Any) -> Callable[[], Any]:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


@dataclass
class Asset:
    address: str
    symbol: str

    @staticmethod
    def from_dict(obj: Any) -> 'Asset':
        assert isinstance(obj, dict)
        address = from_str(obj.get("address"))
        symbol = from_str(obj.get("symbol"))
        return Asset(address, symbol)

    def to_dict(self) -> dict:
        result: dict = {"address": from_str(self.address), "symbol": from_str(self.symbol),
                        }
        return result


@dataclass
class State:
    borrow_apy: float
    borrow_assets: Union[int, str]
    supply_apy: float
    supply_assets: Union[int, str]
    fee: int
    utilization: float
    borrow_assets_usd: Optional[float] = None
    supply_assets_usd: Optional[float] = None

    @staticmethod
    def from_dict(obj: Any) -> 'State':
        if isinstance(obj, dict):
            borrow_apy = from_float(obj.get("borrowApy"))
            borrow_assets = from_union([from_int, from_str], obj.get("borrowAssets"))
            supply_apy = from_float(obj.get("supplyApy"))
            supply_assets = from_union([from_int, from_str], obj.get("supplyAssets"))
            fee = from_int(obj.get("fee"))
            utilization = from_float(obj.get("utilization"))
            borrow_assets_usd = from_union([from_float, from_none], obj.get("borrowAssetsUsd"))
            supply_assets_usd = from_union([from_float, from_none], obj.get("supplyAssetsUsd"))
            return State(borrow_apy, borrow_assets, supply_apy, supply_assets, fee, utilization,
                         borrow_assets_usd, supply_assets_usd)

    def to_dict(self) -> dict:
        result: dict = {"borrowApy": to_float(self.borrow_apy),
                        "borrowAssets": from_union([from_int, from_str], self.borrow_assets),
                        "supplyApy": to_float(self.supply_apy),
                        "supplyAssets": from_union([from_int, from_str], self.supply_assets),
                        "fee": from_int(self.fee), "utilization": to_float(self.utilization),
                        "borrowAssetsUsd": from_union([to_float, from_none],
                                                      self.borrow_assets_usd),
                        "supplyAssetsUsd": from_union([to_float, from_none],
                                                      self.supply_assets_usd)}
        return result


@dataclass
class Market:
    unique_key: str
    lltv: Union[int, str]
    oracle_address: str
    irm_address: str
    loan_asset: Asset
    state: State
    collateral_asset: Optional[Asset] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Market':
        assert isinstance(obj, dict)
        unique_key = from_str(obj.get("uniqueKey"))
        lltv = obj.get("lltv")
        oracle_address = from_str(obj.get("oracleAddress"))
        irm_address = obj.get("irmAddress")
        loan_asset = Asset.from_dict(obj.get("loanAsset"))
        state = State.from_dict(obj.get("state"))
        collateral_asset = from_union([Asset.from_dict, from_none], obj.get("collateralAsset"))
        return Market(unique_key, lltv, oracle_address, irm_address, loan_asset, state,
                      collateral_asset)

    def to_dict(self) -> dict:
        result: dict = {"uniqueKey": from_str(self.unique_key),
                        "lltv": from_union([from_int, from_str], self.lltv),
                        "oracleAddress": from_str(self.oracle_address),
                        "irmAddress": from_str( self.irm_address),
                        "loanAsset": to_class(Asset, self.loan_asset),
                        "state": to_class(State, self.state),
                        "collateralAsset": from_union([lambda x: to_class(Asset, x), from_none],
                                                      self.collateral_asset)}
        return result


@dataclass
class Markets:
    items: List[Market]

    @staticmethod
    def from_dict(obj: Any) -> 'Markets':
        assert isinstance(obj, dict)
        items = from_list(Market.from_dict, obj.get("items"))
        return Markets(items)

    def to_dict(self) -> dict:
        result: dict = {"items": from_list(lambda x: to_class(Market, x), self.items)}
        return result


@dataclass
class Data:
    markets: List[Market]

    @staticmethod
    def from_dict(obj: Any) -> 'Data':
        assert isinstance(obj, dict)
        markets = Markets.from_dict(obj.get("markets")).items
        return Data(markets)

    def to_dict(self) -> dict:
        result: dict = {"markets": to_class(Markets, self.markets)}
        return result


@dataclass
class MarketsResponse:
    markets: List[Market]

    @staticmethod
    def from_dict(obj: Any) -> 'MarketsResponse':
        assert isinstance(obj, dict)
        data = Data.from_dict(obj.get("data")).markets
        return MarketsResponse(data)

    def to_dict(self) -> dict:
        result: dict = {"markets": to_class(Data, self.markets)}
        return result


def markets_response_from_dict(s: Any) -> MarketsResponse:
    return MarketsResponse.from_dict(s)


def markets_response_to_dict(x: MarketsResponse) -> Any:
    return to_class(MarketsResponse, x)
