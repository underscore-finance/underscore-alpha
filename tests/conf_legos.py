import pytest
import boa

from constants import YIELD_OPP_UINT256, DEX_UINT256
from utils.BluePrint import ADDYS


#######################
# Yield Opportunities #
#######################


@pytest.fixture(scope="session")
def lego_aave_v3(fork, lego_registry, addy_registry_deploy, governor, mock_aave_v3_pool):
    AAVE_V3_POOL = mock_aave_v3_pool if fork == "local" else ADDYS[fork]["AAVE_V3_POOL"]
    AAVE_V3_ADDRESS_PROVIDER = mock_aave_v3_pool if fork == "local" else ADDYS[fork]["AAVE_V3_ADDRESS_PROVIDER"]
    addr = boa.load("contracts/legos/yield/LegoAaveV3.vy", AAVE_V3_POOL, AAVE_V3_ADDRESS_PROVIDER, addy_registry_deploy, name="lego_aave_v3")
    lego_registry.registerNewLego(addr, "Aave V3", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_fluid(mock_registry, fork, lego_registry, addy_registry_deploy, governor):
    FLUID_RESOLVER = mock_registry if fork == "local" else ADDYS[fork]["FLUID_RESOLVER"]
    addr = boa.load("contracts/legos/yield/LegoFluid.vy", FLUID_RESOLVER, addy_registry_deploy, name="lego_fluid")
    lego_registry.registerNewLego(addr, "Fluid", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_moonwell(mock_registry, fork, lego_registry, addy_registry_deploy, weth, governor):
    MOONWELL_COMPTROLLER = mock_registry if fork == "local" else ADDYS[fork]["MOONWELL_COMPTROLLER"]
    addr = boa.load("contracts/legos/yield/LegoMoonwell.vy", MOONWELL_COMPTROLLER, addy_registry_deploy, weth, name="lego_moonwell")
    lego_registry.registerNewLego(addr, "Moonwell", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_compound_v3(mock_registry, fork, lego_registry, addy_registry_deploy, governor):
    COMPOUND_V3_CONFIGURATOR = mock_registry if fork == "local" else ADDYS[fork]["COMPOUND_V3_CONFIGURATOR"]
    addr = boa.load("contracts/legos/yield/LegoCompoundV3.vy", COMPOUND_V3_CONFIGURATOR, addy_registry_deploy, name="lego_compound_v3")
    lego_registry.registerNewLego(addr, "Compound V3", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_morpho(fork, lego_registry, addy_registry_deploy, governor, mock_registry):
    MORPHO_FACTORY = mock_registry if fork == "local" else ADDYS[fork]["MORPHO_FACTORY"]
    MORPHO_FACTORY_LEGACY = mock_registry if fork == "local" else ADDYS[fork]["MORPHO_FACTORY_LEGACY"]
    addr = boa.load("contracts/legos/yield/LegoMorpho.vy", MORPHO_FACTORY, MORPHO_FACTORY_LEGACY, addy_registry_deploy, name="lego_morpho")
    lego_registry.registerNewLego(addr, "Morpho", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_euler(fork, lego_registry, addy_registry_deploy, governor, mock_registry):
    EULER_EVAULT_FACTORY = mock_registry if fork == "local" else ADDYS[fork]["EULER_EVAULT_FACTORY"]
    EULER_EARN_FACTORY = mock_registry if fork == "local" else ADDYS[fork]["EULER_EARN_FACTORY"]
    addr = boa.load("contracts/legos/yield/LegoEuler.vy", EULER_EVAULT_FACTORY, EULER_EARN_FACTORY, addy_registry_deploy, name="lego_euler")
    lego_registry.registerNewLego(addr, "Euler", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_sky(mock_registry, fork, lego_registry, addy_registry_deploy, governor):
    SKY_PSM = mock_registry if fork == "local" else ADDYS[fork]["SKY_PSM"]
    addr = boa.load("contracts/legos/yield/LegoSky.vy", SKY_PSM, addy_registry_deploy, name="lego_sky")
    lego_registry.registerNewLego(addr, "Sky", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


########
# DEXs #
########


@pytest.fixture(scope="session")
def lego_uniswap_v2(fork, lego_registry, addy_registry_deploy, governor):
    if fork == "local":
        pytest.skip("asset not relevant on this fork")
    addr = boa.load("contracts/legos/dexes/LegoUniswapV2.vy", ADDYS[fork]["UNISWAP_V2_FACTORY"], ADDYS[fork]["UNISWAP_V2_ROUTER"], addy_registry_deploy, ADDYS[fork]["UNI_V2_WETH_USDC_POOL"], name="lego_uniswap_v2")
    lego_registry.registerNewLego(addr, "Uniswap V2", DEX_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_uniswap_v3(fork, lego_registry, addy_registry_deploy, governor):
    if fork == "local":
        pytest.skip("asset not relevant on this fork")
    addr = boa.load("contracts/legos/dexes/LegoUniswapV3.vy", ADDYS[fork]["UNIV3_FACTORY"], ADDYS[fork]["UNIV3_NFT_MANAGER"], ADDYS[fork]["UNIV3_QUOTER"], addy_registry_deploy, ADDYS[fork]["UNI_V3_WETH_USDC_POOL"], name="lego_uniswap_v3")
    lego_registry.registerNewLego(addr, "Uniswap V3", DEX_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_aero_classic(fork, lego_registry, addy_registry_deploy, governor):
    if fork == "local":
        pytest.skip("asset not relevant on this fork")
    addr = boa.load("contracts/legos/dexes/LegoAeroClassic.vy", ADDYS[fork]["AERODROME_FACTORY"], ADDYS[fork]["AERODROME_ROUTER"], addy_registry_deploy, ADDYS[fork]["AERODROME_WETH_USDC_POOL"], name="lego_aero_classic")
    lego_registry.registerNewLego(addr, "aero_classic", DEX_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_aero_slipstream(fork, lego_registry, addy_registry_deploy, governor):
    if fork == "local":
        pytest.skip("asset not relevant on this fork")
    addr = boa.load("contracts/legos/dexes/LegoAeroSlipstream.vy", ADDYS[fork]["AERO_SLIPSTREAM_FACTORY"], ADDYS[fork]["AERO_SLIPSTREAM_NFT_MANAGER"], ADDYS[fork]["AERO_SLIPSTREAM_QUOTER"], addy_registry_deploy, ADDYS[fork]["AERO_SLIPSTREAM_WETH_USDC_POOL"], name="lego_aero_slipstream")
    lego_registry.registerNewLego(addr, "aero_slipstream", DEX_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="session")
def lego_curve(fork, lego_registry, addy_registry_deploy, governor):
    if fork == "local":
        pytest.skip("asset not relevant on this fork")
    addr = boa.load("contracts/legos/dexes/LegoCurve.vy", ADDYS[fork]["CURVE_ADDRESS_PROVIDER"], addy_registry_deploy, name="lego_curve")
    lego_registry.registerNewLego(addr, "Curve", DEX_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr