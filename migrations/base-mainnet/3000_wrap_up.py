from scripts.utils import log
from scripts.utils.migration import Migration


AGENT_OWNER = "0xf1A77E89a38843E95A1634A4EB16854D48d29709"


def migrate(migration: Migration):
    log.h1("Wrapping up")

    log.h1("Setting up Core Contracts delays")

    #  lego registry
    lego_registry = migration.get_contract("LegoRegistry")
    migration.execute(lego_registry.setLegoChangeDelayToMin)

    #  oracle registry
    oracle_registry = migration.get_contract("OracleRegistry")
    migration.execute(oracle_registry.setOraclePartnerChangeDelayToMin)

    addy_registry = migration.get_contract("AddyRegistry")
    migration.execute(addy_registry.setAddyChangeDelayToMin)

    agent_factory = migration.get_contract("AgentFactory")
    default_agent = migration.execute(agent_factory.createAgent, AGENT_OWNER)
    migration.execute(agent_factory.initiateDefaultAgentUpdate, default_agent)

    # TODO: Update governance
    GOV_WALLET = "0x10b990a0b0B192D76AbB199fc6fc41826041E280"
    migration.execute(addy_registry.changeGovernance, GOV_WALLET)

    # Do this after changing governance

    # (addy_registry.setGovernanceChangeDelay, blueprint.PARAMS["ADDY_REGISTRY_MIN_GOV_CHANGE_DELAY"])
