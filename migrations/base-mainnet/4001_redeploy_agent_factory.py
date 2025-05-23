from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    log.h1("Re-deploying Agent Factory")

    blueprint = migration.blueprint()
    addy_registry = migration.get_address("AddyRegistry")
    wallet_funds = migration.get_address("UserWalletTemplate")
    wallet_config = migration.get_address("UserWalletConfigTemplate")
    agent_template = migration.get_address("AgentTemplate")
    agent_factory = migration.get_contract("AgentFactory")
    default_agent = agent_factory.getDefaultAgentAddr()

    #  factory contract
    agent_factory = migration.deploy(
        "AgentFactory",
        addy_registry,
        blueprint.CORE_TOKENS["WETH"],
        wallet_funds,
        wallet_config,
        agent_template,
        default_agent,
        blueprint.PARAMS["USER_MIN_OWNER_CHANGE_DELAY"],
        blueprint.PARAMS["USER_MAX_OWNER_CHANGE_DELAY"]
    )
