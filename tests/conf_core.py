import pytest
import boa

from constants import MAX_UINT256
from utils.BluePrint import PARAMS, ADDYS, CORE_TOKENS


# core


@pytest.fixture(scope="session")
def addy_registry_deploy(governor, fork):
    min_gov_delay = PARAMS[fork]["ADDY_REGISTRY_MIN_GOV_CHANGE_DELAY"]
    max_gov_delay = PARAMS[fork]["ADDY_REGISTRY_MAX_GOV_CHANGE_DELAY"]
    min_change_delay = PARAMS[fork]["ADDY_REGISTRY_MIN_CHANGE_DELAY"]
    max_change_delay = PARAMS[fork]["ADDY_REGISTRY_MAX_CHANGE_DELAY"]
    return boa.load("contracts/core/registries/AddyRegistry.vy", governor, min_gov_delay, max_gov_delay, min_change_delay, max_change_delay, name="addy_registry")


@pytest.fixture(scope="session", autouse=True)
def addy_registry(addy_registry_deploy, lego_registry, agent_factory, price_sheets, oracle_registry, governor):
    delay = addy_registry_deploy.addyChangeDelay()

    assert addy_registry_deploy.registerNewAddy(agent_factory, "Agent Factory", sender=governor) # 1
    boa.env.time_travel(blocks=delay + 1)
    assert addy_registry_deploy.confirmNewAddy(agent_factory, sender=governor) != 0

    assert addy_registry_deploy.registerNewAddy(lego_registry, "Lego Registry", sender=governor) # 2
    boa.env.time_travel(blocks=delay + 1)
    assert addy_registry_deploy.confirmNewAddy(lego_registry, sender=governor) != 0

    assert addy_registry_deploy.registerNewAddy(price_sheets, "Price Sheets", sender=governor) # 3
    boa.env.time_travel(blocks=delay + 1)
    assert addy_registry_deploy.confirmNewAddy(price_sheets, sender=governor) != 0

    assert addy_registry_deploy.registerNewAddy(oracle_registry, "Oracle Registry", sender=governor) # 4
    boa.env.time_travel(blocks=delay + 1)
    assert addy_registry_deploy.confirmNewAddy(oracle_registry, sender=governor) != 0

    return addy_registry_deploy


@pytest.fixture(scope="session")
def lego_registry(addy_registry_deploy, fork):
    min_delay = PARAMS[fork]["LEGO_REGISTRY_MIN_CHANGE_DELAY"]
    max_delay = PARAMS[fork]["LEGO_REGISTRY_MAX_CHANGE_DELAY"]
    return boa.load("contracts/core/registries/LegoRegistry.vy", addy_registry_deploy, min_delay, max_delay, name="lego_registry")


@pytest.fixture(scope="session")
def agent_factory(addy_registry_deploy, weth, wallet_funds_template, wallet_config_template, agent_template, governor, fork, agent):
    min_owner_change_delay = PARAMS[fork]["USER_MIN_OWNER_CHANGE_DELAY"]
    max_owner_change_delay = PARAMS[fork]["USER_MAX_OWNER_CHANGE_DELAY"]
    f = boa.load("contracts/core/AgentFactory.vy", addy_registry_deploy, weth, wallet_funds_template, wallet_config_template, agent_template, agent, min_owner_change_delay, max_owner_change_delay, name="agent_factory")
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
        "contracts/core/registries/OracleRegistry.vy",
        addy_registry_deploy,
        ETH,
        PARAMS[fork]["ORACLE_REGISTRY_MIN_STALE_TIME"],
        PARAMS[fork]["ORACLE_REGISTRY_MAX_STALE_TIME"],
        PARAMS[fork]["ORACLE_REGISTRY_MIN_CHANGE_DELAY"],
        PARAMS[fork]["ORACLE_REGISTRY_MAX_CHANGE_DELAY"],
        name="oracle_registry",
    )


# templates


@pytest.fixture(scope="session")
def wallet_funds_template():
    return boa.load_partial("contracts/core/templates/UserWalletTemplate.vy").deploy_as_blueprint()


@pytest.fixture(scope="session")
def wallet_config_template():
    return boa.load_partial("contracts/core/templates/UserWalletConfigTemplate.vy").deploy_as_blueprint()


@pytest.fixture(scope="session")
def agent_template():
    return boa.load_partial("contracts/core/templates/AgentTemplate.vy").deploy_as_blueprint()


# other


@pytest.fixture(scope="session")
def lego_helper(
    addy_registry,
    lego_registry,
    lego_aave_v3,
    lego_compound_v3,
    lego_euler,
    lego_fluid,
    lego_moonwell,
    lego_morpho,
    lego_sky,
    lego_uniswap_v2,
    lego_uniswap_v3,
    lego_aero_classic,
    lego_aero_slipstream,
    lego_curve,
    governor,
    fork,
    alpha_token,
    mock_weth,
):
    usdc = alpha_token
    weth = mock_weth
    if fork != "local":
        usdc = CORE_TOKENS[fork]["USDC"]
        weth = CORE_TOKENS[fork]["WETH"]

    h = boa.load(
        "contracts/legos/LegoHelper.vy",
        addy_registry,
        usdc,
        weth,
        lego_aave_v3.legoId(),
        lego_compound_v3.legoId(),
        lego_euler.legoId(),
        lego_fluid.legoId(),
        lego_moonwell.legoId(),
        lego_morpho.legoId(),
        lego_sky.legoId(),
        lego_uniswap_v2.legoId(),
        lego_uniswap_v3.legoId(),
        lego_aero_classic.legoId(),
        lego_aero_slipstream.legoId(),
        lego_curve.legoId(),
        name="lego_helper",
    )
    assert lego_registry.setLegoHelper(h, sender=governor)
    return h

