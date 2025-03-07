from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    deployer = migration.account()
    blueprint = migration.blueprint()
    log.h1("Deploying Core Contracts")

    addy_registry = migration.deploy("AddyRegistry", deployer)

    #  template contracts
    wallet_funds = migration.deploy("WalletFunds")
    wallet_config = migration.deploy(
        "WalletConfig",
        blueprint.PARAMS["USER_MIN_OWNER_CHANGE_DELAY"],
        blueprint.PARAMS["USER_MAX_OWNER_CHANGE_DELAY"]
    )
    agent_template = migration.deploy(
        "AgentTemplate",
        blueprint.PARAMS["AGENT_MIN_OWNER_CHANGE_DELAY"],
        blueprint.PARAMS["AGENT_MAX_OWNER_CHANGE_DELAY"]
    )

    #  factory contract
    agent_factory = migration.deploy(
        "AgentFactory",
        addy_registry,
        blueprint.CORE_TOKENS["WETH"],
        wallet_funds,
        wallet_config,
        agent_template
    )

    #  registry contracts
    lego_registry = migration.deploy('LegoRegistry', addy_registry)
    oracle_registry = migration.deploy(
        'OracleRegistry',
        blueprint.ADDYS["ETH"],
        blueprint.PARAMS["ORACLE_REGISTRY_MIN_STALE_TIME"],
        blueprint.PARAMS["ORACLE_REGISTRY_MAX_STALE_TIME"],
        addy_registry
    )
    price_sheets = migration.deploy(
        'PriceSheets',
        blueprint.PARAMS["PRICES_MIN_TRIAL_PERIOD"],
        blueprint.PARAMS["PRICES_MAX_TRIAL_PERIOD"],
        blueprint.PARAMS["PRICES_MIN_PAY_PERIOD"],
        blueprint.PARAMS["PRICES_MAX_PAY_PERIOD"],
        blueprint.PARAMS["PRICES_MIN_PRICE_CHANGE_BUFFER"],
        addy_registry
    )

    migration.execute(addy_registry.registerNewAddy, agent_factory, "Agent Factory")
    migration.execute(addy_registry.registerNewAddy, lego_registry, "Lego Registry")
    migration.execute(addy_registry.registerNewAddy, price_sheets, "Price Sheets")
    migration.execute(addy_registry.registerNewAddy, oracle_registry, "Oracle Registry")

    migration.execute(agent_factory.setNumUserWalletsAllowed, 1000)
