// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;
import {IOracle} from "./interfaces/IOracle.sol";
contract MockOracle is IOracle {
    uint256 public internalPrice;
    constructor(uint256 price_) {
        internalPrice = price_;
    }
    //@inherit doc IOracle
    function price() external view override returns (uint256) {
        return internalPrice;
    }
    function updatePrice() public {
        internalPrice /= 2;
    }
}
