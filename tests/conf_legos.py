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
def lego_aave_v3(getRegistry, fork, mock_aave_v3_pool, lego_registry, agent_factory, governor):
    pool = getRegistry("aave_v3", fork, mock_aave_v3_pool)
    addr = boa.load("contracts/legos/LegoAaveV3.vy", pool, lego_registry, agent_factory, name="lego_aave_v3")
    assert lego_registry.registerNewLego(addr, "Aave V3", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_fluid(getRegistry, fork, lego_registry, agent_factory, governor):
    registry = getRegistry("fluid", fork)
    addr = boa.load("contracts/legos/LegoFluid.vy", registry, lego_registry, agent_factory, name="lego_fluid")
    assert lego_registry.registerNewLego(addr, "Fluid", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_moonwell(getRegistry, fork, lego_registry, agent_factory, governor):
    registry = getRegistry("moonwell", fork)
    addr = boa.load("contracts/legos/LegoMoonwell.vy", registry, lego_registry, agent_factory, name="lego_moonwell")
    assert lego_registry.registerNewLego(addr, "Moonwell", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_compound_v3(getRegistry, fork, lego_registry, agent_factory, governor):
    registry = getRegistry("compound_v3", fork)
    addr = boa.load("contracts/legos/LegoCompoundV3.vy", registry, lego_registry, agent_factory, name="lego_compound_v3")
    assert lego_registry.registerNewLego(addr, "Compound V3", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_morpho(fork, lego_registry, agent_factory, governor, mock_registry):
    registries = LEGO_REGISTRIES["morpho"][fork]

    factory = mock_registry 
    factory_legacy = mock_registry
    if len(registries) != 0:
        factory = boa.from_etherscan(registries[0], name="morpho_factory")
        factory_legacy = boa.from_etherscan(registries[1], name="morpho_factory_legacy")

    addr = boa.load("contracts/legos/LegoMorpho.vy", factory, factory_legacy, lego_registry, agent_factory, name="lego_morpho")
    assert lego_registry.registerNewLego(addr, "Morpho", sender=governor) != 0 # dev: invalid lego id
    return addr


@pytest.fixture(scope="session")
def lego_euler(fork, lego_registry, agent_factory, governor, mock_registry):
    registries = LEGO_REGISTRIES["euler"][fork]

    evault_factory = mock_registry 
    earn_factory = mock_registry
    if len(registries) != 0:
        evault_factory = boa.from_etherscan(registries[0], name="euler_evault_factory")
        earn_factory = boa.from_etherscan(registries[1], name="euler_earn_factory")

    addr = boa.load("contracts/legos/LegoEuler.vy", evault_factory, earn_factory, lego_registry, agent_factory, name="lego_euler")
    assert lego_registry.registerNewLego(addr, "Euler", sender=governor) != 0 # dev: invalid lego id
    return addr
