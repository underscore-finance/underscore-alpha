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
| AddyRegistry             | [0x7BcD6d471D1A068012A79347C7a944d1Df01a1AE](https://basescan.org/address/0x7BcD6d471D1A068012A79347C7a944d1Df01a1AE) |
| AgentFactory             | [0xd5a1cc447D94114136A5a8828F59d5a1cfe65038](https://basescan.org/address/0xd5a1cc447D94114136A5a8828F59d5a1cfe65038) |
| UserWalletTemplate       | [0xe43D5bD11a2A6A9348EFC516ad9Ac3D32164A5A0](https://basescan.org/address/0xe43D5bD11a2A6A9348EFC516ad9Ac3D32164A5A0) |
| UserWalletConfigTemplate | [0x61293F1bF484d20dcc841175b4E4A0F46c26658c](https://basescan.org/address/0x61293F1bF484d20dcc841175b4E4A0F46c26658c) |
| AgentTemplate            | [0x76Eb19Ae42c07a7AD50aFD58b579a7c45bd70183](https://basescan.org/address/0x76Eb19Ae42c07a7AD50aFD58b579a7c45bd70183) |
| LegoRegistry             | [0x8D8593FE154d14976352FA2CE30322EcDF99C72a](https://basescan.org/address/0x8D8593FE154d14976352FA2CE30322EcDF99C72a) |
| OracleRegistry           | [0xe133F22aAdC23F9B7ca7A9f16B6D9A0C662Cf90b](https://basescan.org/address/0xe133F22aAdC23F9B7ca7A9f16B6D9A0C662Cf90b) |
| PriceSheets              | [0xD15331Cf355B5D8EF017c1FD49516b95593FA6aA](https://basescan.org/address/0xD15331Cf355B5D8EF017c1FD49516b95593FA6aA) |
| LegoHelper               | [0xF80b87DD1096f9E68739f55B9807Df1CB21422E3](https://basescan.org/address/0xF80b87DD1096f9E68739f55B9807Df1CB21422E3) |

| Oracles        |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| ChainlinkFeeds | [0x605c6ab843d65dD14b00CEB33f445D7f9bbb7930](https://basescan.org/address/0x605c6ab843d65dD14b00CEB33f445D7f9bbb7930) |
| PythFeeds      | [0x415a2fe1e591619c6c12Df09eAEc8a598224F9fE](https://basescan.org/address/0x415a2fe1e591619c6c12Df09eAEc8a598224F9fE) |
| StorkFeeds     | [0xD47D74C56c17Bf3B7236e8a7eb97D3194c3d477c](https://basescan.org/address/0xD47D74C56c17Bf3B7236e8a7eb97D3194c3d477c) |

| Yield Legos    |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| LegoAaveV3     | [0x8c94cfC11A9340e45032e5021881cc312993Bf15](https://basescan.org/address/0x8c94cfC11A9340e45032e5021881cc312993Bf15) |
| LegoCompoundV3 | [0xF86d1D68C951d163aBc383C508740df6ddED500C](https://basescan.org/address/0xF86d1D68C951d163aBc383C508740df6ddED500C) |
| LegoEuler      | [0xB2a1cdC1D896eE37cD432b591FeC2664294286FB](https://basescan.org/address/0xB2a1cdC1D896eE37cD432b591FeC2664294286FB) |
| LegoFluid      | [0xc4a864F5543D3CDB06D5F3419c18315f2cDe9675](https://basescan.org/address/0xc4a864F5543D3CDB06D5F3419c18315f2cDe9675) |
| LegoMoonwell   | [0x3890573c04A13d1D982104c7DaDb17F66cb1aE6c](https://basescan.org/address/0x3890573c04A13d1D982104c7DaDb17F66cb1aE6c) |
| LegoMorpho     | [0x825309418B066603C2732fdA08d39A79CAA5CC8e](https://basescan.org/address/0x825309418B066603C2732fdA08d39A79CAA5CC8e) |
| LegoSky        | [0x3514536163D5c0c5207A6A1230fc76bEe8CE8506](https://basescan.org/address/0x3514536163D5c0c5207A6A1230fc76bEe8CE8506) |

| Dex Legos          |                                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| LegoAeroClassic    | [0x61C8D98F01B066fA99eb2cf2E6069a7e5d891313](https://basescan.org/address/0x61C8D98F01B066fA99eb2cf2E6069a7e5d891313) |
| LegoAeroSlipstream | [0x0891DdE2eC48f9663A1c9a81820c283dD8846594](https://basescan.org/address/0x0891DdE2eC48f9663A1c9a81820c283dD8846594) |
| LegoCurve          | [0x6118D44763a556Cf8d113ebBce853E14a0C67997](https://basescan.org/address/0x6118D44763a556Cf8d113ebBce853E14a0C67997) |
| LegoUniswapV2      | [0x9973e271Bd6cAb8Ce1CAEaBAB8a1bEbcB6EdD535](https://basescan.org/address/0x9973e271Bd6cAb8Ce1CAEaBAB8a1bEbcB6EdD535) |
| LegoUniswapV3      | [0x6bfd82031a968685358DA84ebB797c3C068EC704](https://basescan.org/address/0x6bfd82031a968685358DA84ebB797c3C068EC704) |
