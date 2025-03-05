import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256, EIGHTEEN_DECIMALS
from conf_tokens import TEST_AMOUNTS
from utils.BluePrint import CORE_TOKENS


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
    testLegoSwap(lego_aero_classic.legoId(), fromAsset, toToken, pool)


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
    testLegoSwap(lego_aero_classic.legoId(), fromAsset, toToken, pool, testAmount // 2)


@pytest.always
def test_aerodrom_classic_swap_with_routes(
    oracle_chainlink,
    getTokenAndWhale,
    bob,
    lego_aero_classic,
    fork,
    oracle_registry,
    governor,
    _test,
):
    # usdc setup
    usdc, usdc_whale = getTokenAndWhale("usdc")
    usdc_amount = 10_000 * (10 ** usdc.decimals())
    usdc.transfer(bob, usdc_amount, sender=usdc_whale)
    assert oracle_chainlink.setChainlinkFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)

    # weth setup
    weth = CORE_TOKENS[fork]["WETH"]
    weth_usdc_pool = "0xcDAC0d6c6C59727a65F871236188350531885C43"

    # virtual setup
    virtual = boa.from_etherscan(CORE_TOKENS[fork]["VIRTUAL"], name="virtual token")
    weth_virtual_pool = "0x21594b992F68495dD28d605834b58889d0a727c7"
    virtual_price = lego_aero_classic.getPriceUnsafe(weth_virtual_pool, virtual)

    # pre balances
    pre_usdc_bal = usdc.balanceOf(bob)
    pre_virtual_bal = virtual.balanceOf(bob)

    # swap aerodrome classic
    usdc.approve(lego_aero_classic, usdc_amount, sender=bob)
    fromSwapAmount, toAmount, _, usd_value = lego_aero_classic.swapTokens(usdc_amount, 0, [usdc, weth, virtual], [weth_usdc_pool, weth_virtual_pool], bob, sender=bob)
    assert toAmount != 0

    # post balances
    assert usdc.balanceOf(bob) == pre_usdc_bal - fromSwapAmount
    assert virtual.balanceOf(bob) == pre_virtual_bal + toAmount

    # usd values
    usdc_input_usd_value = oracle_registry.getUsdValue(usdc, usdc_amount, False)
    virtual_output_usd_value = virtual_price * toAmount // (10 ** virtual.decimals())
    _test(usdc_input_usd_value, virtual_output_usd_value, 2_00) # 2%


# add liquidity


