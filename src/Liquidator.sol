// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {IIrm} from "@morpho-blue/interfaces/IIrm.sol";
import {Id, IMorpho, MarketParams, Market, Position} from "@morpho-blue/interfaces/IMorpho.sol";
import {MathLib} from "@morpho-blue/libraries/MathLib.sol";
import {MorphoBalancesLib} from "@morpho-blue/libraries/periphery/MorphoBalancesLib.sol";
import {MorphoStorageLib} from "@morpho-blue/libraries/periphery/MorphoStorageLib.sol";
import {IOracle} from "./interfaces/IOracle.sol";
import {ISwap} from "./interfaces/ISwap.sol";
import {IMorphoLiquidateCallback} from "@morpho-blue/interfaces/IMorphoCallbacks.sol";
import {MorphoLib} from "@morpho-blue/libraries/periphery/MorphoLib.sol";
import {MarketParamsLib} from "@morpho-blue/libraries/MarketParamsLib.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {SafeERC20, IERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Multicall3} from "./MultiCall.sol";
import "@morpho-blue/libraries/ConstantsLib.sol";

/// @title Morpho Blue Snippets
/// @notice The Morpho Blue Snippets contract.
/// @dev This contract provides functionalities for liquidating positions in the Morpho Blue protocol.
contract Liquidator is Ownable, Multicall3 {
    using MathLib for uint256;
    using MathLib for uint128;
    using MorphoBalancesLib for IMorpho;
    using MorphoLib for IMorpho;
    using MarketParamsLib for MarketParams;
    using MorphoLib for uint256;
    using SafeERC20 for IERC20;

    IMorpho public immutable morpho;
    ISwap public immutable swapper;

    /// @dev Struct for liquidation callback data.
    struct LiquidateData {
        address collateralToken;
    }

    /// @notice Event emitted after a liquidation process.
    /// @param seizedAssets The amount of assets seized.
    /// @param balance The balance after liquidation.
    /// @param loanToken The address of the loan token.
    /// @param repaidAssets The amount of assets repaid.
    /// @param borrower The user whose position was liquidated
    event LiquidationResults(
        uint256 indexed seizedAssets,
        uint256 indexed balance,
        address loanToken,
        uint256 repaidAssets,
        address indexed borrower
    );
    event Liqudated(LiquidateData indexed data);
    /// @dev Error for insufficient ether balance.
    error InsufficientEtherBalance();

    /// @dev Modifier to restrict access to only the Morpho contract.
    modifier onlyMorpho() {
        require(
            msg.sender == address(morpho),
            "msg.sender should be Morpho Blue"
        );
        _;
    }
    /// @notice Constructor to initialize the Liquidator contract.
    /// @param morphoAddress The address of the Morpho protocol.
    /// @param swapperAddress The address of the swapper contract.
    constructor(
        address morphoAddress,
        address swapperAddress
    ) Ownable(msg.sender) {
        morpho = IMorpho(morphoAddress);
        swapper = ISwap(swapperAddress);
    }

    /// @notice Calculates the health factor of a user in a specific market.
    /// @param marketParams The parameters of the market.
    /// @param id The identifier of the market.
    /// @param user The address of the user whose health factor is being calculated.
    /// @return healthFactor The calculated health factor.
    function userHealthFactor(
        MarketParams memory marketParams,
        Id id,
        address user
    ) public view returns (uint256 healthFactor) {
        uint256 collateralPrice = IOracle(marketParams.oracle).price();
        Position memory position = morpho.position(id, user);
        uint256 borrowed = morpho.expectedBorrowAssets(marketParams, user);
        uint256 max = position
            .collateral
            .mulDivDown(collateralPrice, ORACLE_PRICE_SCALE)
            .wMulDown(marketParams.lltv);

        if (borrowed == 0) return type(uint256).max;
        healthFactor = max.wDivDown(borrowed);
    }
    /// @notice Calculates the total borrow balance of a given user in a specific market.
    /// @param marketParams The parameters of the market.
    /// @param user The address of the user whose borrow balance is being calculated.
    /// @return totalBorrowAssets The calculated total borrow balance.
    function borrowAssetsUser(
        MarketParams memory marketParams,
        address user
    ) public view returns (uint256 totalBorrowAssets) {
        totalBorrowAssets = morpho.expectedBorrowAssets(marketParams, user);
    }
    /// @notice Calculates the total supply of assets in a specific market.
    /// @param marketParams The parameters of the market.
    /// @return totalSupplyAssets The calculated total supply of assets.
    function marketTotalSupply(
        MarketParams memory marketParams
    ) public view returns (uint256 totalSupplyAssets) {
        totalSupplyAssets = morpho.expectedTotalSupplyAssets(marketParams);
    }
    /// @notice Calculates the total borrow of assets in a specific market.
    /// @param marketParams The parameters of the market.
    /// @return totalBorrowAssets The calculated total borrow of assets.
    function marketTotalBorrow(
        MarketParams memory marketParams
    ) public view returns (uint256 totalBorrowAssets) {
        totalBorrowAssets = morpho.expectedTotalBorrowAssets(marketParams);
    }
    // ---- MANAGING FUNCTIONS ----
    /// @notice Callback function for Morpho liquidations.
    /// @param data Encoded liquidation data.
    function onMorphoLiquidate(
        uint256,
        bytes calldata data
    ) external onlyMorpho {
        emit Liqudated(abi.decode(data, (LiquidateData)));
    }

    /// @notice Withdraws tokens to the owner.
    /// @param loanToken The address of the loan token.
    function withdrawToken(address loanToken) public onlyOwner {
        IERC20(loanToken).safeTransfer(
            msg.sender,
            IERC20(loanToken).balanceOf(address(this))
        );
    }

    /// @notice Withdraws ether to the owner.
    function withdrawEther() public onlyOwner {
        (bool sent, ) = owner().call{value: address(this).balance}("");
        if (!sent) {
            revert InsufficientEtherBalance();
        }
    }

    /// @notice Returns the token balance of the owner.
    /// @param loanToken The address of the loan token.
    /// @return The token balance of the owner.
    function tokenBalanceOf(address loanToken) public view returns (uint256) {
        return IERC20(loanToken).balanceOf(owner());
    }

    /// @notice Returns the ether balance of the contract.
    /// @return The ether balance of the contract.
    function etherBalanceOf() public view returns (uint256) {
        return address(this).balance;
    }
    /// @notice Calculates the total supply balance of a given user in a specific market.
    /// @param marketParams The parameters of the market.
    /// @param user The address of the user whose supply balance is being calculated.
    /// @return totalSupplyAssets The calculated total supply balance.
    function supplyAssetsUser(
        MarketParams memory marketParams,
        address user
    ) public view returns (uint256 totalSupplyAssets) {
        totalSupplyAssets = morpho.expectedSupplyAssets(marketParams, user);
    }
    /// @notice Fully liquidates the borrow position of `borrower` on the given `marketParams` market of Morpho Blue and
    /// sends the profit of the liquidation to the sender.
    /// @dev Thanks to callbacks, the sender doesn't need to hold any tokens to perform this operation.
    /// @param marketParams The market to perform the liquidation on.
    /// @param borrower The owner of the liquidable borrow position.
    /// @param seizeFullCollat Pass `True` to seize all the collateral of `borrower`. Pass `False` to repay all of the
    /// `borrower`'s debt.
    function fullLiquidationWithoutCollat(
        MarketParams calldata marketParams,
        address borrower,
        bool seizeFullCollat
    ) public onlyOwner returns (bool success) {
        Id id = marketParams.id();

        uint256 seizedCollateral;
        uint256 repaidShares;

        if (seizeFullCollat) seizedCollateral = morpho.collateral(id, borrower);
        else repaidShares = morpho.borrowShares(id, borrower);

        _approveMaxTo(marketParams.loanToken, address(morpho));
        uint256 seizedAssets;
        uint256 repaidAssets;
        (seizedAssets, repaidAssets) = morpho.liquidate(
            marketParams,
            borrower,
            seizedCollateral,
            repaidShares,
            abi.encode(LiquidateData(marketParams.collateralToken))
        );

        emit LiquidationResults(
            seizedAssets,
            IERC20(marketParams.loanToken).balanceOf(msg.sender),
            marketParams.loanToken,
            repaidAssets,
            borrower
        );
        success = true;
    }

    /// @dev Approves the maximum amount of tokens to the specified spender.
    /// @param asset The address of the asset to approve.
    /// @param spender The address of the spender.
    function _approveMaxTo(address asset, address spender) internal {
        if (IERC20(asset).allowance(address(this), spender) == 0) {
            IERC20(asset).approve(spender, type(uint256).max);
        }
    }

    /// @notice Handles the supply of assets by the caller to a specific market.
    /// @param marketParams The parameters of the market.
    /// @param amount The amount of assets the user is supplying.
    /// @return assetsSupplied The actual amount of assets supplied.
    /// @return sharesSupplied The shares supplied in return for the assets.
    function supply(
        MarketParams memory marketParams,
        uint256 amount
    ) external returns (uint256 assetsSupplied, uint256 sharesSupplied) {
        IERC20(marketParams.loanToken).forceApprove(
            address(morpho),
            type(uint256).max
        );
        IERC20(marketParams.loanToken).safeTransferFrom(
            msg.sender,
            address(this),
            amount
        );

        uint256 shares;
        address onBehalf = msg.sender;

        (assetsSupplied, sharesSupplied) = morpho.supply(
            marketParams,
            amount,
            shares,
            onBehalf,
            hex""
        );
    }

    /// @notice Handles the supply of collateral by the caller to a specific market.
    /// @param marketParams The parameters of the market.
    /// @param amount The amount of collateral the user is supplying.
    function supplyCollateral(
        MarketParams memory marketParams,
        uint256 amount
    ) external {
        IERC20(marketParams.collateralToken).approve(
            address(morpho),
            type(uint256).max
        );
        IERC20(marketParams.collateralToken).safeTransferFrom(
            msg.sender,
            address(this),
            amount
        );

        address onBehalf = msg.sender;

        morpho.supplyCollateral(marketParams, amount, onBehalf, hex"");
    }

    /// @notice Handles the withdrawal of collateral by the caller from a specific market of a specific amount.
    /// @param marketParams The parameters of the market.
    /// @param amount The amount of collateral the user is withdrawing.
    function withdrawCollateral(
        MarketParams memory marketParams,
        uint256 amount
    ) external {
        address onBehalf = msg.sender;
        address receiver = msg.sender;

        morpho.withdrawCollateral(marketParams, amount, onBehalf, receiver);
    }

    /// @notice Handles the withdrawal of a specified amount of assets by the caller from a specific market.
    /// @param marketParams The parameters of the market.
    /// @param amount The amount of assets the user is withdrawing.
    /// @return assetsWithdrawn The actual amount of assets withdrawn.
    /// @return sharesWithdrawn The shares withdrawn in return for the assets.
    function withdrawAmount(
        MarketParams memory marketParams,
        uint256 amount
    ) external returns (uint256 assetsWithdrawn, uint256 sharesWithdrawn) {
        uint256 shares;
        address onBehalf = msg.sender;
        address receiver = msg.sender;

        (assetsWithdrawn, sharesWithdrawn) = morpho.withdraw(
            marketParams,
            amount,
            shares,
            onBehalf,
            receiver
        );
    }

    /// @notice Handles the withdrawal of 50% of the assets by the caller from a specific market.
    /// @param marketParams The parameters of the market.
    /// @return assetsWithdrawn The actual amount of assets withdrawn.
    /// @return sharesWithdrawn The shares withdrawn in return for the assets.
    function withdraw50Percent(
        MarketParams memory marketParams
    ) external returns (uint256 assetsWithdrawn, uint256 sharesWithdrawn) {
        Id marketId = marketParams.id();
        uint256 supplyShares = morpho
            .position(marketId, msg.sender)
            .supplyShares;
        uint256 amount;
        uint256 shares = supplyShares / 2;

        address onBehalf = msg.sender;
        address receiver = msg.sender;

        (assetsWithdrawn, sharesWithdrawn) = morpho.withdraw(
            marketParams,
            amount,
            shares,
            onBehalf,
            receiver
        );
    }

    /// @notice Handles the withdrawal of all the assets by the caller from a specific market.
    /// @param marketParams The parameters of the market.
    /// @return assetsWithdrawn The actual amount of assets withdrawn.
    /// @return sharesWithdrawn The shares withdrawn in return for the assets.
    function withdrawAll(
        MarketParams memory marketParams
    ) external returns (uint256 assetsWithdrawn, uint256 sharesWithdrawn) {
        Id marketId = marketParams.id();
        uint256 supplyShares = morpho
            .position(marketId, msg.sender)
            .supplyShares;
        uint256 amount;

        address onBehalf = msg.sender;
        address receiver = msg.sender;

        (assetsWithdrawn, sharesWithdrawn) = morpho.withdraw(
            marketParams,
            amount,
            supplyShares,
            onBehalf,
            receiver
        );
    }

    /// @notice Handles the borrowing of assets by the caller from a specific market.
    /// @param marketParams The parameters of the market.
    /// @param amount The amount of assets the user is borrowing.
    /// @return assetsBorrowed The actual amount of assets borrowed.
    /// @return sharesBorrowed The shares borrowed in return for the assets.
    function borrow(
        MarketParams memory marketParams,
        uint256 amount
    ) external returns (uint256 assetsBorrowed, uint256 sharesBorrowed) {
        uint256 shares;
        address onBehalf = msg.sender;
        address receiver = msg.sender;

        (assetsBorrowed, sharesBorrowed) = morpho.borrow(
            marketParams,
            amount,
            shares,
            onBehalf,
            receiver
        );
    }
    function maxBorrow(
        MarketParams memory marketParams,
        Id id
    ) external view returns (uint256 max) {
        uint256 collateralPrice = IOracle(marketParams.oracle).price();
        Position memory position = morpho.position(id, msg.sender);
        max = position
            .collateral
            .mulDivDown(collateralPrice, ORACLE_PRICE_SCALE)
            .wMulDown(marketParams.lltv);
    }
    /// @notice Handles the repayment of a specified amount of assets by the caller to a specific market.
    /// @param marketParams The parameters of the market.
    /// @param amount The amount of assets the user is repaying.
    /// @return assetsRepaid The actual amount of assets repaid.
    /// @return sharesRepaid The shares repaid in return for the assets.
    function repayAmount(
        MarketParams memory marketParams,
        uint256 amount
    ) external returns (uint256 assetsRepaid, uint256 sharesRepaid) {
        IERC20(marketParams.loanToken).approve(
            address(morpho),
            type(uint256).max
        );
        IERC20(marketParams.loanToken).safeTransferFrom(
            msg.sender,
            address(this),
            amount
        );

        uint256 shares;
        address onBehalf = msg.sender;
        (assetsRepaid, sharesRepaid) = morpho.repay(
            marketParams,
            amount,
            shares,
            onBehalf,
            hex""
        );
    }
}
