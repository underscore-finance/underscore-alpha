from scripts.utils import log
from scripts.utils.migration import Migration


AGENT_OWNER = "0xf1A77E89a38843E95A1634A4EB16854D48d29709"


def migrate(migration: Migration):
    log.h1("Wrapping up")

    log.h1("Setting up Core Contracts delays")

    agent_factory = migration.get_contract("AgentFactory")
    default_agent = migration.execute(agent_factory.createAgent, AGENT_OWNER)
    migration.execute(agent_factory.initiateDefaultAgentUpdate, default_agent)
