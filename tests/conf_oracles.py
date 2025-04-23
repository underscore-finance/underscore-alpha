import pytest
import boa

from utils.BluePrint import ADDYS
from constants import ZERO_ADDRESS


# oracle partners


@pytest.fixture(scope="session")
def oracle_chainlink(oracle_registry, addy_registry, governor, fork, weth):
    ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE" if fork == "local" else ADDYS[fork]["ETH"]
    BTC = "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB" if fork == "local" else ADDYS[fork]["BTC"]
    CHAINLINK_ETH_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_ETH_USD"]
    CHAINLINK_BTC_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_BTC_USD"]
    addr = boa.load("contracts/oracles/ChainlinkFeeds.vy", weth, ETH, BTC, CHAINLINK_ETH_USD, CHAINLINK_BTC_USD, addy_registry, name="oracle_chainlink")
    assert oracle_registry.registerNewOraclePartner(addr, "Chainlink", sender=governor)
    boa.env.time_travel(blocks=oracle_registry.oracleChangeDelay() + 1)
    assert oracle_registry.confirmNewOraclePartnerRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def oracle_pyth(oracle_registry, addy_registry, governor, mock_pyth, fork):
    PYTH_NETWORK = mock_pyth if fork == "local" else ADDYS[fork]["PYTH_NETWORK"]
    addr = boa.load("contracts/oracles/PythFeeds.vy", PYTH_NETWORK, addy_registry, name="oracle_pyth")
    assert oracle_registry.registerNewOraclePartner(addr, "Pyth", sender=governor)
    boa.env.time_travel(blocks=oracle_registry.oracleChangeDelay() + 1)
    assert oracle_registry.confirmNewOraclePartnerRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def oracle_stork(oracle_registry, addy_registry, governor, mock_stork, fork):
    STORK_NETWORK = mock_stork if fork == "local" else ADDYS[fork]["STORK_NETWORK"]
    addr = boa.load("contracts/oracles/StorkFeeds.vy", STORK_NETWORK, addy_registry, name="oracle_stork")
    assert oracle_registry.registerNewOraclePartner(addr, "Stork", sender=governor)
    boa.env.time_travel(blocks=oracle_registry.oracleChangeDelay() + 1)
    assert oracle_registry.confirmNewOraclePartnerRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def oracle_custom(oracle_registry, addy_registry, governor):
    addr = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="oracle_custom")
    assert oracle_registry.registerNewOraclePartner(addr, "Custom Oracle", sender=governor)
    boa.env.time_travel(blocks=oracle_registry.oracleChangeDelay() + 1)
    assert oracle_registry.confirmNewOraclePartnerRegistration(addr, sender=governor) != 0
    return addr