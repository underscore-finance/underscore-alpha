from scripts.deployment.utils import deploy_contract, Tokens
from utils import log


def deploy_core(deployer):
    log.h1("Deploying core...")

    addy_registry = deploy_contract(
        'AddyRegistry',
        'contracts/core/AddyRegistry.vy',
        deployer,
    )

    wallet_template = deploy_contract(
        'WalletTemplate',
        'contracts/core/WalletTemplate.vy',
    )

    agent_factory = deploy_contract(
        'AgentFactory',
        'contracts/core/AgentFactory.vy',
        addy_registry,
        Tokens.WETH,
        wallet_template,
    )

    lego_registry = deploy_contract(
        'LegoRegistry',
        'contracts/core/LegoRegistry.vy',
        addy_registry,
    )

    oracle_registry = deploy_contract(
        'OracleRegistry',
        'contracts/core/OracleRegistry.vy',
        addy_registry,
    )

    price_sheets = deploy_contract(
        'PriceSheets',
        'contracts/core/PriceSheets.vy',
        addy_registry,
    )

    if addy_registry.isValidNewAddy(agent_factory):
        addy_registry.registerNewAddy(agent_factory, "Agent Factory")
    if addy_registry.isValidNewAddy(lego_registry):
        addy_registry.registerNewAddy(lego_registry, "Lego Registry")
    if addy_registry.isValidNewAddy(price_sheets):
        addy_registry.registerNewAddy(price_sheets, "Price Sheets")
    if addy_registry.isValidNewAddy(oracle_registry):
        addy_registry.registerNewAddy(oracle_registry, "Oracle Registry")

    if agent_factory.numAgenticWalletsAllowed() < 1000:
        agent_factory.setNumAgenticWalletsAllowed(1000)
