from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    log.h1("Deploying Agent Factory")

    addy_registry = migration.get_contract("AddyRegistry")

    #  template contracts
    wallet_funds = migration.get_contract("WalletFunds")
    wallet_config = migration.get_contract("WalletConfig")
    agent_template = migration.get_contract("AgentTemplate")

    #  factory contract
    migration.deploy(
        "AgentFactory",
        addy_registry,
        blueprint.CORE_TOKENS["WETH"],
        wallet_funds,
        wallet_config,
        agent_template
    )
