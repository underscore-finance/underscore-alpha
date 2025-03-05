import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256, EIGHTEEN_DECIMALS
from conf_tokens import TEST_AMOUNTS, TOKENS
from conf_utils import filter_logs
from utils.BluePrint import CORE_TOKENS


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
    testLegoSwap(lego_curve.legoId(), fromAsset, toToken, pool)


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
    testLegoSwap(lego_curve.legoId(), fromAsset, toToken, pool, testAmount // 2)


@pytest.always
def test_curve_swap_with_routes(
    oracle_chainlink,
    getTokenAndWhale,
    bob,
    lego_curve,
    fork,
    oracle_registry,
    governor,
    _test,
):
    # tbtc setup
    tbtc, tbtc_whale = getTokenAndWhale("tbtc")
    tbtc_amount = int(0.1 * (10 ** tbtc.decimals()))
    tbtc.transfer(bob, tbtc_amount, sender=tbtc_whale)
    assert oracle_chainlink.setChainlinkFeed(tbtc, "0x6D75BFB5A5885f841b132198C9f0bE8c872057BF", sender=governor)

    # crvusd setup
    crvusd = TOKENS["crvusd"][fork]
    tbtc_crvusd = "0x6e53131f68a034873b6bfa15502af094ef0c5854"

    # usdc
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc token")
    usdc_4pool = "0xf6c5f01c7f3148891ad0e19df78743d31e390d1f"
    assert oracle_chainlink.setChainlinkFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)

    # pre balances
    pre_tbtc_bal = tbtc.balanceOf(bob)
    pre_usdc_bal = usdc.balanceOf(bob)

    # swap curve
    tbtc.approve(lego_curve, tbtc_amount, sender=bob)
    fromSwapAmount, toAmount, _, usd_value = lego_curve.swapTokens(tbtc_amount, 0, [tbtc, crvusd, usdc], [tbtc_crvusd, usdc_4pool], bob, sender=bob)
    assert toAmount != 0

    # post balances
    assert tbtc.balanceOf(bob) == pre_tbtc_bal - fromSwapAmount
    assert usdc.balanceOf(bob) == pre_usdc_bal + toAmount

    # usd values
    tbtc_input_usd_value = oracle_registry.getUsdValue(tbtc, tbtc_amount, False)
    usdc_output_usd_value = oracle_registry.getUsdValue(usdc, toAmount, False)
    _test(tbtc_input_usd_value, usdc_output_usd_value, 4_00) # 4%


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



# helper / utils


@pytest.always
def test_curve_get_best_pool(
    getTokenAndWhale,
    lego_curve,
):
    tokenA, _ = getTokenAndWhale("cbeth")
    tokenB, _ = getTokenAndWhale("weth")

    best_pool = lego_curve.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59"
    assert best_pool.fee == 3
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2

    # tricrypto
    tokenA, _ = getTokenAndWhale("crvusd")
    best_pool = lego_curve.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0x6e53131F68a034873b6bFA15502aF094Ef0c5854"
    assert best_pool.fee == 163
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 3


