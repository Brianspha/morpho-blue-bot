// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import {MockOracle} from "../../src/MockOracle.sol";
import {MockToken} from "../../src/MockToken.sol";
import {ERC20, IERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "forge-std/Test.sol";
import "../../src/Liquidator.sol";
abstract contract LiquidatorBaseTest is Test,Multicall3 {
    using SafeERC20 for MockToken;
    Liquidator public liquidator;
    ERC20 public token;
    MockToken public loanToken;
    MockToken public collateralToken;
    MockOracle public mockOracleLoanToken;
    MockOracle public mockOracleCollatToken;
    address public spha;
    address public mike;
    string public ETH_RPC = "";
    uint256 public ethForkID;
    IMorpho public morpho;
    function setUp() public virtual {
        ETH_RPC = vm.envString("RPC_URL");
        ethForkID = vm.createSelectFork(ETH_RPC);
        vm.selectFork(ethForkID);
        spha = _createUser("spha");
        mike = _createUser("mike");

        vm.startPrank(spha);
        morpho = IMorpho(address(0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb));
        liquidator = new Liquidator(
            address(morpho),
            address(0xE592427A0AEce92De3Edee1F18E0157C05861564)
        );
        loanToken = new MockToken("LoanToken", "LT");
        collateralToken = new MockToken("CollatToken", "CT");
        mockOracleLoanToken = new MockOracle(101 ether);
        mockOracleCollatToken = new MockOracle(331 ether);
        vm.stopPrank();
        _mintTokens(mike, collateralToken, 20000 ether);
        _mintTokens(spha, collateralToken, 20000 ether);
        _mintTokens(spha, loanToken, 20000 ether);
        _mintTokens(address(liquidator), loanToken, 20000 ether);
    }

    function _faucetToken(
        address tokenAddress,
        address whale,
        address to,
        uint256 amount
    ) internal {
        vm.startPrank(whale);
        assert(ERC20(tokenAddress).balanceOf(whale) > 0);
        ERC20(tokenAddress).transfer(to, amount);
        vm.stopPrank();
    }
    function _createUser(
        string memory name
    ) internal returns (address payable) {
        address payable user = payable(makeAddr(name));
        vm.deal({account: user, newBalance: 10000 ether});
        vm.label(user, name);
        return user;
    }
    function _mintTokens(
        address to,
        MockToken token_,
        uint256 amount
    ) internal {
        vm.startPrank(spha);
        token_.mint(to, amount);
        vm.stopPrank();
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
        assertEq(liquidator.marketTotalSupply(marketParams), 2000 ether);
        assertEq(
            collateralToken.balanceOf(address(morpho)) - morphoBalanceBefore,
            2000 ether
        );
    }
}