@pytest.always
def test_aerodrome_classic_add_liquidity_more_token_A_volatile(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("aero")
    amountB = 1_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d")
    testLegoLiquidityAdded(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, amountB)


@pytest.always
def test_aerodrome_classic_add_liquidity_more_token_B_volatile(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 1_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("aero")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d")
    testLegoLiquidityAdded(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, amountB)


@pytest.always
def test_aerodrome_classic_add_liquidity_more_token_A_stable(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("dola")
    amountB = 1_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xf213F2D02837012dC0236cC105061e121bB03e37")
    testLegoLiquidityAdded(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, amountB)


@pytest.always
def test_aerodrome_classic_add_liquidity_more_token_B_stable(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 1_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("dola")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xf213F2D02837012dC0236cC105061e121bB03e37")
    testLegoLiquidityAdded(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, amountB)


# remove liquidity


@pytest.always
def test_aerodrome_classic_remove_liq_max_volatile(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    bob_agent,
):
    legoId = lego_aero_classic.legoId()
    pool = boa.from_etherscan("0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("aero")
    amountB = 11_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    lpAmountReceived, liqAmountA, liqAmountB, usdValue, _ = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_aerodrome_classic_remove_liq_partial_volatile(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    bob_agent,
):
    legoId = lego_aero_classic.legoId()
    pool = boa.from_etherscan("0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("aero")
    amountB = 11_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    lpAmountReceived, liqAmountA, liqAmountB, usdValue, _ = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB, lpAmountReceived // 2)


@pytest.always
def test_aerodrome_classic_remove_liq_max_stable(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    bob_agent,
):
    legoId = lego_aero_classic.legoId()
    pool = boa.from_etherscan("0xf213F2D02837012dC0236cC105061e121bB03e37")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("dola")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    lpAmountReceived, liqAmountA, liqAmountB, usdValue, _ = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_aerodrome_classic_remove_liq_partial_stable(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    bob_agent,
):
    legoId = lego_aero_classic.legoId()
    pool = boa.from_etherscan("0xf213F2D02837012dC0236cC105061e121bB03e37")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("dola")
    amountB = 10_000 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    lpAmountReceived, liqAmountA, liqAmountB, usdValue, _ = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_aero_classic, ZERO_ADDRESS, 0, pool, tokenA, tokenB, lpAmountReceived // 2)


# helper / utils


@pytest.always
def test_aerodrome_classic_get_best_pool(
    getTokenAndWhale,
    lego_aero_classic,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")

    best_pool = lego_aero_classic.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0xcDAC0d6c6C59727a65F871236188350531885C43"
    assert best_pool.fee == 30
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2

    # aero
    tokenB, _ = getTokenAndWhale("aero")
    best_pool = lego_aero_classic.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d"
    assert best_pool.fee == 30
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2


@pytest.always
def test_aerodrome_classic_get_swap_amount_out(
    getTokenAndWhale,
    lego_aero_classic,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_out = lego_aero_classic.getSwapAmountOut("0xcDAC0d6c6C59727a65F871236188350531885C43", tokenA, tokenB, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_out, 100)

    amount_out = lego_aero_classic.getSwapAmountOut("0xcDAC0d6c6C59727a65F871236188350531885C43", tokenB, tokenA, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_out, 100)


@pytest.always
def test_aerodrome_classic_get_swap_amount_in(
    getTokenAndWhale,
    lego_aero_classic,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_in = lego_aero_classic.getSwapAmountIn("0xcDAC0d6c6C59727a65F871236188350531885C43", tokenB, tokenA, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_in, 100)

    amount_in = lego_aero_classic.getSwapAmountIn("0xcDAC0d6c6C59727a65F871236188350531885C43", tokenA, tokenB, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_in, 100)


@pytest.always
def test_aerodrome_classic_get_add_liq_amounts_in(
    getTokenAndWhale,
    lego_aero_classic,
    _test,
):
    pool = boa.from_etherscan("0xcDAC0d6c6C59727a65F871236188350531885C43")
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, _ = lego_aero_classic.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 3 * (10 ** tokenB.decimals()), 1_00)

    # set new amount b
    amountB = 10 * (10 ** tokenB.decimals())

    # reduce amount b
    liq_amount_a, liq_amount_b, _ = lego_aero_classic.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 10_000 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 4 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_aerodrome_classic_get_remove_liq_amounts_out(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_classic,
    bob_agent,
    _test,
):
    legoId = lego_aero_classic.legoId()
    pool = boa.from_etherscan("0xcDAC0d6c6C59727a65F871236188350531885C43")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 7_500 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert liquidityAdded != 0

    # test
    amountAOut, amountBOut = lego_aero_classic.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(amountAOut, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(amountBOut, 3 * (10 ** tokenB.decimals()), 1_00)

    # re-arrange amounts
    first_amount, second_amount = lego_aero_classic.getRemoveLiqAmountsOut(pool, tokenB, tokenA, liquidityAdded)
    _test(first_amount, 3 * (10 ** tokenB.decimals()), 1_00)
    _test(second_amount, 7_500 * (10 ** tokenA.decimals()), 1_00)


@pytest.always
def test_aerodrome_classic_get_price(
    getTokenAndWhale,
    lego_aero_classic,
    governor,
    oracle_chainlink,
    oracle_registry,
    _test,
):
    pool = boa.from_etherscan("0xcDAC0d6c6C59727a65F871236188350531885C43")

    tokenA, _ = getTokenAndWhale("usdc")
    assert oracle_chainlink.setChainlinkFeed(tokenA, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)
    assert oracle_chainlink.getPrice(tokenA) != 0
    assert oracle_registry.getPrice(tokenA, False) != 0

    tokenB, _ = getTokenAndWhale("weth")
    exp_weth_price = oracle_chainlink.getPrice(tokenB)
    assert exp_weth_price != 0
    assert oracle_registry.getPrice(tokenB, False) != 0

    price = lego_aero_classic.getPriceUnsafe(pool, tokenA)
    assert int(0.98 * EIGHTEEN_DECIMALS) <= price <= int(1.02 * EIGHTEEN_DECIMALS)

    price = lego_aero_classic.getPriceUnsafe(pool, tokenB)
    _test(exp_weth_price, price, 1_00)