import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256, EIGHTEEN_DECIMALS
from conf_tokens import TEST_AMOUNTS
from utils.BluePrint import CORE_TOKENS


TEST_ASSETS = [
    "usdc",
    "weth",
]


TO_TOKEN = {
    "usdc": {
        "base": "0x4200000000000000000000000000000000000006", # WETH
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b", # VIRTUAL
        "local": ZERO_ADDRESS,
    },
}


POOLS = {
    "usdc": {
        "base": "0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C", # usdc/weth
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0xE31c372a7Af875b3B5E0F3713B17ef51556da667", # weth/virtual
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
def test_uniswapV2_swap_max_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_uniswap_v2.legoId(), fromAsset, toToken, pool)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_uniswapV2_swap_partial_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_uniswap_v2.legoId(), fromAsset, toToken, pool, testAmount // 2)


@pytest.always
def test_uniswapV2_swap_with_multiple_routes(
    oracle_chainlink,
    getTokenAndWhale,
    bob,
    lego_uniswap_v2,
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
    weth_usdc_pool = "0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C"

    # virtual setup
    virtual = boa.from_etherscan(CORE_TOKENS[fork]["VIRTUAL"], name="virtual token")
    weth_virtual_pool = "0xE31c372a7Af875b3B5E0F3713B17ef51556da667"
    virtual_price = lego_uniswap_v2.getPriceUnsafe(weth_virtual_pool, virtual)

    # pre balances
    pre_usdc_bal = usdc.balanceOf(bob)
    pre_virtual_bal = virtual.balanceOf(bob)

    # swap uniswap v2
    usdc.approve(lego_uniswap_v2, usdc_amount, sender=bob)
    fromSwapAmount, toAmount, _, usd_value = lego_uniswap_v2.swapTokens(usdc_amount, 0, [usdc, weth, virtual], [weth_usdc_pool, weth_virtual_pool], bob, sender=bob)
    assert toAmount != 0

    # post balances
    assert usdc.balanceOf(bob) == pre_usdc_bal - fromSwapAmount
    assert virtual.balanceOf(bob) == pre_virtual_bal + toAmount

    # usd values
    usdc_input_usd_value = oracle_registry.getUsdValue(usdc, usdc_amount, False)
    virtual_output_usd_value = virtual_price * toAmount // (10 ** virtual.decimals())
    _test(usdc_input_usd_value, virtual_output_usd_value, 5_00) # 5%


# add liquidity


@pytest.always
def test_uniswapV2_add_liquidity_more_token_A(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 50_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 1 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")
    testLegoLiquidityAdded(lego_uniswap_v2, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, amountB)


@pytest.always
def test_uniswapV2_add_liquidity_more_token_B(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 1_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 10 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")
    testLegoLiquidityAdded(lego_uniswap_v2, ZERO_ADDRESS, 0, pool, tokenA, tokenB, amountA, amountB)


# remove liquidity


@pytest.always
def test_uniswapV2_remove_liq_max(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
    bob_agent,
):
    legoId = lego_uniswap_v2.legoId()
    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    lpAmountReceived, liqAmountA, liqAmountB, usdValue, _ = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_uniswap_v2, ZERO_ADDRESS, 0, pool, tokenA, tokenB)


@pytest.always
def test_uniswapV2_remove_liq_partial(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
    bob_agent,
):
    legoId = lego_uniswap_v2.legoId()
    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    lpAmountReceived, liqAmountA, liqAmountB, usdValue, _ = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)

    # test remove liquidity
    testLegoLiquidityRemoved(lego_uniswap_v2, ZERO_ADDRESS, 0, pool, tokenA, tokenB, lpAmountReceived // 2)


# helper / utils


@pytest.always
def test_uniswapV2_get_best_pool(
    getTokenAndWhale,
    lego_uniswap_v2,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")

    best_pool = lego_uniswap_v2.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C"
    assert best_pool.fee == 30
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2

    # virtual
    best_pool = lego_uniswap_v2.getDeepestLiqPool("0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b", tokenB)
    assert best_pool.pool == "0xE31c372a7Af875b3B5E0F3713B17ef51556da667"
    assert best_pool.fee == 30
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2


@pytest.always
def test_uniswapV2_get_swap_amount_out(
    getTokenAndWhale,
    lego_uniswap_v2,
    _test,
):
    pool = "0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C"
    tokenA, _ = getTokenAndWhale("usdc")
    tokenA_amount = 2_500 * (10 ** tokenA.decimals())
    tokenB, _ = getTokenAndWhale("weth")
    tokenB_amount = 1 * (10 ** tokenB.decimals())

    # usdc -> weth
    amount_out = lego_uniswap_v2.getSwapAmountOut(pool, tokenA, tokenB, tokenA_amount)
    _test(tokenB_amount, amount_out, 100)

    best_pool, amount_out_b = lego_uniswap_v2.getBestSwapAmountOut(tokenA, tokenB, tokenA_amount)
    assert best_pool == pool
    assert amount_out == amount_out_b

    # weth -> usdc
    amount_out = lego_uniswap_v2.getSwapAmountOut(pool, tokenB, tokenA, tokenB_amount)
    _test(tokenA_amount, amount_out, 100)

    best_pool, amount_out_b = lego_uniswap_v2.getBestSwapAmountOut(tokenB, tokenA, tokenB_amount)
    assert best_pool == pool
    assert amount_out == amount_out_b


@pytest.always
def test_uniswapV2_get_swap_amount_in(
    getTokenAndWhale,
    lego_uniswap_v2,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_in = lego_uniswap_v2.getSwapAmountIn("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C", tokenB, tokenA, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_in, 100)

    amount_in = lego_uniswap_v2.getSwapAmountIn("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C", tokenA, tokenB, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_in, 100)


@pytest.always
def test_uniswapV2_get_add_liq_amounts_in(
    getTokenAndWhale,
    lego_uniswap_v2,
    _test,
):
    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, _ = lego_uniswap_v2.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 3 * (10 ** tokenB.decimals()), 1_00)

    # set new amount b
    amountB = 10 * (10 ** tokenB.decimals())

    # reduce amount b
    liq_amount_a, liq_amount_b, _ = lego_uniswap_v2.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 10_000 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 4 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_uniswapV2_get_remove_liq_amounts_out(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v2,
    bob_agent,
    _test,
):
    legoId = lego_uniswap_v2.legoId()
    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")

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
    amountAOut, amountBOut = lego_uniswap_v2.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(amountAOut, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(amountBOut, 3 * (10 ** tokenB.decimals()), 1_00)

    # re-arrange amounts
    first_amount, second_amount = lego_uniswap_v2.getRemoveLiqAmountsOut(pool, tokenB, tokenA, liquidityAdded)
    _test(first_amount, 3 * (10 ** tokenB.decimals()), 1_00)
    _test(second_amount, 7_500 * (10 ** tokenA.decimals()), 1_00)


@pytest.always
def test_uniswapV2_get_price(
    getTokenAndWhale,
    lego_uniswap_v2,
    governor,
    oracle_chainlink,
    oracle_registry,
    _test,
):
    pool = boa.from_etherscan("0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C")

    tokenA, _ = getTokenAndWhale("usdc")
    assert oracle_chainlink.setChainlinkFeed(tokenA, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)
    assert oracle_chainlink.getPrice(tokenA) != 0
    assert oracle_registry.getPrice(tokenA, False) != 0

    tokenB, _ = getTokenAndWhale("weth")
    exp_weth_price = oracle_chainlink.getPrice(tokenB)
    assert exp_weth_price != 0
    assert oracle_registry.getPrice(tokenB, False) != 0

    price = lego_uniswap_v2.getPriceUnsafe(pool, tokenA)
    assert int(0.98 * EIGHTEEN_DECIMALS) <= price <= int(1.02 * EIGHTEEN_DECIMALS)

    price = lego_uniswap_v2.getPriceUnsafe(pool, tokenB)
    _test(exp_weth_price, price, 1_00)