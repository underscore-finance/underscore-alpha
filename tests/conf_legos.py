import pytest
import boa

from constants import ZERO_ADDRESS


LEGO_REGISTRIES = {
    "aave_v3": {
        "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        "local": ZERO_ADDRESS,
    },
    "morpho": {
        "base": ["0xFf62A7c278C62eD665133147129245053Bbf5918", "0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101"],
        "local": [],
    },
    "fluid": {
        "base": "0x3aF6FBEc4a2FE517F56E402C65e3f4c3e18C1D86",
        "local": ZERO_ADDRESS,
    },
    "moonwell": {
        "base": "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C",
        "local": ZERO_ADDRESS,
    },
    "compound_v3": {
        "base": "0x45939657d1CA34A8FA39A924B71D28Fe8431e581",
        "local": ZERO_ADDRESS,
    },
    "euler": {
        "base": ["0x7F321498A801A191a93C840750ed637149dDf8D0", "0x72bbDB652F2AEC9056115644EfCcDd1986F51f15"],
        "local": [],
    },
    "sky": {
        "base": "0x1601843c5E9bC251A3272907010AFa41Fa18347E",
        "local": ZERO_ADDRESS,
    },
    "uniswap_v3": {
        "base": ["0x33128a8fC17869897dcE68Ed026d694621f6FDfD", "0x2626664c2603336E57B271c5C0b26F421741e481"],
        "local": [],
    },
    "uniswap_v2": {
        "base": ["0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6", "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"],
        "local": [],
    },
    "aero_classic": {
        "base": ["0x420DD381b31aEf6683db6B902084cB0FFECe40Da", "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"],
        "local": [],
    },
    "aero_slipstream": {
        "base": ["0x5e7BB104d84c7CB9B682AaC2F3d509f5F406809A", "0xBE6D8f0d05cC4be24d5167a3eF062215bE6D18a5"],
        "local": [],
    },
    "curve": {
        "base": "0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98",
        "local": ZERO_ADDRESS,
    },
}


@pytest.fixture(scope="session")
def getRegistry(mock_registry):
    def getRegistry(lego, fork, customRegistry=ZERO_ADDRESS):
        registry = LEGO_REGISTRIES[lego][fork]
        if registry == ZERO_ADDRESS:
            if customRegistry == ZERO_ADDRESS:
                registry = mock_registry
            else:
                registry = customRegistry
        else:
            registry = boa.from_etherscan(registry, name=f"{lego}_{fork}")
        return registry

    yield getRegistry


# lego partners


