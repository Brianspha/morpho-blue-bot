// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;
import {ISwap} from "./interfaces/ISwap.sol";

contract Swap is ISwap {
    address public uniswap;
    address public loanToken;
    address public collatToken;
    address public liquidator;
    address public owner;
    error NotAuthorised();
    bytes4 public immutable EXACT_INPUT_SINGLE_SELECTOR = bytes4(0x04e45aaf);
    modifier onlyAuth() {
        if (msg.sender != liquidator || msg.sender != owner) {
            revert NotAuthorised();
        }
        _;
    }
    constructor(address uniswap_, address loanToken_, address collatToken_,address liquidator_) {
        uniswap = uniswap_;
        loanToken = loanToken_;
        collatToken = collatToken_;
        owner = msg.sender;
        liquidator=liquidator_;
    }
    //@inherit doc ISwap
    function swapCollatToLoan(
        uint256 amount
    ) external override onlyAuth returns (uint256 returnedAmount) {}
    //@inherit doc ISwap
    function swapLoanToCollat(
        uint256 amount
    ) external override onlyAuth returns (uint256 returnedAmount) {}
}
