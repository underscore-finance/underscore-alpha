# Underscore: Trustless AI Agents for DeFi

## Overview

Underscore is onchain infrastructure that enables AI agents to operate in DeFi within user-defined boundaries. It creates a **User AI Wallet** - a personal smart contract that connects to DeFi protocols with AI assistance while maintaining security and control.

## Key Features

- **Non-Custodial**: Only you can transfer/withdraw funds out of the wallet
- **Granular Control**: Define which assets and protocols AI agents can interact with
- **Rule-Based Actions**: Agents operate strictly within specified parameters
- **Extensible**: Underscore can add new DeFi integrations without you needing to move funds or upgrading your wallet

## Why Underscore?

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│   AI Assistance   │────▶│  Onchain Rules   │────▶│   User Control    │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

- **Minimized Trust**: Rely on immutable smart contracts instead of server-side AI wallets
- **Auditability**: Open-source logic means transparent, reviewable code
- **Security**: Combine AI capabilities with onchain rule enforcement
- **User Sovereignty**: Retain ultimate control over your assets

## Quick Navigation

### Technical Reference

- [**Core Components**](docs/technical/CORE_COMPONENTS.md): Core smart contracts and their relationships
- [**Interfaces**](docs/technical/INTERFACES.md): System interfaces and interaction patterns
- [**Legos**](docs/technical/LEGOS.md): Modular protocol integrations

### Developer Guides

- [**Getting Started**](docs/guides/GETTING_STARTED.md): Create your first User AI Wallet
- [**Deployment Guide**](docs/guides/DEPLOYMENT.md): Deploy the Underscore system
- [**Testing Guide**](docs/guides/TESTING.md): Test the Underscore system

### API Reference

- [**AgentFactory**](docs/api/AgentFactory.md): Creates and manages user wallets and agents
- [**AgentTemplate**](docs/api/AgentTemplate.md): Template for AI agents and their actions
- [**WalletConfig**](docs/api/WalletConfig.md): Manages wallet configuration settings
- [**WalletFunds**](docs/api/WalletFunds.md): Handles user funds management
- [**LegoRegistry**](docs/api/LegoRegistry.md): Registry for DeFi protocol integrations
- [**OracleRegistry**](docs/api/OracleRegistry.md): Registry for price oracles
- [**AddyRegistry**](docs/api/AddyRegistry.md): Registry for system component addresses
- [**PriceSheets**](docs/api/PriceSheets.md): Handles price data and calculations
- [**LegoHelper**](docs/api/LegoHelper.md): Helper functions for lego operations

## Example Usage

### Create a User AI Wallet

A User AI Wallet is a smart contract wallet that the user owns, and that AI agents can interact with on the user's behalf. The User AI wallet interacts with DeFi. Here's how to create one:

```python
owner = "0xYourOwnerAddress", # your wallet address (i.e. Ledger hardware wallet)

user_ai_wallet = agent_factory.createUserWallet(
    owner, # owner of the User AI Wallet
    agent, # agent address
)
```

### Configure AI Agent Permissions

Set boundaries and permissions with what the agent is allowed to do:

```python
user_wallet_config = user_ai_wallet.walletConfig()

# assets the agent can interact with
allowed_assets = ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                  "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"]  # USDC
for asset in allowed_assets:
    user_wallet_config.addAssetForAgent(agent, asset, sender=owner)

# protocols agent can interact with
allowed_protocols = [1, 2]  # lego ids (i.e. aave, uniswap)
for protocol_id in allowed_protocols:
    user_wallet_config.addLegoIdForAgent(agent, protocol_id, sender=owner)

# actions the agent can perform
allowed_actions = {
    "canDeposit": True,
    "canWithdraw": True,
    "canSwap": False,
    ...
}
wallet_config.modifyAllowedActions(
    agent,
    allowed_actions,
    sender=owner
)
```

### Agent can perform actions

Once funds are in the User's AI Wallet, the agent can perform DeFi actions within the boundaries that the user has set:

