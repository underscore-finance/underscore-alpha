# Underscore Protocol: Trustless AI Agents for DeFi

Underscore is an open-source, onchain infrastructure that allows AI agents to operate on your behalf in DeFi—securely, transparently, and within boundaries you define.

## Why Underscore?

- **Non-Custodial**: Retain full control of your assets; only you can transfer or withdraw funds.
- **Granular Control**: Define which assets, protocols, and actions your AI agent can manage—no hidden moves.
- **Rule-Based Autonomy**: Smart contracts strictly enforce your boundaries, ensuring the AI agent never oversteps.
- **Minimal Trust**: Rely on open-source, immutable code instead of opaque server-side wallets.
- **Extensible**: Integrate new DeFi protocols (“legos”) without migrating your wallet—stay future-proof.
- **Auditability**: Transparent, reviewable code that anyone can inspect or verify for security.

## How It Works (High-Level)

1. **Deploy your AI Wallet**: A personal smart contract that you—and your chosen AI agent—control.
2. **Set Permissions & Rules**: Decide exactly which assets, protocols, or operations your agent can handle.
3. **AI Autonomy Within Limits**: The agent can lend, swap, or rebalance your DeFi holdings—but only within your specified parameters.

## Build with Underscore

Deploy your AI Wallet in minutes. Here’s how:

### Create a User AI Wallet

```python
owner = "0xYourOwnerAddress"  # Your wallet address

user_ai_wallet = agent_factory.createUserWallet(
    owner,  # You are the ultimate owner
    agent   # Your AI agent's address
)

```

### Configure Agent Permissions

```python
# Allowed assets (e.g., WETH, USDC)
allowed_assets = [
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"   # USDC
]
for asset in allowed_assets:
    user_wallet_config.addAssetForAgent(agent, asset, sender=owner)

# Allowed protocols (e.g., Aave, Uniswap)
allowed_protocols = [1, 2]  # Lego IDs
for protocol_id in allowed_protocols:
    user_wallet_config.addLegoIdForAgent(agent, protocol_id, sender=owner)

```

### AI-Driven DeFi Actions

```python
# Example: Swap WETH → USDC on Uniswap (legoId = 2)
swap = {"legoId": 2, "amountIn": weth_amount, "tokenPath": [weth, usdc]}
user_ai_wallet.swapTokens([swap], sender=agent)

# Example: Deposit into Aave (legoId = 1)
user_ai_wallet.depositTokens(1, usdc, usdc_amount, sender=agent)
```

For a complete walkthrough, see our [Getting Started Guide](docs/guides/GETTING_STARTED.md).

## Use Cases

- **Autonomous Yield Farming**: your AI agent could monitor lending rates on Aave and Compound, shifting funds to whichever yields the best APY -- all within your specified risk tolerance.
- **Portfolio Rebalancing**: your AI agent could dynamically rebalance your holdings (e.g., 50% stablecoins, 50% ETH). If the price of ETH spikes, the agent swaps just enough to maintain your target ratios.
- **Proactive Risk Monitoring**: your agent could watch onchain data for liquidity drops or major volatility. If a threshold is hit, it automatically unwinds high-risk positions -- limited only to the protocols you’ve authorized.

## Why It Matters

AI agents in DeFi are powerful but can be risky—server-side AI wallets can be compromised, leaving your funds vulnerable. Underscore takes a trust-minimized approach:

- **Smart Contracts Govern the Rules**: No black-box infrastructure or opaque custodians.
- **No Blind Trust**: Full transparency in code and onchain operations.
- **Security by Design**: Even if the AI logic goes astray, it can’t exceed your smart contract’s strict parameters.

## Quick Navigation

### Technical Reference

- [**Core Components**](docs/technical/CORE_COMPONENTS.md): Core smart contracts and their relationships
- [**Interfaces**](docs/technical/INTERFACES.md): System interfaces and interaction patterns
- [**Legos**](docs/technical/LEGOS.md): Modular protocol integrations

### Developer Guides

- [**Getting Started**](docs/guides/GETTING_STARTED.md): Create your first User AI Wallet
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

## Frequently Asked Questions

**Q: Is Underscore custodial?**  
A: No, only you can withdraw funds from your AI Wallet.

**Q: Can I use Underscore without AI?**  
A: Absolutely. You can use manual agents or other automation solutions.

**Q: Which blockchains are supported?**  
A: Currently Base L2, with plans for additional EVM-compatible chains.

**Q: Can I upgrade my AI Wallet?**  
A: The core wallet is immutable. However, you can add new DeFi integrations (“legos”) as they become available, without migrating funds.

**Q: Who manages the AI logic?**  
A: That’s up to you. Underscore provides the infrastructure to constrain AI agents within onchain rules, but the agent’s code or service can be yours or a third party’s.

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

## Get Involved

Underscore bridges AI and DeFi without compromising security or sovereignty. Ready to scale trustless finance?

