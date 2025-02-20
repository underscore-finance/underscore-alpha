import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256
from conf_tokens import TEST_AMOUNTS, TOKENS
from conf_utils import filter_logs


TEST_ASSETS = [
    "usdc",
    "weth",
    "tbtc",
    "frok",
    "crvusd",
]


TO_TOKEN = {
    "usdc": {
        "base": "0x59d9356e565ab3a36dd77763fc0d87feaf85508c", # usdm (stable ng)
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22", # cbeth (two crypto)
        "local": ZERO_ADDRESS,
    },
    "tbtc": {
        "base": "0x417ac0e078398c154edfadd9ef675d30be60af93", # crvusd (tricrypto)
        "local": ZERO_ADDRESS,
    },
    "frok": {
        "base": "0x4200000000000000000000000000000000000006", # weth (two crypto ng)
        "local": ZERO_ADDRESS,
    },
    "crvusd": {
        "base": "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca", # usdbc (4pool)
        "local": ZERO_ADDRESS,
    },
}


POOLS = {
    "usdc": {
        "base": "0x63Eb7846642630456707C3efBb50A03c79B89D81", # usdc/usdm (stable ng)
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59", # weth/cbeth (two crypto)
        "local": ZERO_ADDRESS,
    },
    "tbtc": {
        "base": "0x6e53131F68a034873b6bFA15502aF094Ef0c5854", # tbtc/crvusd (tricrypto)
        "local": ZERO_ADDRESS,
    },
    "frok": {
        "base": "0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569", # frok/weth (two crypto ng)
        "local": ZERO_ADDRESS,
    },
    "crvusd": {
        "base": "0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f", # crvusd/usdbc (4pool)
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
def test_curve_swap_max(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_curve.legoId(), fromAsset, toToken)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_curve_swap_partial(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_curve.legoId(), fromAsset, toToken, testAmount // 2)


@pytest.always
def test_curve_preferred_pool(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    getToToken,
    governor,
    bob_agent
):
    # setup
    fromAsset, whale = getTokenAndWhale("crvusd")
    testAmount = TEST_AMOUNTS["crvusd"] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken("crvusd")

    # set preferred pool
    four_pool = "0xf6c5f01c7f3148891ad0e19df78743d31e390d1f"
    assert lego_curve.setPreferredPools([four_pool], sender=governor)
    log = filter_logs(lego_curve, "PreferredPoolsSet")[0]
    assert log.numPools == 1

    fromSwapAmount, toAmount, usd_value = bob_ai_wallet.swapTokens(lego_curve.legoId(), fromAsset.address, toToken.address, MAX_UINT256, 0, sender=bob_agent)
    assert fromSwapAmount != 0
    assert toAmount != 0


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_curve_swap_max_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_curve.legoId(), fromAsset, toToken, MAX_UINT256, 0, pool)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_curve_swap_partial_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_curve.legoId(), fromAsset, toToken, testAmount // 2, 0, pool)