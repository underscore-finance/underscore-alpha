# Underscore Deployment Guide

This guide provides instructions for deploying the Underscore system.

## Deployment Architecture

```
┌─────────────────────┐
│                     │
│     deploy.py       │
│  (Main Orchestrator)│
│                     │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│                                                  │
│               Deployment Modules                 │
│                                                  │
├──────────────┬──────────────┬───────────────────┤
│              │              │                   │
│   core.py    │  oracles.py  │     legos.py      │
│              │              │                   │
└──────────────┴──────────────┴───────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│                                                  │
│                 Target Network                   │
│                                                  │
└──────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- Vyper 0.4.1+
- Boa framework
- Access to target network (RPC URL)
- Deployer account with sufficient funds

## Environment Setup

1. Create a `.env` file with the following variables:

```
# Network
UNDY_RPC_URL=https://your-rpc-url.com

# Accounts
DEPLOYER_PRIVATE_KEY=your-private-key

# Optional: Contract verification
ETHERSCAN_API_KEY=your-etherscan-api-key
```

## Deployment Process

### 1. Basic Deployment

To deploy the entire system with default settings:

```bash
# Deploy all components
python scripts/deploy.py
```

### 2. Component-Specific Deployment

To deploy specific components:

```bash
# Deploy only core contracts
python scripts/deploy.py --core-only

# Deploy only oracle integrations
python scripts/deploy.py --oracles-only

# Deploy only lego modules
python scripts/deploy.py --legos-only
```

### 3. Network-Specific Deployment

```bash
# Deploy to mainnet
python scripts/deploy.py --network mainnet

# Deploy to testnet
python scripts/deploy.py --network goerli

# Deploy to local network
python scripts/deploy.py --network local
```

## Deployment Sequence

The system deploys contracts in the following order:

1. **Core Registry Contracts**
   - AddyRegistry
   - LegoRegistry
   - OracleRegistry
   - PriceSheets

2. **Core Functional Contracts**
   - AgentFactory
   - LegoHelper

3. **Oracle Integrations**
   - Oracle adapters
   - Oracle providers

4. **Lego Modules**
   - Yield legos
   - DEX legos
   - Credit legos
