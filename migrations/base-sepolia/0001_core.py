from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    deployer = migration.account()
    blueprint = migration.blueprint()
    log.h1("Deploying Core Contracts")

    addy_registry = migration.deploy(
        "AddyRegistry",
        deployer,
        blueprint.PARAMS["ADDY_REGISTRY_MIN_GOV_CHANGE_DELAY"],
        blueprint.PARAMS["ADDY_REGISTRY_MAX_GOV_CHANGE_DELAY"],
        blueprint.PARAMS["ADDY_REGISTRY_MIN_CHANGE_DELAY"],
        blueprint.PARAMS["ADDY_REGISTRY_MAX_CHANGE_DELAY"],
    )

    #  template contracts
    wallet_funds = migration.deploy_bp("UserWalletTemplate")
    wallet_config = migration.deploy_bp("UserWalletConfigTemplate")
    agent_template = migration.deploy_bp("AgentTemplate")

    #  factory contract
    agent_factory = migration.deploy(
        "AgentFactory",
        addy_registry,
        blueprint.CORE_TOKENS["WETH"],
        wallet_funds,
        wallet_config,
        agent_template,
        ZERO_ADDRESS,
        blueprint.PARAMS["USER_MIN_OWNER_CHANGE_DELAY"],
        blueprint.PARAMS["USER_MAX_OWNER_CHANGE_DELAY"]
    )

    #  registry contracts
    lego_registry = migration.deploy(
        'LegoRegistry',
        addy_registry,
        blueprint.PARAMS["LEGO_REGISTRY_MIN_CHANGE_DELAY"],
        blueprint.PARAMS["LEGO_REGISTRY_MAX_CHANGE_DELAY"],
    )
    oracle_registry = migration.deploy(
        'OracleRegistry',
        addy_registry,
        blueprint.ADDYS["ETH"],
        blueprint.PARAMS["ORACLE_REGISTRY_MIN_STALE_TIME"],
        blueprint.PARAMS["ORACLE_REGISTRY_MAX_STALE_TIME"],
        blueprint.PARAMS["ORACLE_REGISTRY_MIN_CHANGE_DELAY"],
        blueprint.PARAMS["ORACLE_REGISTRY_MAX_CHANGE_DELAY"],
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
    migration.execute(addy_registry.confirmNewAddy, agent_factory)

    migration.execute(addy_registry.registerNewAddy, lego_registry, "Lego Registry")
    migration.execute(addy_registry.confirmNewAddy, lego_registry)

    migration.execute(addy_registry.registerNewAddy, price_sheets, "Price Sheets")
    migration.execute(addy_registry.confirmNewAddy, price_sheets)

    migration.execute(addy_registry.registerNewAddy, oracle_registry, "Oracle Registry")
    migration.execute(addy_registry.confirmNewAddy, oracle_registry)

    migration.execute(agent_factory.setNumUserWalletsAllowed, 1000)
    migration.execute(agent_factory.setNumAgentsAllowed, 10)
    migration.execute(agent_factory.setTrialFundsData, blueprint.CORE_TOKENS["USDC"], 10_000000)
