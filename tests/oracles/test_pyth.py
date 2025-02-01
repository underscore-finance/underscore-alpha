import boa
import pytest

from constants import ZERO_ADDRESS
from conf_utils import filter_logs
from conf_tokens import TOKENS


@pytest.fixture(scope="module")
def oracle_pyth(addy_registry):
    return boa.load("contracts/oracles/PythFeeds.vy", addy_registry, name="oracle_pyth")


##############
# Pyth Tests #
##############


@pytest.base
def test_set_pyth_feed(
    oracle_pyth,
    bob,
    governor,
    fork,
):
    usdc = TOKENS["usdc"][fork]
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # no perms
    with boa.reverts("no perms"):
        oracle_pyth.setPythFeed(usdc, data_feed_id, sender=bob)

    # set feed
    oracle_pyth.setPythFeed(usdc, data_feed_id, sender=governor)

    log = filter_logs(oracle_pyth, 'PythFeedAdded')[0]
    assert log.asset == usdc
    assert log.feedId == data_feed_id

    assert oracle_pyth.feedConfig(usdc) == data_feed_id
    assert int(1.02 * 10 ** 18) > oracle_pyth.getPrice(usdc) > int(0.98 * 10 ** 18)


@pytest.base
def test_disable_pyth_feed(
    oracle_pyth,
    bob,
    governor,
    fork,
):
    usdc = TOKENS["usdc"][fork]
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    oracle_pyth.setPythFeed(usdc, data_feed_id, sender=governor)
    assert oracle_pyth.getPrice(usdc) != 0

    # disable feed
    assert oracle_pyth.disablePythPriceFeed(usdc, sender=governor)

    log = filter_logs(oracle_pyth, 'PythFeedDisabled')[0]
    assert log.asset == usdc

    assert oracle_pyth.feedConfig(usdc) == bytes.fromhex("00" * 32)
    assert oracle_pyth.getPrice(usdc) == 0


# def test_local_update_prices(
#     oracle_pyth,
#     bob,
#     price_desk,
#     mock_pyth,
#     stable_bravo_raw,
#     governor,
#     fork,
# ):
#     usdc = TOKENS["usdc"][fork]
#     data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

#     # add pyth config
#     oracle_pyth.setPythFeed(stable_bravo_raw, data_feed_id, 3600, sender=governor)
#     config = oracle_pyth.feedConfig(stable_bravo_raw)
#     assert config.feedId == data_feed_id

#     # get payload
#     publish_time = boa.env.evm.patch.timestamp + 1
#     payload = mock_pyth.createPriceFeedUpdateData(
#         data_feed_id,
#         98000000,
#         50000,
#         -8,
#         publish_time,
#     )
#     exp_fee = len(payload)

#     # no perms
#     with boa.reverts():
#         oracle_pyth.updatePrices([payload], sender=bob)

#     # no balance
#     with boa.reverts():
#         oracle_pyth.updatePrices([payload], sender=price_desk.address)

#     # add eth balance
#     assert boa.env.get_balance(mock_pyth.address) == 0
#     boa.env.set_balance(oracle_pyth.address, 10 ** 18)
#     assert boa.env.get_balance(oracle_pyth.address) > exp_fee
#     pre_pyth_prices_bal = boa.env.get_balance(oracle_pyth.address)

#     # success
#     oracle_pyth.updatePrices([payload], sender=price_desk.address)
#     log = filter_logs(oracle_pyth, 'PythPriceUpdated')[0]

#     assert boa.env.get_balance(oracle_pyth.address) == pre_pyth_prices_bal - exp_fee
#     assert boa.env.get_balance(mock_pyth.address) == exp_fee

#     assert log.fromKeeper == False
#     assert log.payload == payload
#     assert log.feeAmount == exp_fee
#     assert log.propId == 0

#     # check mock pyth
#     price_data = mock_pyth.priceFeeds(data_feed_id)
#     assert price_data.price.price == 98000000
#     assert price_data.price.conf == 50000
#     assert price_data.price.expo == -8
#     assert price_data.price.publishTime == publish_time

#     assert int(0.98 * 10 ** 18) > oracle_pyth.getPrice(stable_bravo_raw) > int(0.97 * 10 ** 18)


