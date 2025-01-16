import pytest
import boa


@pytest.fixture(scope="session")
def lego_registry(governor):
    return boa.load("contracts/core/LegoRegistry.vy", governor, name="lego_registry")


@pytest.fixture(scope="session")
def agent_factory(lego_registry, wallet_template):
    return boa.load("contracts/core/AgentFactory.vy", lego_registry, wallet_template, name="agent_factory")


@pytest.fixture(scope="session")
def wallet_template():
    return boa.load("contracts/core/WalletTemplate.vy", name="wallet_template")

