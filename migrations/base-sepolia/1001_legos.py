from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying YieldLego")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    yield_lego = migration.deploy(
        'MockLego',
        addy_registry
    )
    migration.execute(lego_registry.registerNewLego, yield_lego, 'YieldLego', LegoType.YIELD_OPP)
    migration.execute(lego_registry.confirmNewLegoRegistration, yield_lego)

    tokens = [
        "WETH",
        "CBBTC",
        "USDC",
    ]
    for token in tokens:
        migration.execute(yield_lego.addAssetOpportunity,
                          blueprint.CORE_TOKENS[token], blueprint.YIELD_TOKENS[f"{token}_VAULT"])
