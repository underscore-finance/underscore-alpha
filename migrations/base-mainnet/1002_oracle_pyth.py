from scripts.utils import log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    log.h1("Deploying Pyth")

    addy_registry = migration.get_address('AddyRegistry')
    oracle_registry = migration.get_contract('OracleRegistry')

    blueprint = migration.blueprint()

    pyth_feeds = migration.deploy(
        'PythFeeds',
        blueprint.ADDYS['PYTH_NETWORK'],
        addy_registry
    )

    migration.execute(oracle_registry.registerNewOraclePartner, pyth_feeds, 'Pyth')
    migration.execute(oracle_registry.confirmNewOraclePartnerRegistration, pyth_feeds)
