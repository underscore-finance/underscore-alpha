# Underscore Core Components

This document provides a high-level overview of the core components of the Underscore system.

## Core Components

### 1. AgentTemplate

**Purpose**: Serves as the template for AI agents in the Underscore system.

**Key Responsibilities**:
- Defines actions that agents can perform (deposits, withdrawals, swaps, etc.)
- Implements signature verification for secure operations
- Manages ownership and permissions
- Executes DeFi operations on behalf of users

[Detailed API Reference](../api/AgentTemplate.md)

### 2. WalletConfig

**Purpose**: Manages wallet configuration settings and agent permissions.

**Key Responsibilities**:
- Controls agent permissions and allowlists
- Manages subscription data and payments
- Handles whitelist management for transfers
- Enforces security constraints on wallet operations

[Detailed API Reference](../api/WalletConfig.md)

### 3. WalletFunds

**Purpose**: Manages user funds and executes financial operations.

**Key Responsibilities**:
- Handles deposits and withdrawals
- Executes swaps, rebalances, and liquidity operations
- Manages borrowing and lending operations
- Ensures secure handling of user assets

[Detailed API Reference](../api/WalletFunds.md)

### 4. LegoRegistry

**Purpose**: Maintains a registry of all available DeFi protocol integrations ("legos").

**Key Responsibilities**:
- Registers and manages lego modules
- Verifies lego authenticity
- Tracks versions and updates
- Provides discovery mechanisms for available integrations

[Detailed API Reference](../api/LegoRegistry.md)

### 5. AgentFactory

**Purpose**: Creates and initializes new agent instances and user wallets.

**Key Responsibilities**:
- Creates standardized agent instances
- Initializes user wallets
- Links agents to user wallets
- Manages agent lifecycle

[Detailed API Reference](../api/AgentFactory.md)

### 6. AddyRegistry

**Purpose**: Central registry for system component addresses.

**Key Responsibilities**:
- Maintains addresses of core system components
- Provides address lookup and resolution
- Enables system-wide address updates
- Facilitates component discovery

[Detailed API Reference](../api/AddyRegistry.md)

### 7. LegoHelper

**Purpose**: Provides helper functions for lego operations.

**Key Responsibilities**:
- Offers utility functions for lego interactions
- Facilitates cross-lego operations
- Provides standardized interaction patterns
- Simplifies complex DeFi operations

[Detailed API Reference](../api/LegoHelper.md)

### 8. OracleRegistry

**Purpose**: Manages price oracles and provides price data.

**Key Responsibilities**:
- Registers and manages price oracle providers
- Provides access to price data
- Implements fallback mechanisms
- Validates price data integrity

[Detailed API Reference](../api/OracleRegistry.md)

### 9. PriceSheets

**Purpose**: Handles price data management and calculations.

**Key Responsibilities**:
- Manages price data access
- Tracks historical prices
- Provides price conversion utilities
- Calculates subscription prices

[Detailed API Reference](../api/PriceSheets.md)

## Component Relationships

### User Wallet Flow

1. **Creation**: `AgentFactory` creates a new user wallet consisting of `WalletConfig` and `WalletFunds` contracts
2. **Configuration**: `WalletConfig` is set up with initial permissions and settings
3. **Agent Setup**: `AgentTemplate` instances are created and linked to the user wallet
4. **Operations**: Agents interact with `WalletFunds` to execute DeFi operations, constrained by permissions in `WalletConfig`

### Registry Dependencies

- All components rely on `AddyRegistry` to locate other system components
- DeFi operations use `LegoRegistry` to find and validate protocol integrations
- Price data is obtained through `OracleRegistry` and `PriceSheets`
- `LegoHelper` provides utility functions that work across different legos

### Security Model

The system implements multiple security layers:
- Ownership controls with delayed transfers
- Permission-based access control
- Signature verification for agent operations
- Whitelisting for fund transfers
- Subscription enforcement
- Asset and protocol allowlists

For detailed information about each component's API, including function signatures, parameters, return values, and requirements, please refer to the individual API reference documents linked above. 