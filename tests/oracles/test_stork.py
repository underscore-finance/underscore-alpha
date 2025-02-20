import boa
import pytest

from constants import ZERO_ADDRESS, MONTH_IN_SECONDS
from conf_utils import filter_logs
from conf_tokens import TOKENS


@pytest.fixture(scope="session")
def new_oracle_stork(addy_registry, mock_stork, fork):
    if fork == "base":
        stork = "0x647DFd812BC1e116c6992CB2bC353b2112176fD6"
    else:
        stork = mock_stork
    return boa.load("contracts/oracles/StorkFeeds.vy", addy_registry, stork, name="new_oracle_stork")


###############
# Stork Tests #
###############


@pytest.base
def test_set_stork_feed(
    new_oracle_stork,
    bob,
    governor,
    fork,
):
    cbbtc = TOKENS["cbbtc"][fork]
    data_feed_id = bytes.fromhex("7404e3d104ea7841c3d9e6fd20adfe99b4ad586bc08d8f3bd3afef894cf184de") # btc

    # no perms
    with boa.reverts("no perms"):
        new_oracle_stork.setStorkFeed(cbbtc, data_feed_id, sender=bob)

    # set feed
    new_oracle_stork.setStorkFeed(cbbtc, data_feed_id, sender=governor)

    log = filter_logs(new_oracle_stork, 'StorkFeedAdded')[0]
    assert log.asset == cbbtc
    assert log.feedId == data_feed_id

    assert new_oracle_stork.feedConfig(cbbtc) == data_feed_id
    assert int(102_000 * 10 ** 18) > new_oracle_stork.getPrice(cbbtc) > int(97_000 * 10 ** 18)


@pytest.base
def test_disable_stork_feed(
    new_oracle_stork,
    governor,
    fork,
):
    cbbtc = TOKENS["cbbtc"][fork]
    data_feed_id = bytes.fromhex("7404e3d104ea7841c3d9e6fd20adfe99b4ad586bc08d8f3bd3afef894cf184de") # btc
    new_oracle_stork.setStorkFeed(cbbtc, data_feed_id, sender=governor)
    assert new_oracle_stork.getPrice(cbbtc) != 0

    # disable feed
    assert new_oracle_stork.disableStorkPriceFeed(cbbtc, sender=governor)

    log = filter_logs(new_oracle_stork, 'StorkFeedDisabled')[0]
    assert log.asset == cbbtc

    assert new_oracle_stork.feedConfig(cbbtc) == bytes.fromhex("00" * 32)
    assert new_oracle_stork.getPrice(cbbtc) == 0


def test_local_update_prices(
    new_oracle_stork,
    mock_stork,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    new_oracle_stork.setStorkFeed(alpha_token, data_feed_id, sender=governor)
    assert new_oracle_stork.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        998888888000000000,
        publish_time,
    )
    exp_fee = len(payload)

    # no balance
    with boa.reverts():
        new_oracle_stork.updateStorkPrices([payload], sender=governor)

    # add eth balance
    assert boa.env.get_balance(mock_stork.address) == 0
    boa.env.set_balance(new_oracle_stork.address, 10 ** 18)
    assert boa.env.get_balance(new_oracle_stork.address) > exp_fee
    pre_stork_prices_bal = boa.env.get_balance(new_oracle_stork.address)

    # success
    new_oracle_stork.updateStorkPrices([payload], sender=governor)

    log = filter_logs(new_oracle_stork, 'StorkPriceUpdated')[0]
    assert log.payload == payload
    assert log.feeAmount == exp_fee
    assert log.caller == governor

    assert boa.env.get_balance(new_oracle_stork.address) == pre_stork_prices_bal - exp_fee
    assert boa.env.get_balance(mock_stork.address) == exp_fee

    # check mock stork
    price_data = mock_stork.priceFeeds(data_feed_id)
    assert price_data.quantizedValue == 998888888000000000
    assert price_data.timestampNs == publish_time * 1_000_000_000

    assert int(1 * 10 ** 18) > new_oracle_stork.getPrice(alpha_token) > int(0.97 * 10 ** 18)


def test_stork_recover_eth(
    new_oracle_stork,
    bob,
    governor,
):
    # no balance
    assert not new_oracle_stork.recoverEthBalance(bob, sender=governor)

    # Add ETH balance to contract
    initial_balance = 10 ** 18  # 1 ETH
    boa.env.set_balance(new_oracle_stork.address, initial_balance)
    assert boa.env.get_balance(new_oracle_stork.address) == initial_balance

    # No perms check
    with boa.reverts():
        new_oracle_stork.recoverEthBalance(bob, sender=bob)

    # Invalid recipient check
    assert not new_oracle_stork.recoverEthBalance(ZERO_ADDRESS, sender=governor)

    # Success case
    pre_bob_balance = boa.env.get_balance(bob)
    new_oracle_stork.recoverEthBalance(bob, sender=governor)
    log = filter_logs(new_oracle_stork, 'EthRecoveredFromStork')[0]

    # Check balances
    assert boa.env.get_balance(new_oracle_stork.address) == 0
    assert boa.env.get_balance(bob) == pre_bob_balance + initial_balance

    # Check event
    assert log.recipient == bob
    assert log.amount == initial_balance


