from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Compound V3")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    compound_v3 = migration.deploy(
        'LegoCompoundV3',
        blueprint.ADDYS['COMPOUND_V3_CONFIGURATOR'],
        addy_registry
    )

    migration.execute(lego_registry.registerNewLego, compound_v3, 'CompoundV3', LegoType.YIELD_OPP)
    migration.execute(lego_registry.confirmNewLegoRegistration, compound_v3)

    tokens = [
        "USDC",
        "USDBC",
        "WETH",
        "AERO",
    ]

    for token in tokens:
        migration.execute(
            compound_v3.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"COMPOUNDV3_{token}"]
        )
