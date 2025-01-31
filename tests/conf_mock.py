import pytest
import boa

from constants import ZERO_ADDRESS
from contracts.core import WalletTemplate


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


# mock asset: alpha token


@pytest.fixture(scope="session")
def alpha_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Alpha Token", "ALPHA", 18, 10_000_000, name="alpha_token")


@pytest.fixture(scope="session")
def alpha_token_whale(env, alpha_token, governor):
    whale = env.generate_address("alpha_token_whale")
    alpha_token.mint(whale, 1_000_000 * (10 ** alpha_token.decimals()), sender=governor)
    return whale


@pytest.fixture(scope="session")
def alpha_token_erc4626_vault(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault")


@pytest.fixture(scope="session")
def alpha_token_erc4626_vault_another(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault_another")


@pytest.fixture(scope="session")
def alpha_token_comp_vault(alpha_token):
    return boa.load("contracts/mock/MockCompVault.vy", alpha_token, name="alpha_comp_vault")


# mock asset: bravo token


@pytest.fixture(scope="session")
def bravo_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Bravo Token", "BRAVO", 18, 10_000_000, name="bravo_token")


@pytest.fixture(scope="session")
def bravo_token_whale(env, bravo_token, governor):
    whale = env.generate_address("bravo_token_whale")
    bravo_token.mint(whale, 1_000_000 * (10 ** bravo_token.decimals()), sender=governor)
    return whale


@pytest.fixture(scope="session")
def bravo_token_erc4626_vault(bravo_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", bravo_token, name="bravo_erc4626_vault")


# mock asset: charlie token (6 decimals)


@pytest.fixture(scope="session")
def charlie_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Charlie Token", "CHARLIE", 6, 10_000_000, name="charlie_token")


@pytest.fixture(scope="session")
def charlie_token_whale(env, charlie_token, governor):
    whale = env.generate_address("charlie_token_whale")
    charlie_token.mint(whale, 1_000_000 * (10 ** charlie_token.decimals()), sender=governor)
    return whale


# mock asset: weth


@pytest.fixture(scope="session")
def mock_weth():
    return boa.load("contracts/mock/MockWeth.vy", name="mock_weth")


# mock lego


@pytest.fixture(scope="session")
def mock_lego_alpha(alpha_token, alpha_token_erc4626_vault, lego_registry, addy_registry_deploy, governor):
    addr = boa.load("contracts/mock/MockLego.vy", alpha_token, alpha_token_erc4626_vault, addy_registry_deploy, name="mock_lego_alpha")
    legoId = lego_registry.registerNewLego(addr, "Mock Lego Alpha", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def mock_lego_alpha_another(alpha_token, alpha_token_erc4626_vault_another, lego_registry, addy_registry_deploy, governor):
    addr = boa.load("contracts/mock/MockLego.vy", alpha_token, alpha_token_erc4626_vault_another, addy_registry_deploy, name="mock_lego_alpha_another")
    legoId = lego_registry.registerNewLego(addr, "Mock Lego Alpha Another", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


# mock lego: another


@pytest.fixture(scope="session")
def mock_lego_bravo(bravo_token, bravo_token_erc4626_vault, addy_registry_deploy, lego_registry, governor):
    addr = boa.load("contracts/mock/MockLego.vy", bravo_token, bravo_token_erc4626_vault, addy_registry_deploy, name="mock_lego_bravo")
    legoId = lego_registry.registerNewLego(addr, "Mock Lego Bravo", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


# mock lego integrations


@pytest.fixture(scope="session")
def mock_registry(alpha_token_erc4626_vault, alpha_token_comp_vault):
    return boa.load("contracts/mock/MockRegistry.vy", [alpha_token_erc4626_vault, alpha_token_comp_vault], name="mock_registry")


@pytest.fixture(scope="session")
def mock_aave_v3_pool():
    return boa.load("contracts/mock/MockAaveV3Pool.vy", name="mock_aave_v3_pool")