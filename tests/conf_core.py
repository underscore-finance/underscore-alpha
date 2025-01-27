import pytest
import boa

from constants import MAX_UINT256


@pytest.fixture(scope="session")
def lego_registry(governor):
    return boa.load("contracts/core/LegoRegistry.vy", governor, name="lego_registry")


@pytest.fixture(scope="session")
def agent_factory(lego_registry, weth, wallet_template, governor):
    f = boa.load("contracts/core/AgentFactory.vy", lego_registry, weth, wallet_template, name="agent_factory")
    assert f.setNumAgenticWalletsAllowed(MAX_UINT256, sender=governor)
    return f


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

