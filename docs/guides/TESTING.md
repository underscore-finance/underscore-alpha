# Underscore Testing Guide

This guide provides instructions for testing the Underscore system.

## Testing Architecture

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                  pytest Framework                   │
│                                                     │
└───────────┬─────────────────────┬───────────────────┘
            │                     │
            ▼                     ▼
┌───────────────────┐   ┌──────────────────────┐
│                   │   │                      │
│  Test Categories  │   │    Test Fixtures     │
│                   │   │                      │
└─┬─────┬─────┬─────┘   └──────────────────────┘
  │     │     │                    │
  │     │     │                    ▼
  │     │     │         ┌──────────────────────┐
  │     │     │         │                      │
  │     │     │         │  Configuration Files │
  │     │     │         │                      │
  │     │     │         └──────────────────────┘
  │     │     │
  ▼     ▼     ▼
┌─────┐ ┌─────┐ ┌─────┐
│Core │ │Lego │ │Oracle│
│Tests│ │Tests│ │Tests │
└─────┘ └─────┘ └─────┘
```

## Prerequisites

- Python 3.12
- Vyper 0.4.1
- Titanoboa framework

## Test Configuration Files

The testing framework uses several configuration files:

- `tests/conftest.py`: Main pytest configuration
- `tests/conf_core.py`: Core contract test configuration
- `tests/conf_legos.py`: Lego modules test configuration
- `tests/conf_oracles.py`: Oracle integrations test configuration
- `tests/conf_mocks.py`: Mock contract test configuration
- `tests/conf_wallet.py`: Wallet test configuration

## Test Categories

### Core Tests

Tests for core contracts including:
- AgentFactory
- WalletConfig
- WalletFunds
- LegoRegistry
- AddyRegistry

**Location**: `tests/core/`

### Lego Tests

Tests for lego modules including:
- Yield legos (Aave, Compound)
- DEX legos (Uniswap, Curve)
- Credit legos

**Location**: `tests/legos/`

### Oracle Tests

Tests for oracle integrations including:
- Price feed oracles
- Oracle adapters

**Location**: `tests/oracles/`

### Wallet Tests

Tests for wallet functionality including:
- Deposit/withdrawal
- Asset management
- Security features

**Location**: `tests/wallet/`

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/core/

# Run specific test file
pytest tests/core/test_agent_factory.py

# Run specific test function
pytest tests/core/test_agent_factory.py::test_create_agent
```
