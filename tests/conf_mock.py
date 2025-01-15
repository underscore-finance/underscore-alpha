import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
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


# mock assets


@pytest.fixture(scope="session")
def alpha_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Alpha Token", "ALPHA", 18, 1_000_000, name="alpha_token")


@pytest.fixture(scope="session")
def alpha_token_whale(env, alpha_token, governor):
    whale = env.generate_address("alpha_token_whale")
    alpha_token.mint(whale, 100_000 * EIGHTEEN_DECIMALS, sender=governor)
    return whale


@pytest.fixture(scope="session")
def alpha_token_erc4626_vault(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault")


@pytest.fixture(scope="session")
def alpha_token_compV2_vault(alpha_token):
    return boa.load("contracts/mock/MockCompV2Vault.vy", alpha_token, name="alpha_compV2_vault")


# mock lego integrations


@pytest.fixture(scope="session")
def mock_aave_v3_pool():
    return boa.load("contracts/mock/MockAaveV3Pool.vy", name="mock_aave_v3_pool")


@pytest.fixture(scope="session")
def mock_morpho_factory():
    return boa.load("contracts/mock/MockMorphoFactory.vy", name="mock_morpho_factory")


@pytest.fixture(scope="session")
def mock_fluid_resolver(alpha_token_erc4626_vault):
    return boa.load("contracts/mock/MockFluidResolver.vy", alpha_token_erc4626_vault, name="mock_fluid_resolver")


@pytest.fixture(scope="session")
def mock_compV2_comptroller(alpha_token_compV2_vault):
    return boa.load("contracts/mock/MockCompV2Comptroller.vy", alpha_token_compV2_vault, name="mock_compV2_comptroller")