@pytest.mark.parametrize(
    'price, expected_price',
    [
        (990000000000000000, 990000000000000000),  # Normal case
        (0, 0),  # Zero price
    ]
)
def test_get_price(
    new_oracle_stork,
    mock_stork,
    alpha_token,
    governor,
    price,
    expected_price
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    new_oracle_stork.setStorkFeed(alpha_token, data_feed_id, sender=governor)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        price,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(new_oracle_stork.address, 10 ** 18)

    # success update price
    new_oracle_stork.updateStorkPrices([payload], sender=governor)

    assert new_oracle_stork.getPrice(alpha_token) == expected_price


def test_get_price_stale(
    new_oracle_stork,
    mock_stork,
    alpha_token,
    governor,
):
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS

    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    new_oracle_stork.setStorkFeed(alpha_token, data_feed_id, sender=governor)
    assert new_oracle_stork.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp - 3601 # 1 hour and 1 second ago, > stale time (3600s)
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        990000000000000000,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(new_oracle_stork.address, 10 ** 18)

    # success update price
    new_oracle_stork.updateStorkPrices([payload], sender=governor)

    # price should be 0 due to staleness
    assert new_oracle_stork.getPrice(alpha_token, 3600) == 0


def test_get_price_and_has_feed(
    new_oracle_stork,
    mock_stork,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # no feed set
    price, has_feed = new_oracle_stork.getPriceAndHasFeed(alpha_token)
    assert price == 0
    assert not has_feed

    # set feed
    new_oracle_stork.setStorkFeed(alpha_token, data_feed_id, sender=governor)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        990000000000000000,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(new_oracle_stork.address, 10 ** 18)

    # success update price
    new_oracle_stork.updateStorkPrices([payload], sender=governor)

    # has feed set
    price, has_feed = new_oracle_stork.getPriceAndHasFeed(alpha_token)
    assert price != 0
    assert has_feed


def test_has_price_feed(
    new_oracle_stork,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # no feed set
    assert not new_oracle_stork.hasPriceFeed(alpha_token)

    # set feed
    new_oracle_stork.setStorkFeed(alpha_token, data_feed_id, sender=governor)

    # has feed set
    assert new_oracle_stork.hasPriceFeed(alpha_token)


def test_update_stork_prices_insufficient_balance(
    new_oracle_stork,
    mock_stork,
    alpha_token,
    governor,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    new_oracle_stork.setStorkFeed(alpha_token, data_feed_id, sender=governor)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        990000000000000000,
        publish_time,
    )

    boa.env.set_balance(new_oracle_stork.address, 1)

    # no balance
    with boa.reverts("insufficient balance"):
        new_oracle_stork.updateStorkPrices([payload], sender=governor)


def test_is_valid_stork_feed(
    new_oracle_stork,
    alpha_token,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    invalid_feed_id = bytes.fromhex("f" * 64)

    # valid feed
    assert new_oracle_stork.isValidStorkFeed(alpha_token, data_feed_id)

    # invalid feed id
    assert not new_oracle_stork.isValidStorkFeed(alpha_token, invalid_feed_id)

    # invalid asset
    assert not new_oracle_stork.isValidStorkFeed(ZERO_ADDRESS, data_feed_id)


def test_set_stork_feed_invalid(
    new_oracle_stork,
    bob,
    governor,
    alpha_token,
):
    invalid_feed_id = bytes.fromhex("f" * 64)

    # invalid feed id
    assert not new_oracle_stork.setStorkFeed(alpha_token, invalid_feed_id, sender=governor)
    assert new_oracle_stork.feedConfig(alpha_token) == bytes.fromhex("00" * 32)

    # invalid asset
    assert not new_oracle_stork.setStorkFeed(ZERO_ADDRESS, invalid_feed_id, sender=governor)
    assert new_oracle_stork.feedConfig(ZERO_ADDRESS) == bytes.fromhex("00" * 32)


def test_disable_stork_feed_invalid(
    new_oracle_stork,
    governor,
    alpha_token,
):
    # no feed set
    assert not new_oracle_stork.disableStorkPriceFeed(alpha_token, sender=governor)

    # already disabled
    new_oracle_stork.disableStorkPriceFeed(alpha_token, sender=governor)
    assert not new_oracle_stork.disableStorkPriceFeed(alpha_token, sender=governor)


def test_is_valid_eth_recovery(
    new_oracle_stork,
    bob,
):
    # invalid balance
    assert not new_oracle_stork.isValidEthRecovery(bob)

    # valid recovery
    boa.env.set_balance(new_oracle_stork.address, 10 ** 18)
    assert new_oracle_stork.isValidEthRecovery(bob)

    # invalid recipient
    assert not new_oracle_stork.isValidEthRecovery(ZERO_ADDRESS)


def test_recover_eth_balance_invalid(
    new_oracle_stork,
    bob,
    governor,
):
    # Invalid recipient check
    assert not new_oracle_stork.recoverEthBalance(ZERO_ADDRESS, sender=governor)

    # no balance
    assert not new_oracle_stork.recoverEthBalance(bob, sender=governor)
