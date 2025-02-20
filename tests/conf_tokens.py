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
        "base": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
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
    "aero": {
        "base": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42",
        "local": ZERO_ADDRESS,
    },
    "usds": {
        "base": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc",
        "local": ZERO_ADDRESS,
    },
    "tbtc": {
        "base": "0x236aa50979d5f3de3bd1eeb40e81137f22ab794b",
        "local": ZERO_ADDRESS,
    },
    "frok": {
        "base": "0x42069babe14fb1802c5cb0f50bb9d2ad6fef55e2",
        "local": ZERO_ADDRESS,
    },
    "crvusd": {
        "base": "0x417ac0e078398c154edfadd9ef675d30be60af93",
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
    "aero": {
        "base": "0xeBf418Fe2512e7E6bd9b87a8F0f294aCDC67e6B4",
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": "0x7b2c99188D8EC7B82d6b3b3b1C1002095F1b8498",
        "local": ZERO_ADDRESS,
    },
    "usds": {
        "base": "0x1601843c5E9bC251A3272907010AFa41Fa18347E",
        "local": ZERO_ADDRESS,
    },
    "tbtc": {
        "base": "0xF2416C264Aa4068fF4D1949383366458F295F205",
        "local": ZERO_ADDRESS,
    },
    "frok": {
        "base": "0x8A160732913759Db1959C91700C8602793C46D64",
        "local": ZERO_ADDRESS,
    },
    "crvusd": {
        "base": "0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f",
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
    "aero": 25_000,
    "eurc": 10_000,
    "usds": 10_000,
    "tbtc": 2,
    "frok": 1_000,
    "crvusd": 10_000,
}


# utils


def aliased(env, addr, alias):
    env.alias(addr, alias)
    return addr


@pytest.fixture(scope="session")
def getTokenAndWhale(fork, env, alpha_token, alpha_token_whale):
    def getTokenAndWhale(_token_str):
        if _token_str == "alpha":
            if fork == "local":
                return alpha_token, alpha_token_whale
            else:
                pytest.skip("asset not relevant on this fork")

        token = TOKENS[_token_str][fork]
        whale = WHALES[_token_str][fork]
        if ZERO_ADDRESS in [token, whale]:
            pytest.skip("asset not relevant on this fork")

        return boa.from_etherscan(token, name=_token_str), aliased(env, whale, _token_str + "_whale")

    yield getTokenAndWhale


@pytest.fixture(scope="session")
def weth(fork, mock_weth):
    weth_addr = TOKENS["weth"][fork]
    if weth_addr == ZERO_ADDRESS:
        return mock_weth
    return boa.from_etherscan(weth_addr, name="weth")