from scripts.utils import log
from scripts.utils.migration import Migration


class ChainlinkFeeds:
    USDC = "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B"
    WETH = "0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70"
    CBBTC = "0x07DA0E54543a844a80ABE69c8A12F22B3aA59f9D"
    WSTETH = "0x43a5C292A453A3bF3606fa856197f09D7B74251a"  # is ETH
    CBETH = "0xd7818272B9e248357d13057AAb0B417aF31E817d"
    AERO = "0x4EC5970fC728C5f65ba413992CD5fF6FD70fcfF0"
    EURC = "0xDAe398520e2B67cd3f27aeF9Cf14D93D927f8250"
    USDS = "0x2330aaE3bca5F05169d5f4597964D44522F62930"
    TBTC = "0x6D75BFB5A5885f841b132198C9f0bE8c872057BF"


def migrate(migration: Migration):
    log.h1("Deploying Chainlink")

    addy_registry = migration.get_address('AddyRegistry')
    oracle_registry = migration.get_contract('OracleRegistry')

    blueprint = migration.blueprint()

    chainlink_feeds = migration.deploy(
        'ChainlinkFeeds',
        blueprint.ADDYS['WETH'],
        blueprint.ADDYS['ETH'],
        blueprint.ADDYS['BTC'],
        blueprint.ADDYS['CHAINLINK_ETH_USD'],
        blueprint.ADDYS['CHAINLINK_BTC_USD'],
        addy_registry
    )

    migration.execute(oracle_registry.registerNewOraclePartner, chainlink_feeds, 'Chainlink')

    log.h2('Adding chainlink feeds to registry...')
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['USDC'], ChainlinkFeeds.USDC)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['WETH'], ChainlinkFeeds.WETH)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['CBBTC'], ChainlinkFeeds.CBBTC)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['WSTETH'], ChainlinkFeeds.WSTETH, True)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['CBETH'], ChainlinkFeeds.CBETH)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['AERO'], ChainlinkFeeds.AERO)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['EURC'], ChainlinkFeeds.EURC)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['USDS'], ChainlinkFeeds.USDS)
    migration.execute(chainlink_feeds.setChainlinkFeed, blueprint.CORE_TOKENS['TBTC'], ChainlinkFeeds.TBTC)
