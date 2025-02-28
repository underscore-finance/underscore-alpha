import boa
import pytest

from constants import ZERO_ADDRESS, MONTH_IN_SECONDS
from conf_utils import filter_logs
from conf_tokens import TOKENS
from utils.BluePrint import ADDYS


@pytest.fixture(scope="session")
def new_oracle_pyth(addy_registry, mock_pyth, fork):
    PYTH_NETWORK = mock_pyth if fork == "local" else ADDYS[fork]["PYTH_NETWORK"]
    return boa.load("contracts/oracles/PythFeeds.vy", PYTH_NETWORK, addy_registry, name="new_oracle_pyth")


##############
# Pyth Tests #
##############


@pytest.base
def test_set_pyth_feed(
    new_oracle_pyth,
    bob,
    governor,
    fork,
):
    usdc = TOKENS["usdc"][fork]
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # no perms
    with boa.reverts("no perms"):
        new_oracle_pyth.setPythFeed(usdc, data_feed_id, sender=bob)

    # set feed
    new_oracle_pyth.setPythFeed(usdc, data_feed_id, sender=governor)

    log = filter_logs(new_oracle_pyth, 'PythFeedAdded')[0]
    assert log.asset == usdc
    assert log.feedId == data_feed_id

    assert new_oracle_pyth.feedConfig(usdc) == data_feed_id
    assert int(1.02 * 10 ** 18) > new_oracle_pyth.getPrice(usdc) > int(0.98 * 10 ** 18)


@pytest.base
def test_disable_pyth_feed(
    new_oracle_pyth,
    governor,
    fork,
):
    usdc = TOKENS["usdc"][fork]
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    new_oracle_pyth.setPythFeed(usdc, data_feed_id, sender=governor)
    assert new_oracle_pyth.getPrice(usdc) != 0

    # disable feed
    assert new_oracle_pyth.disablePythPriceFeed(usdc, sender=governor)

    log = filter_logs(new_oracle_pyth, 'PythFeedDisabled')[0]
    assert log.asset == usdc

    assert new_oracle_pyth.feedConfig(usdc) == bytes.fromhex("00" * 32)
    assert new_oracle_pyth.getPrice(usdc) == 0


def test_local_update_prices(
    new_oracle_pyth,
    mock_pyth,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    new_oracle_pyth.setPythFeed(alpha_token, data_feed_id, sender=governor)
    assert new_oracle_pyth.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )
    exp_fee = len(payload)

    # no balance
    with boa.reverts():
        new_oracle_pyth.updatePythPrices([payload], sender=governor)

    # add eth balance
    assert boa.env.get_balance(mock_pyth.address) == 0
    boa.env.set_balance(new_oracle_pyth.address, 10 ** 18)
    assert boa.env.get_balance(new_oracle_pyth.address) > exp_fee
    pre_pyth_prices_bal = boa.env.get_balance(new_oracle_pyth.address)

    # success
    new_oracle_pyth.updatePythPrices([payload], sender=governor)

    log = filter_logs(new_oracle_pyth, 'PythPriceUpdated')[0]
    assert log.payload == payload
    assert log.feeAmount == exp_fee
    assert log.caller == governor

    assert boa.env.get_balance(new_oracle_pyth.address) == pre_pyth_prices_bal - exp_fee
    assert boa.env.get_balance(mock_pyth.address) == exp_fee

    # check mock pyth
    price_data = mock_pyth.priceFeeds(data_feed_id)
    assert price_data.price.price == 98000000
    assert price_data.price.conf == 50000
    assert price_data.price.expo == -8
    assert price_data.price.publishTime == publish_time

    assert int(0.98 * 10 ** 18) > new_oracle_pyth.getPrice(alpha_token) > int(0.97 * 10 ** 18)


def test_pyth_recover_eth(
    new_oracle_pyth,
    bob,
    governor,
):
    # no balance
    assert not new_oracle_pyth.recoverEthBalance(bob, sender=governor)

    # Add ETH balance to contract
    initial_balance = 10 ** 18  # 1 ETH
    boa.env.set_balance(new_oracle_pyth.address, initial_balance)
    assert boa.env.get_balance(new_oracle_pyth.address) == initial_balance

    # No perms check
    with boa.reverts():
        new_oracle_pyth.recoverEthBalance(bob, sender=bob)

    # Invalid recipient check
    assert not new_oracle_pyth.recoverEthBalance(ZERO_ADDRESS, sender=governor)

    # Success case
    pre_bob_balance = boa.env.get_balance(bob)
    new_oracle_pyth.recoverEthBalance(bob, sender=governor)
    log = filter_logs(new_oracle_pyth, 'EthRecoveredFromPyth')[0]

    # Check balances
    assert boa.env.get_balance(new_oracle_pyth.address) == 0
    assert boa.env.get_balance(bob) == pre_bob_balance + initial_balance

    # Check event
    assert log.recipient == bob
    assert log.amount == initial_balance


