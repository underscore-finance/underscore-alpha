from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying DeXes")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    aerodrome_classic = migration.deploy(
        'LegoAeroClassic',
        blueprint.ADDYS['AERODROME_FACTORY'],
        blueprint.ADDYS['AERODROME_ROUTER'],
        addy_registry,
        blueprint.ADDYS['AERODROME_WETH_USDC_POOL']
    )
    migration.execute(lego_registry.registerNewLego, aerodrome_classic, 'Aero Classic', LegoType.DEX)
    migration.execute(lego_registry.confirmNewLegoRegistration, aerodrome_classic)

    aerodrome_slipstream = migration.deploy(
        'LegoAeroSlipstream',
        blueprint.ADDYS['AERO_SLIPSTREAM_FACTORY'],
        blueprint.ADDYS['AERO_SLIPSTREAM_NFT_MANAGER'],
        blueprint.ADDYS['AERO_SLIPSTREAM_QUOTER'],
        addy_registry,
        blueprint.ADDYS['AERO_SLIPSTREAM_WETH_USDC_POOL']
    )
    migration.execute(lego_registry.registerNewLego, aerodrome_slipstream, 'Aero Slipstream', LegoType.DEX)
    migration.execute(lego_registry.confirmNewLegoRegistration, aerodrome_slipstream)

    curve = migration.deploy(
        'LegoCurve',
        blueprint.ADDYS['CURVE_ADDRESS_PROVIDER'],
        addy_registry,
    )
    migration.execute(lego_registry.registerNewLego, curve, 'Curve', LegoType.DEX)
    migration.execute(lego_registry.confirmNewLegoRegistration, curve)

    uniswap_v2 = migration.deploy(
        'LegoUniswapV2',
        blueprint.ADDYS['UNISWAP_V2_FACTORY'],
        blueprint.ADDYS['UNISWAP_V2_ROUTER'],
        addy_registry,
        blueprint.ADDYS['UNI_V2_WETH_USDC_POOL']
    )
    migration.execute(lego_registry.registerNewLego, uniswap_v2, 'Uniswap V2', LegoType.DEX)
    migration.execute(lego_registry.confirmNewLegoRegistration, uniswap_v2)

    uniswap_v3 = migration.deploy(
        'LegoUniswapV3',
        blueprint.ADDYS['UNIV3_FACTORY'],
        blueprint.ADDYS['UNIV3_NFT_MANAGER'],
        blueprint.ADDYS['UNIV3_QUOTER'],
        addy_registry,
        blueprint.ADDYS['UNI_V3_WETH_USDC_POOL']
    )
    migration.execute(lego_registry.registerNewLego, uniswap_v3, 'Uniswap V3', LegoType.DEX)
    migration.execute(lego_registry.confirmNewLegoRegistration, uniswap_v3)
