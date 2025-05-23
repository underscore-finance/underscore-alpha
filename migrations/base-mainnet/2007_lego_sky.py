from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import LegoType


def migrate(migration: Migration):
    log.h1("Deploying Sky")

    addy_registry = migration.get_address('AddyRegistry')
    lego_registry = migration.get_contract('LegoRegistry')

    blueprint = migration.blueprint()

    sky = migration.deploy(
        'LegoSky',
        blueprint.ADDYS['SKY_PSM'],
        addy_registry
    )

    migration.execute(lego_registry.registerNewLego, sky, 'Sky', LegoType.YIELD_OPP)
    migration.execute(lego_registry.confirmNewLegoRegistration, sky)
