import pytest
import boa

from constants import MAX_UINT256
from utils.BluePrint import PARAMS, ADDYS


# core


@pytest.fixture(scope="session")
def addy_registry_deploy(governor):
    return boa.load("contracts/core/AddyRegistry.vy", governor, name="addy_registry")


@pytest.fixture(scope="session", autouse=True)
def addy_registry(addy_registry_deploy, lego_registry, agent_factory, price_sheets, oracle_registry, governor):
    assert addy_registry_deploy.registerNewAddy(agent_factory, "Agent Factory", sender=governor) != 0 # 1
    assert addy_registry_deploy.registerNewAddy(lego_registry, "Lego Registry", sender=governor) != 0 # 2
    assert addy_registry_deploy.registerNewAddy(price_sheets, "Price Sheets", sender=governor) != 0 # 3
    assert addy_registry_deploy.registerNewAddy(oracle_registry, "Oracle Registry", sender=governor) != 0 # 4
    return addy_registry_deploy


@pytest.fixture(scope="session")
def lego_registry(addy_registry_deploy):
    return boa.load("contracts/core/LegoRegistry.vy", addy_registry_deploy, name="lego_registry")


@pytest.fixture(scope="session")
def agent_factory(addy_registry_deploy, weth, wallet_funds_template, wallet_config_template, agent_template, governor):
    f = boa.load("contracts/core/AgentFactory.vy", addy_registry_deploy, weth, wallet_funds_template, wallet_config_template, agent_template, name="agent_factory")
    assert f.setNumUserWalletsAllowed(MAX_UINT256, sender=governor)
    assert f.setNumAgentsAllowed(MAX_UINT256, sender=governor)
    return f


@pytest.fixture(scope="session")
def price_sheets(addy_registry_deploy, fork):
    return boa.load(
        "contracts/core/PriceSheets.vy",
        PARAMS[fork]["PRICES_MIN_TRIAL_PERIOD"],
        PARAMS[fork]["PRICES_MAX_TRIAL_PERIOD"],
        PARAMS[fork]["PRICES_MIN_PAY_PERIOD"],
        PARAMS[fork]["PRICES_MAX_PAY_PERIOD"],
        PARAMS[fork]["PRICES_MIN_PRICE_CHANGE_BUFFER"],
        addy_registry_deploy,
        name="price_sheets",
    )


@pytest.fixture(scope="session")
def oracle_registry(addy_registry_deploy, fork):
    ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE" if fork == "local" else ADDYS[fork]["ETH"]
    return boa.load(
        "contracts/core/OracleRegistry.vy",
        ETH,
        PARAMS[fork]["ORACLE_REGISTRY_MIN_STALE_TIME"],
        PARAMS[fork]["ORACLE_REGISTRY_MAX_STALE_TIME"],
        addy_registry_deploy,
        name="oracle_registry",
    )


# other


@pytest.fixture(scope="session")
def wallet_funds_template():
    return boa.load("contracts/core/WalletFunds.vy", name="wallet_funds_template")


@pytest.fixture(scope="session")
def wallet_config_template(fork):
    return boa.load("contracts/core/WalletConfig.vy", PARAMS[fork]["USER_MIN_OWNER_CHANGE_DELAY"], PARAMS[fork]["USER_MAX_OWNER_CHANGE_DELAY"], name="wallet_config_template")


@pytest.fixture(scope="session")
def agent_template(fork):
    return boa.load("contracts/core/AgentTemplate.vy", PARAMS[fork]["AGENT_MIN_OWNER_CHANGE_DELAY"], PARAMS[fork]["AGENT_MAX_OWNER_CHANGE_DELAY"], name="agent_template")


@pytest.fixture(scope="session")
def lego_helper(addy_registry, lego_registry, lego_aave_v3, lego_compound_v3, lego_euler, lego_fluid, lego_moonwell, lego_morpho, lego_sky, governor):
    h = boa.load(
        "contracts/core/LegoHelper.vy",
        addy_registry,
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

