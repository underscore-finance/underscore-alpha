from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Morpho")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    morpho = migration.deploy(
        'LegoMorpho',
        blueprint.ADDYS['MORPHO_FACTORY'],
        blueprint.ADDYS['MORPHO_FACTORY_LEGACY'],
        addy_registry,
    )

    migration.execute(lego_registry.registerNewLego, morpho, 'Morpho', LegoType.YIELD_OPP)

    # morpho moonwell
    tokens = [
        "WETH",
        "USDC",
        "CBBTC",
        "EURC",
    ]

    for token in tokens:
        migration.execute(
            morpho.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MORPHO_MOONWELL_{token}"]
        )

    # morpho spark
    migration.execute(
        morpho.addAssetOpportunity,
        blueprint.CORE_TOKENS['USDC'],
        blueprint.YIELD_TOKENS['MORPHO_SPARK_USDC']
    )

    # morpho seamless
    tokens = [
        "USDC",
        "WETH",
        "CBBTC",
    ]

    for token in tokens:
        migration.execute(
            morpho.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MORPHO_SEAMLESS_{token}"]
        )

    # morpho gauntlet
    tokens = [
        "WETH",
        "CBBTC",
        "USDC",
        "LBTC",
        "EURC",
    ]

    for token in tokens:
        migration.execute(
            morpho.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MORPHO_GAUNTLET_{token}_CORE"]
        )
    migration.execute(
        morpho.addAssetOpportunity,
        blueprint.CORE_TOKENS['USDC'],
        blueprint.YIELD_TOKENS['MORPHO_GAUNTLET_USDC_PRIME']
    )

    # morpho steakhouse
    tokens = [
        "USDC",
        "EURC",
    ]

    for token in tokens:
        migration.execute(
            morpho.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MORPHO_STEAKHOUSE_{token}"]
        )

    # morpho 9summits
    migration.execute(
        morpho.addAssetOpportunity,
        blueprint.CORE_TOKENS['WETH'],
        blueprint.YIELD_TOKENS['MORPHO_9SUMMITS_WETH']
    )

    tokens = [
        "WETH",
        "USDC",
    ]

    # morpho re7
    for token in tokens:
        migration.execute(
            morpho.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MORPHO_RE7_{token}"]
        )

    # morpho ionic
    for token in tokens:
        migration.execute(
            morpho.addAssetOpportunity,
            blueprint.CORE_TOKENS[token],
            blueprint.YIELD_TOKENS[f"MORPHO_IONIC_{token}"]
        )
