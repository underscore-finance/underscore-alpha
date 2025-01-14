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
