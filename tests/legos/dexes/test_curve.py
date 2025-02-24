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


# add liquidity


@pytest.always
def test_curve_add_liquidity_stable_ng(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("usdm")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x63Eb7846642630456707C3efBb50A03c79B89D81")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_add_liquidity_stable_ng_one_coin(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, _ = getTokenAndWhale("usdm")
    pool = boa.from_etherscan("0x63Eb7846642630456707C3efBb50A03c79B89D81")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, 0)


@pytest.always
def test_curve_add_liquidity_two_crypto(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 2 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("cbeth")
    amountB = 2 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_add_liquidity_two_crypto_one_coin(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 2 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, _ = getTokenAndWhale("cbeth")
    pool = boa.from_etherscan("0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, 0)


@pytest.always
def test_curve_add_liquidity_tricrypto(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("tbtc")
    amountA = int(0.1 * (10 ** tokenA.decimals()))
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x6e53131F68a034873b6bFA15502aF094Ef0c5854")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_add_liquidity_tricrypto_one_coin(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("tbtc")
    amountA = int(0.1 * (10 ** tokenA.decimals()))
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, _ = getTokenAndWhale("crvusd")
    pool = boa.from_etherscan("0x6e53131F68a034873b6bFA15502aF094Ef0c5854")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, 0)


@pytest.always
def test_curve_add_liquidity_two_crypto_ng(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 1 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("frok")
    amountB = 70_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_add_liquidity_two_crypto_ng_one_coin(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 1 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, _ = getTokenAndWhale("frok")
    pool = boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, 0)


@pytest.always
def test_curve_add_liquidity_4pool(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_add_liquidity_4pool_one_coin(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, _ = getTokenAndWhale("crvusd")
    pool = boa.from_etherscan("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f")
    testLegoLiquidityAdded(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, 0)


# remove liquidity


@pytest.always
def test_curve_remove_liquidity_stable_ng(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("usdm")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x63Eb7846642630456707C3efBb50A03c79B89D81")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_remove_liquidity_stable_ng_one_coin(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("usdm")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x63Eb7846642630456707C3efBb50A03c79B89D81")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, ZERO_ADDRESS)


@pytest.always
def test_curve_remove_liquidity_two_crypto(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 2 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("cbeth")
    amountB = 2 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_remove_liquidity_two_crypto_one_coin(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 2 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("cbeth")
    amountB = 2 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, ZERO_ADDRESS)


@pytest.always
def test_curve_remove_liquidity_tricrypto(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("tbtc")
    amountA = int(0.1 * (10 ** tokenA.decimals()))
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x6e53131F68a034873b6bFA15502aF094Ef0c5854")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_remove_liquidity_tricrypto_one_coin(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("tbtc")
    amountA = int(0.1 * (10 ** tokenA.decimals()))
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x6e53131F68a034873b6bFA15502aF094Ef0c5854")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, ZERO_ADDRESS)


@pytest.always
def test_curve_remove_liquidity_two_crypto_ng(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 1 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("frok")
    amountB = 70_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_remove_liquidity_two_crypto_ng_one_coin(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 1 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("frok")
    amountB = 70_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, ZERO_ADDRESS)


@pytest.always
def test_curve_remove_liquidity_4pool(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_curve_remove_liquidity_4pool_one_coin(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f")

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_curve, ZERO_ADDRESS, 0, pool, tokenA, ZERO_ADDRESS)