from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Moonwell")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    moonwell = migration.deploy(
        'LegoMoonwell',
        blueprint.ADDYS['MOONWELL_COMPTROLLER'],
        addy_registry,
        blueprint.CORE_TOKENS['WETH']
    )

    migration.execute(lego_registry.registerNewLego, moonwell, 'Moonwell', LegoType.YIELD_OPP)

    tokens = [
        "WETH",
        "USDC",
        "CBBTC",
        "AERO",
        "WSTETH",
        "CBETH",
        "WEETH",
        "EURC",
        "WELL",
        "RETH",
        "LBTC",
        "WRSETH",
        "VIRTUAL",
        "TBTC",
        "DAI",
        "USDS",
    ]

    for token in tokens:
        migration.execute(
            moonwell.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MOONWELL_{token}"]
        )