# def test_local_deposit_with_price_updates(
#     oracle_pyth,
#     bob,
#     mock_pyth,
#     stable_bravo_raw,
#     governor,
#     stable_alpha,
#     teller_deposit,
#     simple_erc20,
#     hq,
#     price_desk,
# ):
#     data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

#     # add pyth config
#     oracle_pyth.setPythFeed(stable_bravo_raw, data_feed_id, 3600, sender=governor)
#     boa.env.set_balance(oracle_pyth.address, 10 ** 18)

#     initial_price = oracle_pyth.getPrice(stable_bravo_raw)
#     assert initial_price != 0

#     # get payload
#     publish_time = boa.env.evm.patch.timestamp + 1
#     payload = mock_pyth.createPriceFeedUpdateData(
#         data_feed_id,
#         98000000,
#         50000,
#         -8,
#         publish_time,
#     )

#     # add to price desk
#     assert price_desk.addNewPriceSource(
#         oracle_pyth, "oracle_pyth", sender=governor
#     )
#     assert oracle_pyth.priceId() != 0

#     # setup deposit
#     price_update_struct = (oracle_pyth.priceId(), [payload])
#     amount = 100 * (10 ** stable_alpha.decimals())
#     stable_alpha.mint(bob, amount, sender=hq.address)
#     stable_alpha.approve(teller_deposit, amount, sender=bob)

#     # deposit from teller
#     assert teller_deposit.depositTokens(
#         simple_erc20.stratId(),
#         stable_alpha,
#         stable_alpha,
#         amount,
#         0,
#         False,
#         0,
#         [price_update_struct],
#         sender=bob
#     ) != 0
#     assert len(filter_logs(teller_deposit, 'PythPriceUpdated')) == 1

#     # check mock pyth
#     price_data = mock_pyth.priceFeeds(data_feed_id)
#     assert price_data.price.price == 98000000
#     assert price_data.price.conf == 50000
#     assert price_data.price.expo == -8
#     assert price_data.price.publishTime == publish_time

#     # price changed
#     assert oracle_pyth.getPrice(stable_bravo_raw) != initial_price


# def test_pyth_recover_eth(
#     oracle_pyth,
#     bob,
#     governor,
# ):
#     # no balance
#     assert not oracle_pyth.recoverEthBalance(bob, sender=governor)

#     # Add ETH balance to contract
#     initial_balance = 10 ** 18  # 1 ETH
#     boa.env.set_balance(oracle_pyth.address, initial_balance)
#     assert boa.env.get_balance(oracle_pyth.address) == initial_balance

#     # No perms check
#     with boa.reverts():
#         oracle_pyth.recoverEthBalance(bob, sender=bob)

#     # Invalid recipient check
#     assert not oracle_pyth.recoverEthBalance(ZERO_ADDRESS, sender=governor)

#     # Success case
#     pre_bob_balance = boa.env.get_balance(bob)
#     oracle_pyth.recoverEthBalance(bob, sender=governor)
#     log = filter_logs(oracle_pyth, 'EthRecovered')[0]

#     # Check balances
#     assert boa.env.get_balance(oracle_pyth.address) == 0
#     assert boa.env.get_balance(bob) == pre_bob_balance + initial_balance

#     # Check event
#     assert log.recipient == bob
#     assert log.amount == initial_balance
#     assert log.propId == 0


# def test_pyth_set_keeper(
#     oracle_pyth,
#     bob,
#     alice,
#     governor,
# ):
#     # No perms check
#     with boa.reverts():
#         oracle_pyth.setKeeper(bob, sender=bob)

#     # Initial state check
#     assert oracle_pyth.keeper() == ZERO_ADDRESS

#     # Success case
#     oracle_pyth.setKeeper(bob, sender=governor)
#     log = filter_logs(oracle_pyth, 'KeeperUpdated')[0]

#     assert oracle_pyth.keeper() == bob

#     # Check event
#     assert log.keeper == bob
#     assert log.propId == 0

#     # Can update to new keeper
#     oracle_pyth.setKeeper(alice, sender=governor)
#     log = filter_logs(oracle_pyth, 'KeeperUpdated')[0]
#     assert oracle_pyth.keeper() == alice

#     assert log.keeper == alice
#     assert log.propId == 0
