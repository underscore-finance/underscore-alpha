from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Euler")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    euler = migration.deploy(
        'LegoEuler',
        blueprint.ADDYS['EULER_EVAULT_FACTORY'],
        blueprint.ADDYS['EULER_EARN_FACTORY'],
        addy_registry
    )

    migration.execute(lego_registry.registerNewLego, euler, 'Euler', LegoType.YIELD_OPP)

    tokens = [
        "USDC",
        "USDS",
        "WETH",
        "WEETH",
        "CBBTC",
        "EURC",
    ]

    for token in tokens:
        migration.execute(
            euler.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"EULER_{token}"]
        )