@pytest.mark.parametrize(
    'price, conf, expo, expected_price',
    [
        (99995021, 56127, -8, int(0.99995021 * 10**18) - int(56127 * 10**(-8) * 10**18)),  # Normal case
        (0, 56127, -8, 0),  # Zero price
        (-1, 56127, -8, 0), # Negative price
        (99995021, 99995021, -8, 0), # confidence == price
        (99995021, 99995022, -8, 0), # confidence > price
        (99995021, 56127, 0, int(99995021 * 10**18) - int(56127 * 10**(0) * 10**18)),   # Zero exponent
        (99995021, 56127, 1, int(99995021 * 10**19) - int(56127 * 10**(1) * 10**18)),   # Positive exponent
    ]
)
def test_get_price(
    new_oracle_pyth,
    mock_pyth,
    alpha_token,
    governor,
    price,
    conf,
    expo,
    expected_price
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    new_oracle_pyth.setPythFeed(alpha_token, data_feed_id, sender=governor)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        price,
        conf,
        expo,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(new_oracle_pyth.address, 10 ** 18)

    # success update price
    new_oracle_pyth.updatePythPrices([payload], sender=governor)

    assert new_oracle_pyth.getPrice(alpha_token) == expected_price


def test_get_price_stale(
    new_oracle_pyth,
    mock_pyth,
    alpha_token,
    governor,
):
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS

    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    new_oracle_pyth.setPythFeed(alpha_token, data_feed_id, sender=governor)
    assert new_oracle_pyth.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp - 3601 # 1 hour and 1 second ago, > stale time (3600s)
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(new_oracle_pyth.address, 10 ** 18)

    # success update price
    new_oracle_pyth.updatePythPrices([payload], sender=governor)

    # price should be 0 due to staleness
    assert new_oracle_pyth.getPrice(alpha_token, 3600) == 0


def test_get_price_and_has_feed(
    new_oracle_pyth,
    mock_pyth,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # no feed set
    price, has_feed = new_oracle_pyth.getPriceAndHasFeed(alpha_token)
    assert price == 0
    assert not has_feed

    # set feed
    new_oracle_pyth.setPythFeed(alpha_token, data_feed_id, sender=governor)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(new_oracle_pyth.address, 10 ** 18)

    # success update price
    new_oracle_pyth.updatePythPrices([payload], sender=governor)

    # has feed set
    price, has_feed = new_oracle_pyth.getPriceAndHasFeed(alpha_token)
    assert price != 0
    assert has_feed


def test_has_price_feed(
    new_oracle_pyth,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # no feed set
    assert not new_oracle_pyth.hasPriceFeed(alpha_token)

    # set feed
    new_oracle_pyth.setPythFeed(alpha_token, data_feed_id, sender=governor)

    # has feed set
    assert new_oracle_pyth.hasPriceFeed(alpha_token)


def test_update_pyth_prices_insufficient_balance(
    new_oracle_pyth,
    mock_pyth,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    new_oracle_pyth.setPythFeed(alpha_token, data_feed_id, sender=governor)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )

    boa.env.set_balance(new_oracle_pyth.address, 1)

    # no balance
    with boa.reverts("insufficient balance"):
        new_oracle_pyth.updatePythPrices([payload], sender=governor)


def test_is_valid_pyth_feed(
    new_oracle_pyth,
    alpha_token,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    invalid_feed_id = bytes.fromhex("f" * 64)

    # valid feed
    assert new_oracle_pyth.isValidPythFeed(alpha_token, data_feed_id)

    # invalid feed id
    assert not new_oracle_pyth.isValidPythFeed(alpha_token, invalid_feed_id)

    # invalid asset
    assert not new_oracle_pyth.isValidPythFeed(ZERO_ADDRESS, data_feed_id)


def test_set_pyth_feed_invalid(
    new_oracle_pyth,
    bob,
    governor,
    alpha_token,
):
    invalid_feed_id = bytes.fromhex("f" * 64)

    # invalid feed id
    assert not new_oracle_pyth.setPythFeed(alpha_token, invalid_feed_id, sender=governor)
    assert new_oracle_pyth.feedConfig(alpha_token) == bytes.fromhex("00" * 32)

    # invalid asset
    assert not new_oracle_pyth.setPythFeed(ZERO_ADDRESS, invalid_feed_id, sender=governor)
    assert new_oracle_pyth.feedConfig(ZERO_ADDRESS) == bytes.fromhex("00" * 32)


def test_disable_pyth_feed_invalid(
    new_oracle_pyth,
    governor,
    alpha_token,
):
    # no feed set
    assert not new_oracle_pyth.disablePythPriceFeed(alpha_token, sender=governor)

    # already disabled
    new_oracle_pyth.disablePythPriceFeed(alpha_token, sender=governor)
    assert not new_oracle_pyth.disablePythPriceFeed(alpha_token, sender=governor)


def test_is_valid_eth_recovery(
    new_oracle_pyth,
    bob,
):
    # invalid balance
    assert not new_oracle_pyth.isValidEthRecovery(bob)

    # valid recovery
    boa.env.set_balance(new_oracle_pyth.address, 10 ** 18)
    assert new_oracle_pyth.isValidEthRecovery(bob)

    # invalid recipient
    assert not new_oracle_pyth.isValidEthRecovery(ZERO_ADDRESS)


def test_recover_eth_balance_invalid(
    new_oracle_pyth,
    bob,
    governor,
):
    # Invalid recipient check
    assert not new_oracle_pyth.recoverEthBalance(ZERO_ADDRESS, sender=governor)

    # no balance
    assert not new_oracle_pyth.recoverEthBalance(bob, sender=governor)