```python
# perform a swap with uniswap
swap = {
    "legoId": 2, # uniswap
    "amountIn": weth_amount, # amount to swap from
    "tokenPath": [weth, usdc], # swapping from weth to usdc
    ...
}
user_ai_wallet.swapTokens([swap], sender=agent)

# deposit into aave
user_ai_wallet.depositTokens(
    1, # aave lego id
    usdc, # asset to deposit into aave
    usdcAToken, # aave aToken
    usdc_amount, # amount to deposit into aave
    sender=agent
)
```

For a complete walkthrough, see our [Getting Started Guide](docs/guides/GETTING_STARTED.md).

## Glossary

| Term                | Definition                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------------- |
| **User AI Wallet**  | A smart contract wallet that can be controlled by an AI agent within user-defined boundaries |
| **Lego**            | A modular integration with a DeFi protocol (e.g., Aave, Uniswap)                             |
| **Agent**           | An entity (AI or human) that can perform actions on behalf of the wallet owner               |
| **WalletConfig**    | Contract that stores configuration and permissions for a User AI Wallet                      |
| **WalletFunds**     | Contract that manages funds and executes transactions for a User AI Wallet                   |
| **LegoRegistry**    | Contract that registers and manages protocol integrations                                    |
| **AgentFactory**    | Contract that creates and manages agents and User AI Wallets                                 |
| **Allowed Actions** | Specific operations that an agent is permitted to perform                                    |
| **Rule**            | A condition-action pair that defines automated behavior for an agent                         |
| **Whitelist**       | A list of approved addresses, assets, or protocols                                           |

## Frequently Asked Questions

### General Questions

**Q: Is Underscore custodial?**  
A: No, Underscore is non-custodial. Only the wallet owner can withdraw funds.

**Q: Can I use Underscore without AI?**  
A: Yes, Underscore can be used with manual agents or other automation systems.

**Q: Which blockchains are supported?**  
A: Currently only Base L2, with plans to expand to other EVM-compatible chains.

### Technical Questions

**Q: How are funds secured?**  
A: Funds are secured through smart contract permissions, with only the wallet owner able to withdraw funds.

**Q: Can I upgrade my User AI Wallet?**  
A: The core wallet cannot be upgraded, but new protocol integrations (legos) can be added without moving funds.

## License

Underscore Protocol uses a dual-licensing approach:

- **Core Protocol (BUSL-1.1)**: The core protocol implementation and DeFi integrations (legos) are licensed under the [Business Source License 1.1](LICENSE) (BUSL-1.1). This allows for non-production use and will automatically convert to the MIT License on March 6, 2029, or earlier as specified at [LICENSE_DATE.md](LICENSE_DATE.md).

- **Interfaces (MIT)**: All interfaces and integration libraries are licensed under the MIT License to enable seamless integration with the protocol.

For production use of BUSL-1.1 licensed code, please refer to the [Additional Use Grants](LICENSE_GRANTS.md) or contact Hightop Financial, Inc. for a commercial license.

For detailed information about which directories and files are covered by each license, please see [LICENSE_INFO.md](LICENSE_INFO.md).

## Deployment Addresses

### Base Mainnet