@pytest.fixture(scope="session")
def lego_aave_v3(getRegistry, fork, mock_aave_v3_pool, lego_registry, governor):
    pool = getRegistry("aave_v3", fork, mock_aave_v3_pool)
    addr = boa.load("contracts/legos/LegoAaveV3.vy", pool, lego_registry, name="lego_aave_v3")
    assert lego_registry.registerNewLego(addr, "Aave V3", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_fluid(getRegistry, fork, lego_registry, governor):
    registry = getRegistry("fluid", fork)
    addr = boa.load("contracts/legos/LegoFluid.vy", registry, lego_registry, name="lego_fluid")
    assert lego_registry.registerNewLego(addr, "Fluid", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_moonwell(getRegistry, fork, lego_registry, governor):
    registry = getRegistry("moonwell", fork)
    addr = boa.load("contracts/legos/LegoMoonwell.vy", registry, lego_registry, name="lego_moonwell")
    assert lego_registry.registerNewLego(addr, "Moonwell", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_compound_v3(getRegistry, fork, lego_registry, governor):
    registry = getRegistry("compound_v3", fork)
    addr = boa.load("contracts/legos/LegoCompoundV3.vy", registry, lego_registry, name="lego_compound_v3")
    assert lego_registry.registerNewLego(addr, "Compound V3", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_morpho(fork, lego_registry, governor, mock_registry):
    registries = LEGO_REGISTRIES["morpho"][fork]

    factory = mock_registry 
    factory_legacy = mock_registry
    if len(registries) != 0:
        factory = boa.from_etherscan(registries[0], name="morpho_factory")
        factory_legacy = boa.from_etherscan(registries[1], name="morpho_factory_legacy")

    addr = boa.load("contracts/legos/LegoMorpho.vy", factory, factory_legacy, lego_registry, name="lego_morpho")
    assert lego_registry.registerNewLego(addr, "Morpho", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_euler(fork, lego_registry, governor, mock_registry):
    registries = LEGO_REGISTRIES["euler"][fork]

    evault_factory = mock_registry 
    earn_factory = mock_registry
    if len(registries) != 0:
        evault_factory = boa.from_etherscan(registries[0], name="euler_evault_factory")
        earn_factory = boa.from_etherscan(registries[1], name="euler_earn_factory")

    addr = boa.load("contracts/legos/LegoEuler.vy", evault_factory, earn_factory, lego_registry, name="lego_euler")
    assert lego_registry.registerNewLego(addr, "Euler", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_sky(getRegistry, fork, lego_registry, governor):
    pool = getRegistry("sky", fork)
    addr = boa.load("contracts/legos/LegoSky.vy", pool, lego_registry, name="lego_sky")
    assert lego_registry.registerNewLego(addr, "Sky", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_uniswap_v3(fork, lego_registry, governor):
    registries = LEGO_REGISTRIES["uniswap_v3"][fork]
    if len(registries) == 0:
        pytest.skip("asset not relevant on this fork")

    factory = boa.from_etherscan(registries[0], name="uniswap_v3_factory")
    swap_router = boa.from_etherscan(registries[1], name="uniswap_v3_swap_router")
    addr = boa.load("contracts/legos/LegoUniswapV3.vy", factory, swap_router, lego_registry, name="lego_uniswap_v3")
    assert lego_registry.registerNewLego(addr, "Uniswap V3", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_uniswap_v2(fork, lego_registry, governor):
    registries = LEGO_REGISTRIES["uniswap_v2"][fork]
    if len(registries) == 0:
        pytest.skip("asset not relevant on this fork")

    factory = boa.from_etherscan(registries[0], name="uniswap_v2_factory")
    swap_router = boa.from_etherscan(registries[1], name="uniswap_v2_swap_router")
    addr = boa.load("contracts/legos/LegoUniswapV2.vy", factory, swap_router, lego_registry, name="lego_uniswap_v2")
    assert lego_registry.registerNewLego(addr, "Uniswap V2", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_aero_classic(fork, lego_registry, governor):
    registries = LEGO_REGISTRIES["aero_classic"][fork]
    if len(registries) == 0:
        pytest.skip("asset not relevant on this fork")

    factory = boa.from_etherscan(registries[0], name="aero_classic_factory")
    swap_router = boa.from_etherscan(registries[1], name="aero_classic_swap_router")
    addr = boa.load("contracts/legos/LegoAeroClassic.vy", factory, swap_router, lego_registry, name="lego_aero_classic")
    assert lego_registry.registerNewLego(addr, "aero_classic", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_aero_slipstream(fork, lego_registry, governor):
    registries = LEGO_REGISTRIES["aero_slipstream"][fork]
    if len(registries) == 0:
        pytest.skip("asset not relevant on this fork")

    factory = boa.from_etherscan(registries[0], name="aero_slipstream_factory")
    swap_router = boa.from_etherscan(registries[1], name="aero_slipstream_swap_router")
    addr = boa.load("contracts/legos/LegoAeroSlipstream.vy", factory, swap_router, lego_registry, name="lego_aero_slipstream")
    assert lego_registry.registerNewLego(addr, "aero_slipstream", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_curve(fork, lego_registry, governor):
    registry = LEGO_REGISTRIES["curve"][fork]
    if registry == ZERO_ADDRESS:
        pytest.skip("asset not relevant on this fork")
    factory = boa.from_etherscan(registry, name="curve_factory")
    addr = boa.load("contracts/legos/LegoCurve.vy", factory, lego_registry, name="lego_curve")
    assert lego_registry.registerNewLego(addr, "Curve", sender=governor) != 0 # dev: invalid lego id
    return addr