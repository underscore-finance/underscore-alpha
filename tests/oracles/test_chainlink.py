import pytest
import boa

from conf_utils import filter_logs
from conf_tokens import TOKENS

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MONTH_IN_SECONDS, HOUR_IN_SECONDS


LOCAL_TOKENS = {
    "link": {
        "base": "0xd403d1624daef243fbcbd4a80d8a6f36affe32b2", # link
    },
    "btc": {
        "base": "0x3b86ad95859b6ab773f55f8d94b4b9d443ee931f", # solvBTC
    },
}

CONV_FEEDS = {
    "eth": {
        "base": "0xc5E65227fe3385B88468F9A01600017cDC9F3A12", # link/eth
    },
    "btc": {
        "base": "0xB4a1a7f260C9FF7fEd6A6fbb9fe5a9acFa725DBf", # solvBTC/btc
    },
}


USD_FEEDS = {
    "link": {
        "base": "0x17CAb8FE31E32f08326e5E27412894e49B0f9D65", # link/usd
    },
    "btc": {
        "base": "0x64c911996D3c6aC71f9b455B1E8E7266BcbD848F", # btc/usd
    },
    "usdc": {
        "base": "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", # usdc/usd
    },
}


@pytest.fixture(scope="module")
def chainlink_mock_feed():
    return boa.load("contracts/mock/MockChainlinkFeed.vy", 0, name="mock_chainlink_feed")


###################
# Chainlink Tests #
###################


@pytest.base
def test_set_chainlink_feed(
    fork,
    oracle_chainlink,
    bob,
    governor,
):
    usdc = TOKENS["usdc"][fork]
    usdc_chainlink = boa.from_etherscan(USD_FEEDS["usdc"][fork], name="usdc_chainlink")

    # no perms
    with boa.reverts("no perms"):
        oracle_chainlink.setChainlinkFeed(usdc, usdc_chainlink, sender=bob)

    # usdc
    assert oracle_chainlink.setChainlinkFeed(usdc, usdc_chainlink, sender=governor)
    log = filter_logs(oracle_chainlink, "ChainlinkFeedAdded")[0]

    # data
    config = oracle_chainlink.feedConfig(usdc)
    assert config.feed == usdc_chainlink.address
    assert config.decimals == usdc_chainlink.decimals()
    assert config.needsEthToUsd == False
    assert config.needsBtcToUsd == False

    # event
    assert log.asset == usdc
    assert log.chainlinkFeed == usdc_chainlink.address
    assert log.needsEthToUsd == False
    assert log.needsBtcToUsd == False

    # price
    assert oracle_chainlink.hasPriceFeed(usdc)
    price = oracle_chainlink.getPrice(usdc)
    assert int(1.02 * 10 ** 18) > price > int(0.98 * 10 ** 18)


@pytest.base
def test_disable_chainlink_feed(
    fork,
    oracle_chainlink,
    bob,
    governor,
):
    usdc = TOKENS["usdc"][fork]
    usdc_chainlink = boa.from_etherscan(USD_FEEDS["usdc"][fork], name="usdc_chainlink")

    # set
    assert oracle_chainlink.setChainlinkFeed(usdc, usdc_chainlink, sender=governor)
    assert oracle_chainlink.feedConfig(usdc).feed == usdc_chainlink.address
    assert oracle_chainlink.getPrice(usdc) != 0

    # no perms
    with boa.reverts("no perms"):
        oracle_chainlink.disableChainlinkPriceFeed(usdc, sender=bob)

    # cannot disable default feeds
    with boa.reverts("cannot disable default feeds"):
        oracle_chainlink.disableChainlinkPriceFeed("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", sender=governor)

    # disable
    assert oracle_chainlink.disableChainlinkPriceFeed(usdc, sender=governor)
    log = filter_logs(oracle_chainlink, "ChainlinkFeedDisabled")[0]
    assert log.asset == usdc

    assert not oracle_chainlink.hasPriceFeed(usdc)
    assert oracle_chainlink.feedConfig(usdc).feed == ZERO_ADDRESS
    assert oracle_chainlink.getPrice(usdc) == 0