| Core Contracts |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| AddyRegistry   | [0x49B08551e452cA99da7dE9B3a60E39e5f10C13CD](https://basescan.org/address/0x49B08551e452cA99da7dE9B3a60E39e5f10C13CD) |
| AgentFactory   | [0x7bA5A18b88fFc9bB569d5A7e311c1607a0737a25](https://basescan.org/address/0x7bA5A18b88fFc9bB569d5A7e311c1607a0737a25) |
| WalletFunds    | [0x6A5263B0645c7dFd2788eF46f95f210E947e0743](https://basescan.org/address/0x6A5263B0645c7dFd2788eF46f95f210E947e0743) |
| WalletConfig   | [0x45D1a9429Fd603c13Cdab685dc2540f4F57Df464](https://basescan.org/address/0x45D1a9429Fd603c13Cdab685dc2540f4F57Df464) |
| AgentTemplate  | [0x70418b3AAa1044eC8bFF6a461B4E43460bb5699E](https://basescan.org/address/0x70418b3AAa1044eC8bFF6a461B4E43460bb5699E) |
| LegoRegistry   | [0x590504539913411CeF7fc1b3Fa49b06FE970c759](https://basescan.org/address/0x590504539913411CeF7fc1b3Fa49b06FE970c759) |
| OracleRegistry | [0xc56add9377Bc3a39f1B928Abc7440E43B6b10e1f](https://basescan.org/address/0xc56add9377Bc3a39f1B928Abc7440E43B6b10e1f) |
| PriceSheets    | [0x59918c90eD44a3D7a72375f60C0148Ae18001ADC](https://basescan.org/address/0x59918c90eD44a3D7a72375f60C0148Ae18001ADC) |
| LegoHelper     | [0xd313d00cC5E2129799B90Ad538334BB19e17dfEd](https://basescan.org/address/0xd313d00cC5E2129799B90Ad538334BB19e17dfEd) |

| Oracles        |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| ChainlinkFeeds | [0x6035ff5936563132caD931a3a2F328477372fb82](https://basescan.org/address/0x6035ff5936563132caD931a3a2F328477372fb82) |
| PythFeeds      | [0xB8090783aBF7B6336121FAfd6c4aCa3C4516792D](https://basescan.org/address/0xB8090783aBF7B6336121FAfd6c4aCa3C4516792D) |
| StorkFeeds     | [0x389e7d981A74cd957bf56d83cCB85e6fc9e9d9bD](https://basescan.org/address/0x389e7d981A74cd957bf56d83cCB85e6fc9e9d9bD) |

| Yield Legos    |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| LegoAaveV3     | [0x904CCd911533259C1d6B4C50d87DE8130ABeb55D](https://basescan.org/address/0x904CCd911533259C1d6B4C50d87DE8130ABeb55D) |
| LegoCompoundV3 | [0x8546b0ad0C399930847ce725921DBE0F7c106aD9](https://basescan.org/address/0x8546b0ad0C399930847ce725921DBE0F7c106aD9) |
| LegoEuler      | [0x38400f38E1e7E5d0c49C10a43c37a32977b62339](https://basescan.org/address/0x38400f38E1e7E5d0c49C10a43c37a32977b62339) |
| LegoFluid      | [0xfC78950624d322D30D11aF8363BEB3BdA559FaB9](https://basescan.org/address/0xfC78950624d322D30D11aF8363BEB3BdA559FaB9) |
| LegoMoonwell   | [0xCAacba1b91F4004CCba7d3Ffea0CaAd7E588EEe4](https://basescan.org/address/0xCAacba1b91F4004CCba7d3Ffea0CaAd7E588EEe4) |
| LegoMorpho     | [0x055104Bc79447c94655aABA432D60e0f2ab44cb3](https://basescan.org/address/0x055104Bc79447c94655aABA432D60e0f2ab44cb3) |
| LegoSky        | [0x43bd7a38464179d56402341d03bF030BF3140D41](https://basescan.org/address/0x43bd7a38464179d56402341d03bF030BF3140D41) |

| Dex Legos          |                                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| LegoAeroClassic    | [0xdE426b4f9f6C6ed8D254b6363089597d9eb102A3](https://basescan.org/address/0xdE426b4f9f6C6ed8D254b6363089597d9eb102A3) |
| LegoAeroSlipstream | [0xD6A7aDdB5bCF306e9D5C0d431103C5641576bB90](https://basescan.org/address/0xD6A7aDdB5bCF306e9D5C0d431103C5641576bB90) |
| LegoCurve          | [0xEA11B89c506a1B4b2D214643d4019BBc64B92958](https://basescan.org/address/0xEA11B89c506a1B4b2D214643d4019BBc64B92958) |
| LegoUniswapV2      | [0xFA56408A68ba9bF5Df0F1CF4187B7260fDf38fC4](https://basescan.org/address/0xFA56408A68ba9bF5Df0F1CF4187B7260fDf38fC4) |
| LegoUniswapV3      | [0x83C1864F112A9CD8b9e93c4a166F4d885244Eef3](https://basescan.org/address/0x83C1864F112A9CD8b9e93c4a166F4d885244Eef3) |
