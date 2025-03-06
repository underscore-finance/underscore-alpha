# Underscore Interfaces

This document provides a high-level overview of the interfaces used in the Underscore system.

## Core Interfaces

### UserWallet Interface

**Purpose**: Defines the main interface for user wallet interactions.

**Key Responsibilities**:
- Manages token deposits and withdrawals
- Handles asset swaps and rebalancing
- Supports liquidity provision and management
- Enables borrowing and lending operations

**Implemented By**: WalletFunds contract

### LegoCommon Interface

**Purpose**: Provides common functionality implemented by all lego modules.

**Key Responsibilities**:
- Defines standardized function signatures
- Establishes common data structures
- Provides base functionality for all legos
- Enables consistent interaction patterns

**Implemented By**: All lego modules

## Protocol-Specific Interfaces

### LegoDex Interface

**Purpose**: Defines functionality for decentralized exchange integrations.

**Key Responsibilities**:
- Enables token swaps
- Supports liquidity provision and removal
- Provides price query capabilities
- Standardizes DEX interactions

**Implemented By**: LegoUniswapV2, LegoUniswapV3, LegoCurve, LegoAeroClassic, LegoAeroSlipstream

### LegoYield Interface

**Purpose**: Defines functionality for yield-generating protocol integrations.

**Key Responsibilities**:
- Enables deposits into yield-bearing vaults
- Supports withdrawals from yield positions
- Handles reward claiming
- Standardizes yield protocol interactions

**Implemented By**: LegoAaveV3, LegoCompoundV3, LegoEuler, LegoFluid, LegoMoonwell, LegoMorpho, LegoSky

### LegoCredit Interface

**Purpose**: Defines functionality for lending/borrowing protocol integrations.

**Key Responsibilities**:
- Supports borrowing operations
- Enables repayment functionality
- Handles collateral management
- Standardizes lending protocol interactions

**Implemented By**: Credit protocol legos

## Data Interfaces

### OraclePartner Interface

**Purpose**: Defines functionality for oracle integrations.

**Key Responsibilities**:
- Provides price feed access
- Enables data validation
- Supports oracle-specific configurations
- Standardizes price data retrieval

**Implemented By**: Oracle partner implementations

## Interface Relationships

### Inheritance Hierarchy

Lego implementations inherit from multiple interfaces:
- All legos implement LegoCommon
- DEX legos additionally implement LegoDex
- Yield legos additionally implement LegoYield
- Credit legos additionally implement LegoCredit

### Interaction Patterns

1. **User Wallet to Legos**: The UserWalletInterface defines how the wallet interacts with various lego implementations
2. **Legos to Protocols**: Each lego interface defines how legos interact with their respective DeFi protocols
3. **System to Oracles**: The OraclePartnerInterface defines how the system obtains price data from oracle providers

### Extension Model

The interface architecture is designed for extensibility:
- New protocol types can be added by defining new interfaces
- Existing interfaces can be extended with new functionality
- Implementations can be updated without changing interface contracts

For detailed information about each interface's API, including function signatures, parameters, return values, and requirements, please refer to the individual API reference documents linked above. 