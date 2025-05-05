# Underscore Legos

This document provides a high-level overview of the lego modules in the Underscore system.

## What are Legos?

Legos are modular components that integrate with specific DeFi protocols. Each lego implements the relevant interface (LegoYield, LegoDex, or LegoCredit) and provides protocol-specific functionality while maintaining a consistent interaction pattern with the core system.

The lego architecture allows the Underscore system to be extensible:

- New protocol integrations can be added without requiring users to move funds
- Users don't need to upgrade their wallets to access new protocols
- The system can evolve with the DeFi ecosystem

## Lego Categories

```
┌───────────────────────────────────────────────────┐
│                                                   │
│                  Lego Modules                     │
│                                                   │
└───────────┬───────────────────────┬───────────────┘
            │                       │
            ▼                       ▼
┌───────────────────────┐ ┌───────────────────────┐
│                       │ │                       │
│     Yield Legos       │ │      DEX Legos        │
│                       │ │                       │
└───────────────────────┘ └───────────────────────┘
```

### Yield Legos

Yield legos integrate with yield-generating protocols, enabling deposits into yield-bearing vaults, withdrawals from yield positions, and reward claiming.

| Lego Name      | Protocol      | Key Features                             |
| -------------- | ------------- | ---------------------------------------- |
| LegoAaveV3     | Aave V3       | Lending/borrowing, multiple markets      |
| LegoCompoundV3 | Compound V3   | Lending/borrowing with isolated markets  |
| LegoEuler      | Euler Finance | Lending/borrowing, isolated markets      |
| LegoFluid      | Fluid         | Lending/borrowing/DEX integrations       |
| LegoMoonwell   | Moonwell      | Lending/borrowing with governance tokens |
| LegoMorpho     | Morpho        | Peer-to-peer lending/borrowing           |
| LegoSky        | Sky/Maker     | Sky PSM (Peg Stability Module)           |

### DEX Legos

DEX legos integrate with decentralized exchanges, supporting token swaps, liquidity provision/removal, and price queries.

| Lego Name          | Protocol             | Key Features                                 |
| ------------------ | -------------------- | -------------------------------------------- |
| LegoUniswapV2      | Uniswap V2           | Constant product AMM, LP tokens              |
| LegoUniswapV3      | Uniswap V3           | Concentrated liquidity, multiple fee tiers   |
| LegoCurve          | Curve Finance        | Stablecoin-optimized AMM, various pool types |
| LegoAeroClassic    | Aerodrome Classic    | Base network DEX, classic pools              |
| LegoAeroSlipstream | Aerodrome Slipstream | Base network DEX, slipstream pools           |

## Lego Registry and Governance

All legos are registered in the LegoRegistry contract, which provides:

- Type-based categorization (YIELD_OPP, DEX)
- Secure registration with governance delay
- Version tracking and upgradability
- Discovery mechanisms for supported protocols

Adding or updating legos requires a two-step governance process:

1. Initiating the change (registration, update, or disable)
2. Confirming the change after a delay period

## Lego Implementation Pattern

All legos follow a consistent implementation pattern:

1. **Interface Implementation**: Each lego implements the relevant interfaces (LegoCommon + protocol-specific interface)
2. **Protocol Integration**: Legos handle the specific details of interacting with their target protocol
3. **Asset Conversion**: Legos manage the conversion between user assets and protocol-specific tokens
4. **Position Tracking**: Legos track user positions and balances within the protocol
5. **Security Measures**: Legos implement security checks and validations

## Lego Common Interface

All legos implement the LegoCommon interface, which provides:

- Lego identification and type information
- Protocol and asset validation
- Standard interaction patterns
- Error handling and reporting

## Protocol-Specific Interfaces

In addition to LegoCommon, each lego implements a protocol-specific interface:

### LegoYield Interface

- Vault token discovery and management
- Deposit and withdrawal operations
- Underlying asset calculations
- Yield tracking and estimation

### LegoDex Interface

- Token swap operations
- Liquidity provision and removal
- Price quote and slippage calculations
- Pool information and management

## LegoHelper

The LegoHelper contract serves as a utility layer that simplifies complex operations across multiple legos:

- Multi-step operations like zap-ins
- Cross-protocol optimizations
- Standardized interaction patterns
- Gas-efficient execution

## Using Legos

Legos are not directly accessed by users or agents. Instead:

1. Agents call functions on the UserWalletTemplate (WalletFunds) contract
2. UserWalletTemplate validates permissions and parameters
3. UserWalletTemplate delegates the operation to the appropriate lego
4. The lego executes the operation on the target protocol
5. Results are returned through UserWalletTemplate to the agent

For detailed information about specific lego implementations, please refer to the contract source files in the `contracts/legos` directory.
