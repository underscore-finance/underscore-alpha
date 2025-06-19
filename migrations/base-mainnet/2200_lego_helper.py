from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    log.h1("Deploying LegoHelper")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    lego_helper = migration.deploy(
        'LegoHelper',
        addy_registry,
        blueprint.CORE_TOKENS['USDC'],
        blueprint.CORE_TOKENS['WETH'],
        # yield lego ids
        migration.get_contract('LegoAaveV3').legoId(),
        migration.get_contract('LegoCompoundV3').legoId(),
        migration.get_contract('LegoEuler').legoId(),
        migration.get_contract('LegoFluid').legoId(),
        migration.get_contract('LegoMoonwell').legoId(),
        migration.get_contract('LegoMorpho').legoId(),
        migration.get_contract('LegoSky').legoId(),
        # dex lego ids
        migration.get_contract('LegoUniswapV2').legoId(),
        migration.get_contract('LegoUniswapV3').legoId(),
        migration.get_contract('LegoAeroClassic').legoId(),
        migration.get_contract('LegoAeroSlipstream').legoId(),
        migration.get_contract('LegoCurve').legoId(),
    )
    migration.execute(lego_registry.setLegoHelper, lego_helper)
