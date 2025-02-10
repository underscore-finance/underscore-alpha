
from scripts.deployment.utils import deploy_contract, get_contract, Tokens
from utils import log


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


def deploy_oracles():
    log.h1("Deploying oracles...")

    addy_registry = get_contract('AddyRegistry')
    oracle_registry = get_contract('OracleRegistry')

    log.h2("Deploying chainlink feeds...")

    chainlink_feeds = deploy_contract(
        'ChainlinkFeeds',
        'contracts/oracles/ChainlinkFeeds.vy',
        addy_registry,
        True,
    )
    if oracle_registry.isValidNewOraclePartnerAddr(chainlink_feeds):
        oracle_registry.registerNewOraclePartner(chainlink_feeds, 'Chainlink')

    log.h2('Adding chainlink feeds to registry...')

    if not chainlink_feeds.hasPriceFeed(Tokens.USDC):
        chainlink_feeds.setChainlinkFeed(Tokens.USDC, ChainlinkFeeds.USDC)
    if not chainlink_feeds.hasPriceFeed(Tokens.WETH):
        chainlink_feeds.setChainlinkFeed(Tokens.WETH, ChainlinkFeeds.WETH)
    if not chainlink_feeds.hasPriceFeed(Tokens.CBBTC):
        chainlink_feeds.setChainlinkFeed(Tokens.CBBTC, ChainlinkFeeds.CBBTC)
    if not chainlink_feeds.hasPriceFeed(Tokens.WSTETH):
        chainlink_feeds.setChainlinkFeed(Tokens.WSTETH, ChainlinkFeeds.WSTETH, True)
    if not chainlink_feeds.hasPriceFeed(Tokens.CBETH):
        chainlink_feeds.setChainlinkFeed(Tokens.CBETH, ChainlinkFeeds.CBETH)
    if not chainlink_feeds.hasPriceFeed(Tokens.AERO):
        chainlink_feeds.setChainlinkFeed(Tokens.AERO, ChainlinkFeeds.AERO)
    if not chainlink_feeds.hasPriceFeed(Tokens.EURC):
        chainlink_feeds.setChainlinkFeed(Tokens.EURC, ChainlinkFeeds.EURC)
    if not chainlink_feeds.hasPriceFeed(Tokens.USDS):
        chainlink_feeds.setChainlinkFeed(Tokens.USDS, ChainlinkFeeds.USDS)
    if not chainlink_feeds.hasPriceFeed(Tokens.TBTC):
        chainlink_feeds.setChainlinkFeed(Tokens.TBTC, ChainlinkFeeds.TBTC)

    log.h2("Deploying pyth feeds...")

    pyth_feeds = deploy_contract(
        'PythFeeds',
        'contracts/oracles/PythFeeds.vy',
        addy_registry,
        '0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a',
    )
    if oracle_registry.isValidNewOraclePartnerAddr(pyth_feeds):
        oracle_registry.registerNewOraclePartner(pyth_feeds, 'Pyth')
