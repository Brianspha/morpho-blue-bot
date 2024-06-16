// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import {JsonDeploymentHandler} from "./JsonDeploymentHandler.sol";
import {JsonDeploymentHandler} from "./JsonDeploymentHandler.sol";
import {MockOracle} from "../src/MockOracle.sol";
import {MockToken} from "../src/MockToken.sol";
import {Swap} from "../src/Swap.sol";
import {ERC20, IERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "forge-std/Test.sol";
import "../src/Liquidator.sol";
import "forge-std/Script.sol";
contract LiquidatorScript is Script, JsonDeploymentHandler, Multicall3 {
    using SafeERC20 for MockToken;
    Liquidator public liquidator;
    ERC20 public token;
    MockToken public loanToken;
    MockToken public collateralToken;
    MockOracle public mockOracleLoanToken;
    MockOracle public mockOracleCollatToken;
    Swap public swapper;
    IMorpho public morpho;
    address public owner;
    address public spha;
    address public mike;
    constructor() JsonDeploymentHandler("main") {}

    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        spha = vm.addr(deployerPrivateKey);
        morpho = IMorpho(address(0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb));
        liquidator = new Liquidator(
            address(morpho),
            address(0xE592427A0AEce92De3Edee1F18E0157C05861564)
        );
        loanToken = new MockToken("LoanToken", "LT");
        collateralToken = new MockToken("CollatToken", "CT");
        swapper = new Swap(
            address(0xE592427A0AEce92De3Edee1F18E0157C05861564),
            address(loanToken),
            address(collateralToken),
            address(liquidator)
        );
        morpho.setAuthorization(address(liquidator), true);
        mockOracleLoanToken = new MockOracle(101 ether);
        mockOracleCollatToken = new MockOracle(331 ether);
        _mintTokens(spha, collateralToken, 20000 ether);
        _postdeploy("Liquidator", address(liquidator));
        _postdeploy("CollatToken", address(collateralToken));
        _postdeploy("LoanToken", address(loanToken));
        _postdeploy("MockOracleLoanToken", address(mockOracleLoanToken));
        _postdeploy("MockOracleCollatToken", address(mockOracleCollatToken));
        _postdeploy("Morpho", address(morpho));
        _postdeploy("Swap", address(swapper));
        _writeDeployment(false, "./deploy-out/deployment.json");
        _createMarkets();
    }
    function _postdeploy(
        string memory contractKey,
        address newAddress
    ) private {
        _writeAddress(contractKey, newAddress);
        vm.label(newAddress, contractKey);
        console2.log(string.concat(contractKey, " deployed to:"), newAddress);
    }

    function _mintTokens(
        address to,
        MockToken token_,
        uint256 amount
    ) internal {
        token_.mint(to, amount);
    }

    function _createMarkets() internal {
        _mintTokens(spha, collateralToken, 20000 ether);
        _mintTokens(spha, loanToken, 20000 ether);
        (MarketParams memory marketParams, Id id) = _setUpMarket();
        _mintTokens(address(liquidator), loanToken, 200000 ether);
        _openPostion(marketParams, id);
        mockOracleLoanToken.updatePrice();
    }
    function _createMarket() internal returns (bytes32) {
        vm.recordLogs();
        morpho.createMarket(
            MarketParams({
                loanToken: address(loanToken),
                collateralToken: address(collateralToken),
                oracle: address(mockOracleLoanToken),
                irm: address(0),
                lltv: 945000000000000000
            })
        );
        Vm.Log[] memory entries = vm.getRecordedLogs();
        bytes32 marketId = entries[0].topics[1];
        return marketId;
    }
    function _setUpMarket()
        internal
        returns (MarketParams memory marketParams, Id id)
    {
        bytes32 marketId = _createMarket();
        id = Id.wrap(marketId);
        marketParams = morpho.idToMarketParams(id);
        morpho.accrueInterest(marketParams);
        uint256 morphoBalanceBefore = collateralToken.balanceOf(
            address(morpho)
        );
        collateralToken.approve(address(liquidator), type(uint256).max);
        liquidator.supplyCollateral(marketParams, 2000 ether);
        loanToken.approve(address(liquidator), type(uint256).max);
        liquidator.supply(marketParams, 2000 ether);
        assert(liquidator.marketTotalSupply(marketParams) == 2000 ether);
        assert(
            collateralToken.balanceOf(address(morpho)) - morphoBalanceBefore ==
                2000 ether
        );
    }
    function _openPostion(MarketParams memory marketParams, Id id) public {
        collateralToken.approve(address(liquidator), type(uint256).max);
        liquidator.supplyCollateral(marketParams, 10 ether);
        liquidator.borrow(marketParams, liquidator.maxBorrow(marketParams, id));
    }
}
