import pytest
import boa


@pytest.fixture(scope="session")
def lego_registry(governor):
    return boa.load("contracts/LegoRegistry.vy", governor, name="lego_registry")


@pytest.fixture(scope="session")
def agent_factory(lego_registry, wallet_template):
    return boa.load("contracts/AgentFactory.vy", lego_registry, wallet_template, name="agent_factory")


@pytest.fixture(scope="session")
def wallet_template():
    return boa.load("contracts/WalletTemplate.vy", name="wallet_template")

