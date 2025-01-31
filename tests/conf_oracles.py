import pytest
import boa


# oracle partners


@pytest.fixture(scope="session")
def oracle_chainlink(oracle_registry, addy_registry, governor, fork):
    addr = boa.load("contracts/oracles/ChainlinkFeeds.vy", addy_registry, fork == "base", name="oracle_chainlink")
    assert oracle_registry.registerNewOraclePartner(addr, "Chainlink", sender=governor) != 0 # dev: invalid oracle id
    return addr


@pytest.fixture(scope="session")
def oracle_pyth(oracle_registry, addy_registry, governor):
    addr = boa.load("contracts/oracles/PythFeeds.vy", addy_registry, name="oracle_pyth")
    assert oracle_registry.registerNewOraclePartner(addr, "Pyth", sender=governor) != 0 # dev: invalid oracle id
    return addr


@pytest.fixture(scope="session")
def oracle_custom(oracle_registry, addy_registry, governor):
    addr = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="oracle_custom")
    assert oracle_registry.registerNewOraclePartner(addr, "Custom Oracle", sender=governor) != 0 # dev: invalid oracle id
    return addr