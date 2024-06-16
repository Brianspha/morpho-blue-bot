// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;
import {LiquidatorBaseTest, MarketParams, Market, Position, Vm, console, Id} from "./base/LiquidatorBase.t.sol";

contract LiquidatorTest is LiquidatorBaseTest {
    function setUp() public override {
        LiquidatorBaseTest.setUp();
    }

    function test_CreateMarket() public {
        vm.selectFork(ethForkID);
        vm.startPrank(spha);
        bytes32 marketId = _createMarket();
        MarketParams memory params = morpho.idToMarketParams(Id.wrap(marketId));
        assertEq(params.loanToken, address(loanToken));
        assertEq(params.collateralToken, address(collateralToken));
        assertEq(params.oracle, address(mockOracleLoanToken));
        assertEq(params.irm, address(0));
        assertEq(params.lltv, 945000000000000000);
        vm.stopPrank();
    }
    function test_SupplyAsset() public {
        vm.selectFork(ethForkID);
        vm.startPrank(spha);
        bytes32 marketId = _createMarket();
        MarketParams memory marketParams = morpho.idToMarketParams(
            Id.wrap(marketId)
        );
        loanToken.approve(address(liquidator), type(uint256).max);
        liquidator.supply(marketParams, 100 ether);
        assertEq(liquidator.marketTotalSupply(marketParams), 100 ether);
        vm.stopPrank();
    }

    function test_SupplyCollateral() public {
        vm.selectFork(ethForkID);
        vm.startPrank(spha);
        bytes32 marketId = _createMarket();
        MarketParams memory marketParams = morpho.idToMarketParams(
            Id.wrap(marketId)
        );
        uint256 morphoBalanceBefore = collateralToken.balanceOf(
            address(morpho)
        );
        collateralToken.approve(address(liquidator), type(uint256).max);
        liquidator.supplyCollateral(marketParams, 100 ether);
        assertEq(
            collateralToken.balanceOf(address(morpho)) - morphoBalanceBefore,
            100 ether
        );
        vm.stopPrank();
    }
    function test_SupplyOpenPosition_AndLiquidate() public {
        vm.selectFork(ethForkID);
        vm.startPrank(spha);
        (MarketParams memory marketParams, Id id) = _setUpMarket();
        vm.stopPrank();
        vm.startPrank(mike);
        collateralToken.approve(address(liquidator), type(uint256).max);
        morpho.setAuthorization(address(liquidator), true);
        liquidator.supplyCollateral(marketParams, 10 ether);
        liquidator.borrow(marketParams, 954);
        uint256 userHealthFactor = liquidator.userHealthFactor(
            marketParams,
            id,
            mike
        );
        console.log("userHealthFactor:", userHealthFactor);
        vm.stopPrank();
        vm.startPrank(spha);
        mockOracleLoanToken.updatePrice();
        userHealthFactor = liquidator.userHealthFactor(marketParams, id, mike);
        console.log("userHealthFactor1:", userHealthFactor / 1 ether);
        bytes memory data = abi.encodeWithSelector(
            liquidator.fullLiquidationWithoutCollat.selector,
            marketParams,
            mike,
            true
        );
        Call[] memory calls = new Call[](1);
        calls[0] = Call({callData: data, target: address(liquidator)});
        liquidator.aggregate(calls);
        vm.stopPrank();
    }
}
