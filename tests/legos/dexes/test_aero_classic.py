import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256
from conf_tokens import TEST_AMOUNTS


TEST_ASSETS = [
    "usdc",
    "weth",
    "aero",
    "cbbtc",
]


TO_TOKEN = {
    "usdc": {
        "base": "0x526728DBc96689597F85ae4cd716d4f7fCcBAE9d", # msUSD (sAMM)
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x7Ba6F01772924a82D9626c126347A28299E98c98", # msETH (sAMM)
        "local": ZERO_ADDRESS,
    },
    "aero": {
        "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", # USDC (vAMM)
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b", # VIRTUAL (vAMM)
        "local": ZERO_ADDRESS,
    },
}


POOLS = {
    "usdc": {
        "base": "0xcEFC8B799a8EE5D9b312aeca73262645D664AaF7", # msUSD/usdc (sAMM)
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0xDE4FB30cCC2f1210FcE2c8aD66410C586C8D1f9A", # msETH/weth (sAMM)
        "local": ZERO_ADDRESS,
    },
    "aero": {
        "base": "0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d", # USDC/aero (vAMM)
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0xb909F567c5c2Bb1A4271349708CC4637D7318b4A", # VIRTUAL/cbbtc (vAMM)
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
def test_aerodrome_classic_swap_max(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_aero_classic.legoId(), fromAsset, toToken)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aerodrome_classic_swap_partial(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_aero_classic.legoId(), fromAsset, toToken, testAmount // 2)



@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aerodrome_classic_swap_max_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_aero_classic.legoId(), fromAsset, toToken, MAX_UINT256, 0, pool)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aerodrome_classic_swap_partial_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_aero_classic.legoId(), fromAsset, toToken, testAmount // 2, 0, pool)