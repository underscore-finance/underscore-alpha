from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Aave V3")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    aave_v3 = migration.deploy(
        'LegoAaveV3',
        blueprint.ADDYS['AAVE_V3_POOL'],
        blueprint.ADDYS['AAVE_V3_ADDRESS_PROVIDER'],
        addy_registry
    )

    migration.execute(lego_registry.registerNewLego, aave_v3, 'AaveV3', LegoType.YIELD_OPP)
    migration.execute(lego_registry.confirmNewLegoRegistration, aave_v3)

    tokens = [
        "WETH",
        "CBETH",
        "USDBC",
        "WSTETH",
        "USDC",
        "WEETH",
        "CBBTC",
        "EZETH",
        "GHO",
    ]

    for token in tokens:
        migration.execute(aave_v3.addAssetOpportunity, blueprint.CORE_TOKENS[token])
