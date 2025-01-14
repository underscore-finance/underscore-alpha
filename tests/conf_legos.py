import pytest
import boa


# lego partners


@pytest.fixture(scope="session")
def lego_aave_v3(mock_aave_v3_pool, lego_registry, agent_factory, governor):
    addr = boa.load("contracts/legos/LegoAaveV3.vy", mock_aave_v3_pool, lego_registry, agent_factory, governor, name="lego_aave_v3")
    legoId = lego_registry.registerNewLego(addr, "Aave V3", sender=governor)
    assert legoId != 0 # dev: invalid lego id
    return addr
