import pytest
import boa

from constants import ZERO_ADDRESS


TOKENS = {
    "usdc": {
        "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x4200000000000000000000000000000000000006",
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
        "local": ZERO_ADDRESS,
    },
    "wsteth": {
        "base": "0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452",
        "local": ZERO_ADDRESS,
    },
    "cbeth": {
        "base": "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",
        "local": ZERO_ADDRESS,
    },
}

WHALES = {
    "usdc": {
        "base": "0x0B0A5886664376F59C351ba3f598C8A8B4D0A6f3",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
        "local": ZERO_ADDRESS,
    },
    "wsteth": {
        "base": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
        "local": ZERO_ADDRESS,
    },
    "cbeth": {
        "base": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
        "local": ZERO_ADDRESS,
    },
}


TEST_AMOUNTS = {
    "alpha": 100_000,
    "usdc": 10_000,
    "weth": 5,
    "cbbtc": 2,
    "wsteth": 5,
    "cbeth": 5,
}


# utils


def aliased(env, addr, alias):
    env.alias(addr, alias)
    return addr


def getFromEtherscan(addr, alias):
    if addr != ZERO_ADDRESS:
        return boa.from_etherscan(addr, name=alias)
    return addr


@pytest.fixture(scope="session")
def getTokenAndWhaleProd(fork, env):
    def getTokenAndWhaleProd(_token_str):
        token = TOKENS[_token_str][fork]
        whale = WHALES[_token_str][fork]
        if ZERO_ADDRESS in [token, whale]:
            pytest.skip("asset not relevant on this fork")
        return getFromEtherscan(token, _token_str), aliased(env, whale, _token_str + "_whale")

    yield getTokenAndWhaleProd


# tokens


@pytest.fixture(scope="session")
def usdc(fork):
    return getFromEtherscan(TOKENS["usdc"][fork], "usdc")


@pytest.fixture(scope="session")
def usdc_whale(env, fork):
    return aliased(env, WHALES["usdc"][fork], "usdc_whale")