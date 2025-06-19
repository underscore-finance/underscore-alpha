from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    log.h1("Deploying LegoHelper")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    lego_helper = migration.deploy(
        'LegoHelperSepolia',
        addy_registry,
        blueprint.CORE_TOKENS['USDC'],
        blueprint.CORE_TOKENS['WETH'],
    )
    migration.execute(lego_registry.setLegoHelper, lego_helper)