@pytest.base
def test_eth_price_conversion(
    fork,
    oracle_chainlink,
    governor,
    alpha_token,
    _test,
):
    # sanity check
    assert oracle_chainlink.setChainlinkFeed(alpha_token, USD_FEEDS["link"][fork], sender=governor)
    expected_price = oracle_chainlink.getPrice(alpha_token)

    # setup link/eth price feed
    link_token = LOCAL_TOKENS["link"][fork]
    assert oracle_chainlink.setChainlinkFeed(link_token, CONV_FEEDS["eth"][fork], True, sender=governor)
    converted_price = oracle_chainlink.getPrice(link_token)

    # test if within 1% of expected price
    _test(expected_price, converted_price, 100)


@pytest.base
def test_btc_price_conversion(
    fork,
    oracle_chainlink,
    governor,
    alpha_token,
    _test,
):
    # sanity check
    assert oracle_chainlink.setChainlinkFeed(alpha_token, USD_FEEDS["btc"][fork], sender=governor)
    expected_price = oracle_chainlink.getPrice(alpha_token)

    # setup btc price feed
    btc_token = LOCAL_TOKENS["btc"][fork]
    assert oracle_chainlink.setChainlinkFeed(btc_token, CONV_FEEDS["btc"][fork], False, True, sender=governor)
    converted_price = oracle_chainlink.getPrice(btc_token)

    # test if within 2% of expected price
    _test(expected_price, converted_price, 200)


def test_chainlink_mock_feed(
    oracle_chainlink,
    chainlink_mock_feed,
    bob,
):
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS

    # setup
    time = boa.env.evm.patch.timestamp
    mock_decimals = 8
    price = 5 * (10 ** mock_decimals)
    chainlink_mock_feed.setMockData(price, 2, 2, time, time, sender=bob)

    # mock feed data
    data = chainlink_mock_feed.latestRoundData()
    assert data.answer == price
    assert data.roundId == 2
    assert data.answeredInRound == 2
    assert data.updatedAt == time
    assert data.startedAt == time

    # test
    assert oracle_chainlink.getChainlinkData(chainlink_mock_feed, mock_decimals) == 5 * EIGHTEEN_DECIMALS


def test_chainlink_stale_price(
    oracle_chainlink,
    chainlink_mock_feed,
    bob,
):
    # setup
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS
    
    # setup
    time = boa.env.evm.patch.timestamp
    mock_decimals = 8
    price = 5 * (10 ** mock_decimals)
    chainlink_mock_feed.setMockData(price, 2, 2, time, time, sender=bob)

    price = oracle_chainlink.getChainlinkData(chainlink_mock_feed, mock_decimals, HOUR_IN_SECONDS // 2)
    assert price == 5 * EIGHTEEN_DECIMALS

    # go forward an hour
    boa.env.evm.patch.timestamp += HOUR_IN_SECONDS

    # stale is half hour, return 0
    price = oracle_chainlink.getChainlinkData(chainlink_mock_feed, mock_decimals, HOUR_IN_SECONDS // 2)
    assert price == 0


def test_chainlink_zero_price(
    oracle_chainlink,
    chainlink_mock_feed,
    bob,
):
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS
    
    # test, price is zero
    chainlink_mock_feed.setMockData(0, sender=bob)
    assert oracle_chainlink.getChainlinkData(chainlink_mock_feed, 8) == 0

    # test, price is negative
    chainlink_mock_feed.setMockData(-1, sender=bob)
    assert oracle_chainlink.getChainlinkData(chainlink_mock_feed, 8) == 0

    # bad decimals
    chainlink_mock_feed.setMockData(1, sender=bob)
    assert oracle_chainlink.getChainlinkData(chainlink_mock_feed, 19) == 0
