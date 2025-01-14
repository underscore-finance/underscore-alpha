import pytest
import boa

from constants import ZERO_ADDRESS


LEGO_PARTNERS = {
    "aave_v3": {
        "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
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
