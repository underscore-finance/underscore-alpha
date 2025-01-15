import pytest
import boa

from constants import ZERO_ADDRESS


LEGO_PARTNERS = {
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
}

# lego partners


@pytest.fixture(scope="session")
def lego_aave_v3(fork, mock_aave_v3_pool, lego_registry, agent_factory, governor):
    pool = LEGO_PARTNERS["aave_v3"][fork]
    if pool == ZERO_ADDRESS:
        pool = mock_aave_v3_pool
    else:
        pool = boa.from_etherscan(pool, name="aave_v3_pool")
    addr = boa.load("contracts/legos/LegoAaveV3.vy", pool, lego_registry, agent_factory, name="lego_aave_v3")
    legoId = lego_registry.registerNewLego(addr, "Aave V3", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_morpho(fork, lego_registry, agent_factory, governor, mock_morpho_factory):
    factories = LEGO_PARTNERS["morpho"][fork]

    factory = ZERO_ADDRESS
    factory_legacy = ZERO_ADDRESS
    if len(factories) == 0:
        factory = mock_morpho_factory 
        factory_legacy = mock_morpho_factory
    else:
        factory = boa.from_etherscan(factories[0], name="morpho_factory")
        factory_legacy = boa.from_etherscan(factories[1], name="morpho_factory_legacy")

    addr = boa.load("contracts/legos/LegoMorpho.vy", factory, factory_legacy, lego_registry, agent_factory, name="lego_morpho")
    legoId = lego_registry.registerNewLego(addr, "Morpho", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_fluid(fork, lego_registry, agent_factory, governor, mock_fluid_resolver):
    resolver = LEGO_PARTNERS["fluid"][fork]
    if resolver == ZERO_ADDRESS:
        resolver = mock_fluid_resolver
    else:
        resolver = boa.from_etherscan(resolver, name="fluid_resolver")
    addr = boa.load("contracts/legos/LegoFluid.vy", resolver, lego_registry, agent_factory, name="lego_fluid")
    legoId = lego_registry.registerNewLego(addr, "Fluid", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_moonwell(fork, lego_registry, agent_factory, governor, mock_compV2_comptroller):
    comptroller = LEGO_PARTNERS["moonwell"][fork]
    if comptroller == ZERO_ADDRESS:
        comptroller = mock_compV2_comptroller
    else:
        comptroller = boa.from_etherscan(comptroller, name="moonwell_comptroller")
    addr = boa.load("contracts/legos/LegoMoonwell.vy", comptroller, lego_registry, agent_factory, name="lego_moonwell")
    legoId = lego_registry.registerNewLego(addr, "Moonwell", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_compound_v3(fork, lego_registry, agent_factory, governor, mock_compV3_configurator):
    configurator = LEGO_PARTNERS["compound_v3"][fork]
    if configurator == ZERO_ADDRESS:
        configurator = mock_compV3_configurator
    else:
        configurator = boa.from_etherscan(configurator, name="compound_v3_configurator")
    addr = boa.load("contracts/legos/LegoCompoundV3.vy", configurator, lego_registry, agent_factory, name="lego_compound_v3")
    legoId = lego_registry.registerNewLego(addr, "Compound V3", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_euler(fork, lego_registry, agent_factory, governor, mock_euler_factory):
    factories = LEGO_PARTNERS["euler"][fork]

    evault_factory = ZERO_ADDRESS
    earn_factory = ZERO_ADDRESS
    if len(factories) == 0:
        evault_factory = mock_euler_factory 
        earn_factory = mock_euler_factory
    else:
        evault_factory = boa.from_etherscan(factories[0], name="euler_evault_factory")
        earn_factory = boa.from_etherscan(factories[1], name="euler_earn_factory")

    addr = boa.load("contracts/legos/LegoEuler.vy", evault_factory, earn_factory, lego_registry, agent_factory, name="lego_euler")
    legoId = lego_registry.registerNewLego(addr, "Euler", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr