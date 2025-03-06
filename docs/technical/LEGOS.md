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

| Lego Name | Protocol | Key Features |
|-----------|----------|--------------|
| LegoAaveV3 | Aave V3 | Lending/borrowing |
| LegoCompoundV3 | Compound V3 | Lending/borrowing |
| LegoEuler | Euler Finance | Lending/borrowing, isolated markets |
| LegoFluid | Fluid | Lending/borrowing/DEX |
| LegoMoonwell | Moonwell | Lending/borrowing |
| LegoMorpho | Morpho | Lending/borrowing, isolated markets |
| LegoSky | Sky/Maker | Sky PSM |

### DEX Legos

DEX legos integrate with decentralized exchanges, supporting token swaps, liquidity provision/removal, and price queries.

| Lego Name | Protocol | Key Features |
|-----------|----------|--------------|
| LegoUniswapV2 | Uniswap V2 | Constant product AMM, LP tokens |
| LegoUniswapV3 | Uniswap V3 | Concentrated liquidity, multiple fee tiers |
| LegoCurve | Curve Finance | Stablecoin-optimized AMM, various pool types |
| LegoAeroClassic | Aerodrome Classic | Base network DEX, classic pools |
| LegoAeroSlipstream | Aerodrome Slipstream | Base network DEX, slipstream pools |

## Lego Implementation Pattern

All legos follow a consistent implementation pattern:

1. **Interface Implementation**: Each lego implements the relevant interfaces (LegoCommon + protocol-specific interface)
2. **Protocol Integration**: Legos handle the specific details of interacting with their target protocol
3. **Asset Conversion**: Legos manage the conversion between user assets and protocol-specific tokens
4. **Position Tracking**: Legos track user positions and balances within the protocol
5. **Security Measures**: Legos implement security checks and validations

## Adding New Legos

The Underscore system is designed to be extensible with new lego modules. To add a new lego:

1. Identify the appropriate interface (LegoDex, LegoYield, LegoCredit)
2. Implement the interface for the target protocol
3. Register the lego with the LegoRegistry
4. Update relevant documentation and tests

## Using Legos

Legos are not directly accessed by users or agents. Instead:

1. Agents call functions on the WalletFunds contract
2. WalletFunds validates permissions and parameters
3. WalletFunds delegates the operation to the appropriate lego
4. The lego executes the operation on the target protocol
5. Results are returned through WalletFunds to the agent

For detailed information about each lego's API, including function signatures, parameters, return values, and requirements, please refer to the individual API reference documents linked above. 