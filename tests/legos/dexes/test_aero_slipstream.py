import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256
from conf_tokens import TEST_AMOUNTS


TEST_ASSETS = [
    "usdc",
    "weth",
    "aero",
    "cbbtc",
    "eurc",
]


TO_TOKEN = {
    "usdc": {
        "base": "0x526728DBc96689597F85ae4cd716d4f7fCcBAE9d", # msUSD (CL50)
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42", # EURC (CL100)
        "local": ZERO_ADDRESS,
    },
    "aero": {
        "base": "0x4200000000000000000000000000000000000006", # weth (CL200)
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0x236aa50979D5f3De3Bd1Eeb40E81137F22ab794b", # tbtc (CL1)
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", # usdc (CL50)
        "local": ZERO_ADDRESS,
    },
}


POOLS = {
    "usdc": {
        "base": "0x7501bc8Bb51616F79bfA524E464fb7B41f0B10fB", # msUSD (CL50)
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x5d4e504EB4c526995E0cC7A6E327FDa75D8B52b5", # EURC (CL100)
        "local": ZERO_ADDRESS,
    },
    "aero": {
        "base": "0x82321f3BEB69f503380D6B233857d5C43562e2D0", # weth (CL200)
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0x138aceE5573fA09e7F215965ff60898cc33c6330", # tbtc (CL1)
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": "0xE846373C1a92B167b4E9cd5d8E4d6B1Db9E90EC7", # usdc (CL50)
        "local": ZERO_ADDRESS,
    },
}


@pytest.fixture(scope="module")
def getToToken(fork):
    def getToToken(_token_str):
        toToken = TO_TOKEN[_token_str][fork]
        if toToken == ZERO_ADDRESS:
            pytest.skip("asset not relevant on this fork")
        return boa.from_etherscan(toToken, name=_token_str + "_to_token")

    yield getToToken


@pytest.fixture(scope="module")
def getPool(fork):
    def getPool(_token_str):
        pool = POOLS[_token_str][fork]
        if pool == ZERO_ADDRESS:
            pytest.skip("asset not relevant on this fork")
        return pool

    yield getPool



#########
# Tests #
#########


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aero_slipstream_swap_max(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_aero_slipstream.legoId(), fromAsset, toToken)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aero_slipstream_swap_partial(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_aero_slipstream.legoId(), fromAsset, toToken, testAmount // 2)



@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aero_slipstream_swap_max_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_aero_slipstream.legoId(), fromAsset, toToken, MAX_UINT256, 0, pool)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aero_slipstream_swap_partial_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_aero_slipstream.legoId(), fromAsset, toToken, testAmount // 2, 0, pool)