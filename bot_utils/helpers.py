import json
import os
import sys
from typing import List

import aioredis
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

redis_host = os.environ.get("REDIS_HOST")
if not redis_host:
    raise ValueError("REDIS_HOST environment variable is not set. Please check your .env file.")

print("REDIS_HOST: ", redis_host)

# Create an instance of the Redis client
redis_instance = aioredis.from_url(url=redis_host)


async def get_cache(key: str) -> dict:
    """
    @:dev Retrieve cached data from Redis.

    Args:
        key (str): The key for the cached data.

    Returns:
        dict: A dictionary containing a success flag and the cached data.
    """
    data = await redis_instance.get(key)
    if data is None:
        return {
            "success": False,
            "data": []
        }
    else:
        return {
            "success": True,
            "data": json.loads(data)
        }


async def store_cache(key: str, data) -> bool:
    """
    @:dev Store data in the Redis cache.

    Args:
        key (str): The key for the cached data.
        data: The data to cache.

    Returns:
        bool: True if the data was successfully stored, False otherwise.
    """
    try:
        await redis_instance.set(key, json.dumps(data))
        return True
    except Exception as e:
        print(f"Error storing cache with key: {key}, data: {data}, error: {e}")
        return False


def unique_items(items: list, key: str) -> list:
    """
    @:dev Get a list of unique items based on a specified key.

    Args:
        items (list): The list of items.
        key (str): The key to determine uniqueness.

    Returns:
        list: A list of unique items.
    """
    seen = set()
    unique_list = []
    for item in items:
        if item[key] not in seen:
            unique_list.append(item)
            seen.add(item[key])
    return unique_list


def pow10(exponent: int) -> int:
    """
    @:dev Compute 10 raised to the power of the given exponent.

    Args:
        exponent (int): The exponent.

    Returns:
        int: 10 raised to the power of the exponent.
    """
    return 10 ** exponent


def mul_div_up(x: float, y: float, z: float) -> float:
    """
    @:dev Perform multiplication and division with rounding up.

    Args:
        x (float): The numerator's multiplier.
        y (float): The numerator's multiplicand.
        z (float): The denominator.

    Returns:
        float: The result of the operation.
    """
    return (x * y + z - 1) // z


def div_down_wad(x: float) -> float:
    """
    @:dev Divide by WAD with rounding down.

    Args:
        x (float): The value to divide.

    Returns:
        float: The result of the division.
    """
    return x / WAD


def mul_div_down(x: float, y: float, z: float) -> float:
    """
    @:dev Perform multiplication and division with rounding down.

    Args:
        x (float): The numerator's multiplier.
        y (float): The numerator's multiplicand.
        z (float): The denominator.

    Returns:
        float: The result of the operation.
    """
    return (x * y) // z


def w_mul_down(x: float, y: float) -> float:
    """
    @:dev Perform WAD multiplication with rounding down.

    Args:
        x (float): The first multiplier.
        y (float): The second multiplier.

    Returns:
        float: The result of the multiplication.
    """
    return mul_div_down(x, y, WAD)


def to_assets_up(shares: float, total_assets: float, total_shares: float) -> float:
    """
    @:dev Convert shares to assets with rounding up.

    Args:
        shares (float): The number of shares.
        total_assets (float): The total assets.
        total_shares (float): The total shares.

    Returns:
        float: The equivalent assets.
    """
    return mul_div_up(shares, total_assets + VIRTUAL_ASSETS, total_shares + VIRTUAL_SHARES)


def calculate_max_borrow(position_collateral: float, collateral_price: float,
                         market_params_lltv: float) -> float:
    """
    @:dev Calculate the maximum borrowable amount.

    Args:
        position_collateral (float): The collateral amount.
        collateral_price (float): The price of the collateral.
        market_params_lltv (float): The loan-to-value ratio.

    Returns:
        float: The maximum borrowable amount.
    """
    max_borrow = w_mul_down(
        mul_div_down(position_collateral, collateral_price, ORACLE_PRICE_SCALE),
        market_params_lltv
    )
    return max_borrow


def is_position_healthy(position_collateral: float, collateral_price: float,
                        market_params_lltv: float, borrow_assets_user: int) -> bool:
    """
    @:dev Determine if a position is healthy.

    Args:
        position_collateral (float): The collateral amount.
        collateral_price (float): The price of the collateral.
        market_params_lltv (float): The loan-to-value ratio.
        borrow_assets_user (int): The borrowed assets by the user.

    Returns:
        bool: True if the position is healthy, False otherwise.
    """
    max_borrow = calculate_max_borrow(position_collateral, collateral_price, market_params_lltv)
    return max_borrow >= borrow_assets_user


def parse_env_array(env_var_name: str, separator: str = ',') -> List[str]:
    """
    @:dev Parse an environment variable into a list of strings.

    Args:
        env_var_name (str): The name of the environment variable.
        separator (str): The separator used to split the variable's value.

    Returns:
        List[str]: The parsed list of strings.

    Raises:
        ValueError: If the environment variable is not found.
    """
    env_var_value = os.getenv(env_var_name)
    if env_var_value is None:
        raise ValueError(f"Environment variable {env_var_name} not found")
    return env_var_value.split(separator)


# Constants
ORACLE_PRICE_SCALE = pow10(36)
WAD = pow10(18)
SECONDS_PER_YEAR = 3600 * 24 * 365
VIRTUAL_ASSETS = 1
VIRTUAL_SHARES = 10 ** 6
MAX_UINT256 = int("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", 16)
