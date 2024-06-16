// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import {Script} from "forge-std/Script.sol";
import {stdJson} from "forge-std/StdJson.sol";

import {StringUtil} from "./StringUtil.sol";

contract JsonDeploymentHandler is Script {
    using StringUtil for uint256;
    using stdJson for string;

    string output;
    string readJson;
    string chainId;
    string key;
    string internalKey = "key";

    constructor(string memory _key) {
        chainId = (block.chainid).toString();
        key = _key;
    }

    function _readAddress(
        string memory readPath
    ) internal view returns (address) {
        try vm.parseJsonAddress(readJson, readPath) returns (address addr) {
            return addr;
        } catch {
            return address(0);
        }
    }

    function _readDeployment() internal {
        string memory root = vm.projectRoot();
        string memory filePath = string.concat("./deploy-out/deployment.json");
        string memory path = string.concat(root, filePath);
        readJson = vm.readFile(path);
    }

    function _writeAddress(
        string memory contractKey,
        address newAddress
    ) internal {
        output = vm.serializeAddress(internalKey, contractKey, newAddress);
    }
    function _resetOutput() internal {
        output = "";
    }
    function _writeToJson(
        string memory contractKey,
        string memory value
    ) internal {
        vm.writeJson(
            value,
            string.concat("./deploy-out/deploymentTx.json"),
            contractKey
        );
    }

    function _writeDeployment(bool withKey, string memory fileName) internal {
        if (withKey) {
            vm.writeJson(output, fileName, string.concat(".", key));
        } else {
            vm.writeJson(output, fileName);
        }
    }
}