@pytest.always
def test_curve_get_swap_amount_out(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    tokenA, _ = getTokenAndWhale("crvusd")
    tokenB, _ = getTokenAndWhale("weth")
    amount_out = lego_curve.getSwapAmountOut("0x6e53131F68a034873b6bFA15502aF094Ef0c5854", tokenA, tokenB, 2_500 * (10 ** tokenA.decimals()))
    _test(int(0.97 * (10 ** tokenB.decimals())), amount_out, 100)

    amount_out = lego_curve.getSwapAmountOut("0x6e53131F68a034873b6bFA15502aF094Ef0c5854", tokenB, tokenA, 1 * (10 ** tokenB.decimals()))
    _test(2_450 * (10 ** tokenA.decimals()), amount_out, 100)


@pytest.always
def test_curve_get_swap_amount_out_diff_decimals(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    tokenA, _ = getTokenAndWhale("crvusd")
    tokenB, _ = getTokenAndWhale("usdc")
    amount_out = lego_curve.getSwapAmountOut("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f", tokenA, tokenB, 1_000 * (10 ** tokenA.decimals()))
    _test(1_000 * (10 ** tokenB.decimals()), amount_out, 100)

    amount_out = lego_curve.getSwapAmountOut("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f", tokenB, tokenA, 1_000 * (10 ** tokenB.decimals()))
    _test(1_000 * (10 ** tokenA.decimals()), amount_out, 100)


@pytest.always
def test_curve_get_swap_amount_in(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    tokenA, _ = getTokenAndWhale("crvusd")
    tokenB, _ = getTokenAndWhale("weth")
    amount_in = lego_curve.getSwapAmountIn("0x6e53131F68a034873b6bFA15502aF094Ef0c5854", tokenB, tokenA, 2_500 * (10 ** tokenA.decimals()))
    _test(int(1.02 * (10 ** tokenB.decimals())), amount_in, 100)

    amount_in = lego_curve.getSwapAmountIn("0x6e53131F68a034873b6bFA15502aF094Ef0c5854", tokenA, tokenB, 1 * (10 ** tokenB.decimals()))
    _test(2_555 * (10 ** tokenA.decimals()), amount_in, 100)


@pytest.always
def test_curve_get_swap_amount_in_diff_decimals(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    tokenA, _ = getTokenAndWhale("crvusd")
    tokenB, _ = getTokenAndWhale("usdc")

    # crvusd in, usdc out
    amount_in = lego_curve.getSwapAmountIn("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f", tokenA, tokenB, 1_000 * (10 ** tokenB.decimals()))
    _test(1_000 * (10 ** tokenA.decimals()), amount_in, 100)

    # usdc in, crvusd out
    amount_in = lego_curve.getSwapAmountIn("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f", tokenB, tokenA, 1_000 * (10 ** tokenA.decimals()))
    _test(1_000 * (10 ** tokenB.decimals()), amount_in, 100)


@pytest.always
def test_curve_get_add_liq_amounts_in_stable_ng(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0x63Eb7846642630456707C3efBb50A03c79B89D81")
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 20_000 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("usdm")
    amountB = 10_000 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, lp_amount = lego_curve.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 9_360 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 10_000 * (10 ** tokenB.decimals()), 1_00)
    assert lp_amount != 0

    # set new amount b
    amountB = 30_000 * (10 ** tokenB.decimals())

    # reduce amount b
    liq_amount_a, liq_amount_b, lp_amount = lego_curve.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 20_000 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 21_367 * (10 ** tokenB.decimals()), 1_00)
    assert lp_amount != 0


@pytest.always
def test_curve_get_add_liq_amounts_in_crypto_ng(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569")
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 1 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("frok")
    amountB = 70_000 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, lp_amount = lego_curve.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 1 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 69_000 * (10 ** tokenB.decimals()), 1_00)
    assert lp_amount != 0


@pytest.always
def test_curve_get_add_liq_amounts_in_two_crypto(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59")
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 2 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("cbeth")
    amountB = 2 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, lp_amount = lego_curve.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 2 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, int(1.72 * (10 ** tokenB.decimals())), 1_00)
    assert lp_amount != 0


@pytest.always
def test_curve_get_add_liq_amounts_in_tricrypto(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0x6e53131F68a034873b6bFA15502aF094Ef0c5854")
    tokenA, whaleA = getTokenAndWhale("tbtc")
    amountA = int(0.1 * (10 ** tokenA.decimals()))
    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, lp_amount = lego_curve.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, int(0.1 * (10 ** tokenA.decimals())), 1_00)
    _test(liq_amount_b, 9_189 * (10 ** tokenB.decimals()), 1_00)
    assert lp_amount != 0


@pytest.always
def test_curve_get_add_liq_amounts_in_meta_pool(
    getTokenAndWhale,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f")
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, lp_amount = lego_curve.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 3_500 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, amountB, 1_00)
    assert lp_amount != 0


@pytest.always
def test_curve_get_remove_liq_amounts_out_stable_ng(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0x63Eb7846642630456707C3efBb50A03c79B89D81")
    
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("usdm")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # calc remove liquidity
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(liq_amount_a, 9_681 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 10_318 * (10 ** tokenB.decimals()), 1_00)

    # one coin
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, ZERO_ADDRESS, liquidityAdded)
    _test(liq_amount_a, 19_998 * (10 ** tokenA.decimals()), 1_00)
    assert liq_amount_b == 0

    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, ZERO_ADDRESS, tokenB, liquidityAdded)
    assert liq_amount_a == 0
    _test(liq_amount_b, 19_999 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_curve_get_remove_liq_amounts_out_two_crypto(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59")
    
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 2 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("cbeth")
    amountB = 2 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # calc remove liquidity
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(liq_amount_a, int(2.15 * (10 ** tokenA.decimals())), 1_00)
    _test(liq_amount_b, int(1.85 * (10 ** tokenB.decimals())), 1_00)

    # one coin
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, ZERO_ADDRESS, liquidityAdded)
    _test(liq_amount_a, int(4.18 * (10 ** tokenA.decimals())), 1_00)
    assert liq_amount_b == 0

    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, ZERO_ADDRESS, tokenB, liquidityAdded)
    assert liq_amount_a == 0
    _test(liq_amount_b, int(3.83 * (10 ** tokenB.decimals())), 1_00)


@pytest.always
def test_curve_get_remove_liq_amounts_out_tricrypto(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0x6e53131F68a034873b6bFA15502aF094Ef0c5854")
    
    # setup
    tokenA, whaleA = getTokenAndWhale("tbtc")
    amountA = int(0.1 * (10 ** tokenA.decimals()))
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # calc remove liquidity
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    assert liq_amount_a == MAX_UINT256
    assert liq_amount_b == MAX_UINT256

    # one coin
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, ZERO_ADDRESS, liquidityAdded)
    _test(liq_amount_a, int(0.203 * (10 ** tokenA.decimals())), 1_00)
    assert liq_amount_b == 0

    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, ZERO_ADDRESS, tokenB, liquidityAdded)
    assert liq_amount_a == 0
    _test(liq_amount_b, 18_796 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_curve_get_remove_liq_amounts_out_crypto_ng(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569")
    
    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 1 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("frok")
    amountB = 70_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # calc remove liquidity
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(liq_amount_a, 1 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 69_695 * (10 ** tokenB.decimals()), 1_00)

    # one coin
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, ZERO_ADDRESS, liquidityAdded)
    _test(liq_amount_a, int(1.48 * (10 ** tokenA.decimals())), 1_00)
    assert liq_amount_b == 0

    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, ZERO_ADDRESS, tokenB, liquidityAdded)
    assert liq_amount_a == 0
    _test(liq_amount_b, 103_001 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_curve_get_remove_liq_amounts_out_4pool(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_curve,
    _test,
):
    pool = boa.from_etherscan("0xf6C5F01C7F3148891ad0e19DF78743D31E390D1f")
    
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("crvusd")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    tokenA.approve(lego_curve.address, amountA, sender=bob_ai_wallet.address)
    tokenB.approve(lego_curve.address, amountB, sender=bob_ai_wallet.address)
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = lego_curve.addLiquidity(0, pool, tokenA.address, tokenB.address, 0, 0, amountA, amountB, 0, 0, 0, bob_ai_wallet.address, sender=bob_ai_wallet.address)

    # calc remove liquidity
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    assert liq_amount_a == MAX_UINT256
    assert liq_amount_b == MAX_UINT256

    # one coin
    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, tokenA, ZERO_ADDRESS, liquidityAdded)
    _test(liq_amount_a, 19_955 * (10 ** tokenA.decimals()), 1_00)
    assert liq_amount_b == 0

    liq_amount_a, liq_amount_b = lego_curve.getRemoveLiqAmountsOut(pool, ZERO_ADDRESS, tokenB, liquidityAdded)
    assert liq_amount_a == 0
    _test(liq_amount_b, 20_037 * (10 ** tokenB.decimals()), 1_00)
