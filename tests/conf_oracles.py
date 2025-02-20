import pytest
import boa


# oracle partners


@pytest.fixture(scope="session")
def oracle_chainlink(oracle_registry, addy_registry, governor, fork):
    addr = boa.load("contracts/oracles/ChainlinkFeeds.vy", addy_registry, fork == "base", name="oracle_chainlink")
    assert oracle_registry.registerNewOraclePartner(addr, "Chainlink", sender=governor) != 0 # dev: invalid oracle id
    return addr


@pytest.fixture(scope="session")
def oracle_pyth(oracle_registry, addy_registry, governor, mock_pyth, fork):
    if fork == "base":
        pyth = "0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a"
    else:
        pyth = mock_pyth
    addr = boa.load("contracts/oracles/PythFeeds.vy", addy_registry, pyth, name="oracle_pyth")
    assert oracle_registry.registerNewOraclePartner(addr, "Pyth", sender=governor) != 0 # dev: invalid oracle id
    return addr


@pytest.fixture(scope="session")
def oracle_stork(oracle_registry, addy_registry, governor, mock_stork, fork):
    if fork == "base":
        stork = "0x647DFd812BC1e116c6992CB2bC353b2112176fD6"
    else:
        stork = mock_stork
    addr = boa.load("contracts/oracles/StorkFeeds.vy", addy_registry, stork, name="oracle_stork")
    assert oracle_registry.registerNewOraclePartner(addr, "Stork", sender=governor) != 0 # dev: invalid oracle id
    return addr


@pytest.fixture(scope="session")
def oracle_custom(oracle_registry, addy_registry, governor):
    addr = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="oracle_custom")
    assert oracle_registry.registerNewOraclePartner(addr, "Custom Oracle", sender=governor) != 0 # dev: invalid oracle id
    return addr