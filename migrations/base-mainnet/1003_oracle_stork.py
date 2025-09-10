from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    log.h1("Deploying Stork")

    addy_registry = migration.get_address('AddyRegistry')
    oracle_registry = migration.get_contract('OracleRegistry')

    blueprint = migration.blueprint()

    stork_feeds = migration.deploy(
        'StorkFeeds',
        blueprint.ADDYS['STORK_NETWORK'],
        addy_registry
    )

    migration.execute(oracle_registry.registerNewOraclePartner, stork_feeds, 'Stork')
    migration.execute(oracle_registry.confirmNewOraclePartnerRegistration, stork_feeds)
