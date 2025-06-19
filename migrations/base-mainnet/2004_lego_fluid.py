from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Fluid")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    fluid = migration.deploy(
        'LegoFluid',
        blueprint.ADDYS['FLUID_RESOLVER'],
        addy_registry
    )

    migration.execute(lego_registry.registerNewLego, fluid, 'Fluid', LegoType.YIELD_OPP)
    migration.execute(lego_registry.confirmNewLegoRegistration, fluid)

    tokens = [
        "USDC",
        "WETH",
        "WSTETH",
        "EURC",
        "SUSDS",
    ]

    for token in tokens:
        migration.execute(
            fluid.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"FLUID_{token}"]
        )
