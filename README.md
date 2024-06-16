# Morpho Blue Liquidation Bot

This repository contains a Proof of Concept (POC) implementation of a liquidation bot capable of liquidating any asset on Morpho Blue.

## Badges

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

## Table of Contents

1. [Overview](#overview)
2. [Detailed Explanation](#detailed-explanation)
    1. [Task Scheduler](#task-scheduler)
    2. [Redis](#redis)
    3. [Blockchain Node](#blockchain-node)
    4. [Market Configuration](#market-configuration)
3. [Bot Configuration](#bot-configuration)
4. [Tech Stack](#tech-stack)
5. [Lessons Learned](#lessons-learned)
6. [Run Locally](#run-locally)
7. [Testing](#testing)
8. [Acknowledgements](#acknowledgements)
9. [Feedback](#feedback)
10. [License](#license)

## Overview

Morpho Blue is a trustless and efficient lending protocol that allows for permissionless market creation. It enables the deployment of minimal and isolated lending markets by specifying:

- One collateral asset
- One loan asset
- A Liquidation Loan To Value (LLTV)
- An Interest Rate Model (IRM)
- An oracle

The protocol is designed to be more efficient and flexible than any other decentralized lending platform.

This repository contains a POC implementation of how liquidations could be executed on any given market. The diagram below provides an overview of how the different components within the bot interact.

![Overview](./diagrams/1.png)

The bot uses three key components:

- Task Scheduler
- Redis
- Blockchain Node
- GraphQL
- Markets Behaviour
- Market Behaviour

### Task Scheduler

The task scheduler plans future liquidation executions using [asyncio](https://pypi.org/project/asyncio/).

### Redis

Redis is used to cache liquidated positions. Although other packages could be used, Redis is suitable for this implementation. The `get_cache` and `store_cache` functions return results in JSON format.

### Blockchain Node

The blockchain node is essential for executing liquidations on Morpho Blue.

### Market Configuration

This section includes two classes:

1. **Markets Behaviour**: Sets up different markets defined by users for liquidation.
2. **Market Behaviour**: Handles market-specific tasks including:
    - Allocating each position's health factor
    - Fetching positions
    - Executing liquidations
    - Storing liquidated positions

Liquidations are executed using Multicall, saving gas. Each multicall function processes 100 positions per batch to avoid out-of-gas errors.

The liquidator contract does not immediately swap profits from liquidations, as swapping Token A to Token B for the best quote is an off-chain task. The contract allows the owner to withdraw tokens manually.

To view all liquidations, you can query the Redis DB for all markets where the **liquidated** property is **true**. You can use [Another Redis Desktop Manager](https://goanother.com/).

## Bot Configuration

To configure the bot, refer to the `.env.example` file:

```env
GRAPHQL_API_ENDPOINT=<https://blue-api.morpho.org/graphql>
PRIVATE_KEY=""
LIQUIDATOR_ADDRESS=""
REDIS_HOST=""
RPC_URL="<http://localhost:8545>"
MARKETS=""
MORPHO_ADDRESS=""
INTERVAL=10
```

- **GRAPHQL_API_ENDPOINT**: Public endpoint for querying market data on Morpho Blue
- **PRIVATE_KEY**: Key for executing liquidations
- **LIQUIDATOR_ADDRESS**: Address of the liquidator contract
- **REDIS_HOST**: Redis URL for storing market data
- **RPC_URL**: The RPC URL for connecting to the blockchain
- **MARKETS**: List of markets for liquidation. Separate multiple markets with commas (e.g., "0x...A,0x...B").
- **MORPHO_ADDRESS**: Address of the Morpho Blue contract on the chosen network
- **INTERVAL**: Frequency of bot execution attempts (e.g., 10 = every 10 minutes)

## Tech Stack

![JavaScript](https://img.shields.io/badge/JavaScript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Solidity](https://img.shields.io/badge/Solidity-2674E5?style=for-the-badge&logo=solidity&logoColor=white)
![Excalidraw](https://img.shields.io/badge/excalidraw-FF6C37?style=for-the-badge&logo=excalidraw&logoColor=white)

## Lessons Learned

Building a Liquidation Bot requires careful planning due to various factors, especially depending on the chain. For example, on Ethereum, one must carefully manage gas costs during liquidations.

## Run Locally

### Prerequisites

- [Node.js](https://nodejs.org/)
- [npm](https://www.npmjs.com/)
- [Python](https://www.python.org/)

### Steps

1. **Setup Redis using Docker**:

    ```bash
    docker run -d --name my-redis-stack -p 6379:6379 redis/redis-stack-server:latest
    ```

2. **Clone the project**:

    ```bash
    git clone https://github.com/Brianspha/morpho-blue-bot
    cd morpho-blue-bot
    ```

3. **Install dependencies**:

    ```bash
    npm install
    ```

4. **Setup Python environment**:

    ```bash
    bash setup_env.bash
    ```

5. **Setup Foundry, fork Mainnet Ethereum (see `fork.bash.example`), and create `fork.bash`**:

    ```bash
    bash fork.bash
    ```

6. **Deploy local market**:

    ```bash
    npm run deploy:local
    ```

7. **Create a `.env` file based on `.env.example` and copy relevant values from `deployment.json`**:

    ```env
    GRAPHQL_API_ENDPOINT="https://blue-api.morpho.org/graphql"
    PRIVATE_KEY="private key"
    LIQUIDATOR_ADDRESS="Liquidator"
    REDIS_HOST="redis host"
    RPC_URL="http://localhost:8545"
    MARKETS="CollatToken"
    MORPHO_ADDRESS="Morpho"
    INTERVAL=10
    ```

8. **Run the bot**:

    ```bash
    npm run start
    ```

## Testing

To test liquidations executed by the Liquidator contract, run:

```bash
npm run test
```

## Acknowledgements

- [Awesome Readme Templates](https://awesomeopensource.com/project/elangosundar/awesome-README-templates)
- [Awesome README](https://github.com/matiassingers/awesome-readme)
- [How to Write a Good README](https://bulldogjob.com/news/449-how-to-write-a-good-readme-for-your-github-project)

## Feedback

For feedback, please create an issue.


