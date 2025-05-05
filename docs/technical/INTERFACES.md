# Underscore Interfaces

This document provides a high-level overview of the interfaces used in the Underscore system.

## Core Interfaces

### UserWalletInterface

**Purpose**: Defines the main interface for user wallet interactions.

**Key Responsibilities**:

- Manages token deposits and withdrawals
- Handles asset swaps and rebalancing
- Supports liquidity provision and management
- Enables borrowing and lending operations

**Implemented By**: UserWalletTemplate (WalletFunds) contract

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

**Note**: Currently, lending functionality is primarily implemented through the LegoYield interface, with LegoCredit reserved for future specialized lending protocols.

## Data Interfaces

### OraclePartnerInterface

**Purpose**: Defines functionality for oracle integrations.

**Key Responsibilities**:

- Provides price feed access
- Enables data validation
- Supports oracle-specific configurations
- Standardizes price data retrieval

**Implementation**: Integrated with OracleRegistry for accessing price data from various sources

## Interface Implementation Pattern

Interfaces in the Underscore system follow a consistent implementation pattern:

1. **Interface Definition**: Each interface is defined in a `.vyi` file in the interfaces directory
2. **Implementation Contract**: Contracts implement the interfaces by providing all required methods
3. **Interface Inheritance**: Some interfaces extend others (e.g., all legos implement LegoCommon)
4. **Standardized Interactions**: Contracts interact with each other through well-defined interfaces

## Interface Relationships

### Inheritance Hierarchy

Lego implementations inherit from multiple interfaces:

- All legos implement LegoCommon
- DEX legos additionally implement LegoDex
- Yield legos additionally implement LegoYield
- Credit legos additionally implement LegoCredit (for future specialized implementations)

### Interaction Patterns

1. **User Wallet to Legos**: The UserWalletInterface defines how the wallet interacts with various lego implementations
2. **Legos to Protocols**: Each lego interface defines how legos interact with their respective DeFi protocols
3. **System to Oracles**: The OraclePartnerInterface defines how the system obtains price data from oracle providers

### Interface Stability

The interface architecture prioritizes stability:

- Interfaces change less frequently than implementations
- New functionality is typically added through new methods or optional extensions
- Breaking changes are managed through version upgrades
- Protocol-specific details are encapsulated within implementations

## Governance and Registry Control

Interfaces are used throughout the registry system:

- LegoRegistry manages implementations of the lego interfaces
- OracleRegistry manages implementations of the oracle interface
- Interface validation occurs when registering or updating components

For detailed information about each interface, refer to the `.vyi` files in the `interfaces` directory.
