import pytest
import boa

from constants import ZERO_ADDRESS
from contracts import WalletTemplate


# accounts


@pytest.fixture(scope="session")
def deploy3r(env):
    return env.eoa


@pytest.fixture(scope="session")
def governor(env):
    return env.generate_address("governor")


@pytest.fixture(scope="session")
def sally(env):
    return env.generate_address("sally")


@pytest.fixture(scope="session")
def bob(env):
    return env.generate_address("bob")


@pytest.fixture(scope="session")
def bob_agent(env):
    return env.generate_address("bob_agent")


# agentic wallets 


@pytest.fixture(scope="session")
def bob_ai_wallet(agent_factory, bob, bob_agent):
    w = agent_factory.createAgenticWallet(bob, bob_agent, sender=bob)
    assert w != ZERO_ADDRESS
    assert agent_factory.isAgenticWallet(w)
    return WalletTemplate.at(w)


# assets


@pytest.fixture(scope="session")
def alpha_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Alpha Token", "ALPHA", 18, 1_000_000, name="alpha_token")


# mock legos


@pytest.fixture(scope="session")
def mock_aave_v3_pool():
    return boa.load("contracts/mock/MockAaveV3Pool.vy", name="mock_aave_v3_pool")
