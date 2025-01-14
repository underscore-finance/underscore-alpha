import pytest
import boa

from constants import ZERO_ADDRESS


TOKENS = {
    "usdc": {
        "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "local": ZERO_ADDRESS,
    },
}

WHALES = {
    "usdc": {
        "base": "0x0B0A5886664376F59C351ba3f598C8A8B4D0A6f3",
        "local": ZERO_ADDRESS,
    },
}


# utils


def aliased(env, addr, alias):
    env.alias(addr, alias)
    return addr


def getFromEtherscan(addr, alias):
    if addr != ZERO_ADDRESS:
        return boa.from_etherscan(addr, name=alias)
    return addr


# tokens


@pytest.fixture(scope="session")
def usdc(fork):
    return getFromEtherscan(TOKENS["usdc"][fork], "usdc")


@pytest.fixture(scope="session")
def usdc_whale(env, fork):
    return aliased(env, WHALES["usdc"][fork], "usdc_whale")