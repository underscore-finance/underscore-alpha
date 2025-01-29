import pytest
import boa

from constants import MAX_UINT256


# core


@pytest.fixture(scope="session")
def addy_registry_deploy(governor):
    return boa.load("contracts/core/AddyRegistry.vy", governor, name="addy_registry")


@pytest.fixture(scope="session", autouse=True)
def addy_registry(addy_registry_deploy, lego_registry, agent_factory, agent_prices, governor):
    assert addy_registry_deploy.registerNewAddy(agent_factory, "Agent Factory", sender=governor) != 0
    assert addy_registry_deploy.registerNewAddy(lego_registry, "Lego Registry", sender=governor) != 0
    assert addy_registry_deploy.registerNewAddy(agent_prices, "Agent Prices", sender=governor) != 0
    return addy_registry_deploy


@pytest.fixture(scope="session")
def lego_registry(addy_registry_deploy):
    return boa.load("contracts/core/LegoRegistry.vy", addy_registry_deploy, name="lego_registry")


@pytest.fixture(scope="session")
def agent_factory(addy_registry_deploy, weth, wallet_template, governor):
    f = boa.load("contracts/core/AgentFactory.vy", addy_registry_deploy, weth, wallet_template, name="agent_factory")
    assert f.setNumAgenticWalletsAllowed(MAX_UINT256, sender=governor)
    return f


@pytest.fixture(scope="session")
def agent_prices(addy_registry_deploy):
    return boa.load("contracts/core/AgentPrices.vy", addy_registry_deploy, name="agent_prices")


# other


@pytest.fixture(scope="session")
def wallet_template():
    return boa.load("contracts/core/WalletTemplate.vy", name="wallet_template")


@pytest.fixture(scope="session")
def lego_helper(lego_registry, lego_aave_v3, lego_compound_v3, lego_euler, lego_fluid, lego_moonwell, lego_morpho, lego_sky, governor):
    h = boa.load(
        "contracts/core/LegoHelper.vy",
        lego_registry,
        lego_aave_v3.legoId(),
        lego_compound_v3.legoId(),
        lego_euler.legoId(),
        lego_fluid.legoId(),
        lego_moonwell.legoId(),
        lego_morpho.legoId(),
        lego_sky.legoId(),
        name="lego_helper",
    )
    assert lego_registry.setLegoHelper(h, sender=governor)
    return h