- [GitHub Repo](https://github.com/underscore-finance) – Dive into the code and open issues or PRs.
- [Discord](https://discord.gg/Y6PWmndNaC) - Join our community for support, discussions, and real-time updates.
- [Twitter/X](https://x.com/underscore_hq) – Follow for announcements, roadmap highlights, and more.

Built by the team at [Hightop](http://hightop.com) + [Ripe](http://ripe.finance)

## License

Underscore Protocol uses a dual-licensing approach:

- **Core Protocol (BUSL-1.1)**: The core protocol implementation and DeFi integrations (legos) are licensed under the [Business Source License 1.1](LICENSE) (BUSL-1.1). This allows for non-production use and will automatically convert to the MIT License on March 6, 2029, or earlier as specified at [LICENSE_DATE.md](LICENSE_DATE.md).

- **Interfaces (MIT)**: All interfaces and integration libraries are licensed under the MIT License to enable seamless integration with the protocol.

For production use of BUSL-1.1 licensed code, please refer to the [Additional Use Grants](LICENSE_GRANTS.md) or contact Hightop Financial, Inc. for a commercial license.

For detailed information about which directories and files are covered by each license, please see [LICENSE_INFO.md](LICENSE_INFO.md).

## Deployment Addresses

### Base Mainnet

| Core Contracts           |                                                                                                                       |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| AddyRegistry             | [0xdCCaB9855D7eE558409EBdf358a3A44a8b2415B3](https://basescan.org/address/0xdCCaB9855D7eE558409EBdf358a3A44a8b2415B3) |
| AgentFactory             | [0x5cd5Adb8CE20401D064da60aE051eFc3753CE436](https://basescan.org/address/0x5cd5Adb8CE20401D064da60aE051eFc3753CE436) |
| UserWalletTemplate       | [0xf614Bb656a8B1B8646b25f3Ca4a9655E407D38e5](https://basescan.org/address/0xf614Bb656a8B1B8646b25f3Ca4a9655E407D38e5) |
| UserWalletConfigTemplate | [0xAeE931cC57CfBE31328bCfF092Af7eC7dFD7EBC8](https://basescan.org/address/0xAeE931cC57CfBE31328bCfF092Af7eC7dFD7EBC8) |
| AgentTemplate            | [0x2e3754aD00DcC1c31Ee1Ea46379DA83bD02896F7](https://basescan.org/address/0x2e3754aD00DcC1c31Ee1Ea46379DA83bD02896F7) |
| LegoRegistry             | [0x5dC5A7304a1f2feeadF491b8F62BD41687CB330b](https://basescan.org/address/0x5dC5A7304a1f2feeadF491b8F62BD41687CB330b) |
| OracleRegistry           | [0x4D97d514d92Efd711D0645fE0759fA68480facc5](https://basescan.org/address/0x4D97d514d92Efd711D0645fE0759fA68480facc5) |
| PriceSheets              | [0x38Cd202B42b3906051573174e506b5b6BC83D47C](https://basescan.org/address/0x38Cd202B42b3906051573174e506b5b6BC83D47C) |
| LegoHelper               | [0xF2920Dcb5298D48755b49a5e91F073D47A25439b](https://basescan.org/address/0xF2920Dcb5298D48755b49a5e91F073D47A25439b) |

| Oracles        |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| ChainlinkFeeds | [0x5e06882026739D91541b4F979FbF40057C75aB96](https://basescan.org/address/0x5e06882026739D91541b4F979FbF40057C75aB96) |
| PythFeeds      | [0x56cC721FA002425b074e767A1F7B663Eb00C7535](https://basescan.org/address/0x56cC721FA002425b074e767A1F7B663Eb00C7535) |
| StorkFeeds     | [0x37Ce94Ec6A9072ee1231eff57A8987448aDb8E0a](https://basescan.org/address/0x37Ce94Ec6A9072ee1231eff57A8987448aDb8E0a) |

| Yield Legos    |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| LegoAaveV3     | [0x580729527620ab496195465bfFD15E89eFb508B4](https://basescan.org/address/0x580729527620ab496195465bfFD15E89eFb508B4) |
| LegoCompoundV3 | [0x71fC412B72e052F91AEF0e11084D7cEb99ae275c](https://basescan.org/address/0x71fC412B72e052F91AEF0e11084D7cEb99ae275c) |
| LegoEuler      | [0x29e0815b2c801D6946bD05EB0A5c9b5a510d88f1](https://basescan.org/address/0x29e0815b2c801D6946bD05EB0A5c9b5a510d88f1) |
| LegoFluid      | [0x76765fcd0A666fAc585e520C421FcD881ca0d861](https://basescan.org/address/0x76765fcd0A666fAc585e520C421FcD881ca0d861) |
| LegoMoonwell   | [0x959753dB45E61Cf7dCc6057279A57AC286830C28](https://basescan.org/address/0x959753dB45E61Cf7dCc6057279A57AC286830C28) |
| LegoMorpho     | [0xF7B09b7E6528037e125Ac8d3Ed047A39d10A32AF](https://basescan.org/address/0xF7B09b7E6528037e125Ac8d3Ed047A39d10A32AF) |
| LegoSky        | [0x6c2496434a42779A1c5dc62C18B3177C1771Bb80](https://basescan.org/address/0x6c2496434a42779A1c5dc62C18B3177C1771Bb80) |

| Dex Legos          |                                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| LegoAeroClassic    | [0xF66d2FD9Ee2975DF518c6bA9D2ff7d562EE8530b](https://basescan.org/address/0xF66d2FD9Ee2975DF518c6bA9D2ff7d562EE8530b) |
| LegoAeroSlipstream | [0xe819d6367d393AD952265Ed34b2A9A67a3F1423A](https://basescan.org/address/0xe819d6367d393AD952265Ed34b2A9A67a3F1423A) |
| LegoCurve          | [0x3EadC664BE12D7Ef39ACf50C48695ff8614127f1](https://basescan.org/address/0x3EadC664BE12D7Ef39ACf50C48695ff8614127f1) |
| LegoUniswapV2      | [0xC9Eeeab623B1cd6b53a03938Df5eBf9B7d3d2C0F](https://basescan.org/address/0xC9Eeeab623B1cd6b53a03938Df5eBf9B7d3d2C0F) |
| LegoUniswapV3      | [0x5282BA17Ec8cF31c78404d0C57Fb7CfeabC212a0](https://basescan.org/address/0x5282BA17Ec8cF31c78404d0C57Fb7CfeabC212a0) |
