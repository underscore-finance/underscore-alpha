# Getting Started with Underscore

This guide will walk you through the process of creating, configuring, and using a User AI Wallet with Underscore.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                      User AI Wallet Lifecycle                   │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
┌───────────────────────┐ ┌─────────────┐ ┌─────────────────────┐
│                       │ │             │ │                     │
│      Creation         │ │ Configuration│ │      Usage         │
│                       │ │             │ │                     │
└───────────────────────┘ └─────────────┘ └─────────────────────┘
```

## Prerequisites

Before you begin, ensure you have:

- Python 3.12 installed
- [Vyper 0.4.1](https://docs.vyperlang.org/en/latest/) installed
- [Titanoboa Framework](https://titanoboa.readthedocs.io/en/latest/) installed

## Installation

```bash
# Clone the repository
git clone https://github.com/underscore-finance/underscore.git
cd underscore

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

## Step 1: Create an AI Agent

An agent is a smart contract (with its own owner) that can interact with your User AI Wallet to perform actions on your behalf. Here's how you can create an agent.

```python
# example using titanoboa
import boa
from contracts.core import AgentTemplate

# get agent factory
agent_factory = boa.from_etherscan("0xDeployedAgentFactory")

# create new AI agent
agent_address = agent_factory.createAgent(
    "0xAIAgentDeveloper", # AI developer wallet
)

# get agent contract
agent = AgentTemplate.at(agent_address)
print(f"Agent deployed at: {agent_address}")
```

## Step 2: Create a User AI Wallet

A User AI Wallet is a smart contract wallet that the user owns, and that AI agents can interact with on the user's behalf. The User AI wallet interacts with DeFi. Here's how to create one:

```python
import boa
from contracts.core import WalletFunds

# get agent factory
agent_factory = boa.from_etherscan("0xDeployedAgentFactory")

# create new user AI wallet
user_wallet_address = agent_factory.createUserWallet(
    "0xYourOwnerAddress", # owner wallet address
    agent_address, # see Step 1
)

# get wallet contract
user_wallet = WalletFunds.at(user_wallet_address)
print(f"User AI wallet deployed at: {user_wallet_address}")
```

## Step 3: Configure AI Agent Permissions

Now that you have a User AI Wallet and an AI Agent, you need to configure what it's allowed to do:

```python
import boa
from contracts.core import WalletConfig

# Get the WalletConfig contract associated with your wallet
wallet_config_address = user_wallet.walletConfig()
wallet_config = WalletConfig.at(wallet_config_address)

# Configure allowed assets
allowed_assets = ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                  "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"]  # USDC
for asset in allowed_assets:
    wallet_config.addAssetForAgent(agent_address, asset, sender=user_wallet.owner())

# Configure allowed protocols (legos)
allowed_protocols = [1, 2]  # Example lego IDs for Aave and Uniswap
for protocol_id in allowed_protocols:
    wallet_config.addLegoIdForAgent(agent_address, protocol_id, sender=user_wallet.owner())

# Configure allowed actions
allowed_actions = {
    "canDeposit": True,
    "canWithdraw": True,
    "canSwap": False,
    ...
}
wallet_config.modifyAllowedActions(
    agent_address,
    allowed_actions,
    sender=user_wallet.owner()
)
```

## Step 4: Agent can perform DeFi actions on your behalf

Once funds are sent to the User's AI Wallet, the agent can perform DeFi actions within the boundaries that the user has set:

```python
import boa

weth = boa.from_etherscan("0xWethToken")
usdc = boa.from_etherscan("0xUsdcToken")

# perform a swap with uniswap
weth_amount = weth.balanceOf(user_wallet)
swap = {
    "legoId": 2, # uniswap
    "amountIn": weth_amount, # amount to swap from
    "tokenPath": [weth, usdc], # swapping from weth to usdc
    ...
}
user_wallet.swapTokens([swap], sender=agent) # perform swap

# deposit into aave
usdc_amount = usdc.balanceOf(user_wallet)
user_wallet.depositTokens(
    1, # aave lego id
    usdc, # asset to deposit into aave
    usdcAToken, # aave aToken
    usdc_amount, # amount to deposit into aave
    sender=agent
)
```

## Step 5: Withdraw Funds from User AI Wallet

Funds can only be taken out of the User AI wallet to the owner address, or anyone on whitelist:

```python
import boa

owner = user_wallet.owner()

# take weth out of User AI wallet
user_wallet.transferFunds(
    owner, # recipient
    weth_amount, # amount to transfer
    weth, # asset
    sender=agent # agent can perform this action because recipient is owner
)

# owner can add recipients to whitelist
other_wallet = "0xColdStorage" # the user's other wallet
wallet_config.addWhitelistAddr(other_wallet, sender=owner) # only owner can perform this action

# agent can now send funds to `other_wallet` because it's on whitelist
user_wallet.transferFunds(
    other_wallet, # recipient
    usdc_amount, # amount to transfer
    usdc, # asset
    sender=agent
)

```

## Advanced Configuration

### Configuring Multiple Agents

You can add multiple agents to have access to your User AI Wallet

```python
import boa

# adding agent for usdc yield optimization
yield_agent = "0xYieldAgent"
wallet_config.addOrModifyAgent(
    yield_agent, # agent
    [usdc], # can only interact with usdc
    [1, 3, 4], # can access aave, morpho, moonwell (yield opportunities)
    sender=owner
)

# adding degen agent for trading
degen_agent = "0xDegenTradingAgent"
wallet_config.addOrModifyAgent(
    degen_agent, # agent
    [], # can swap any asset
    [2], # can only access uniswap
    sender=owner
)

```
