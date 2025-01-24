# API

## Setup

```bash
pip install -r requirements.txt
```

## Run the smart contracts

1. In one terminal, run anvil:

```bash
anvil -f YOUR_BASE_RPC_URL
```

2. In another terminal, deploy the smart contracts:

```bash
python -m scripts.deploy
```

## Database preparation

### Initialize database

The first time you run the API, you need to initialize the database:

```bash
aerich init-db
```

### Create a new migration

After you make changes to the database models, you need to create a new migration:

```bash
aerich migrate --name "migration_name"
```

### Apply pending migrations

If there are pending migrations, you need to apply them:

```bash
aerich upgrade
```

## Run the API

```bash
uvicorn api.main:app --reload
```
