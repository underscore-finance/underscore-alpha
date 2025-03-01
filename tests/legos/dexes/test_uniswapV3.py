import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256, EIGHTEEN_DECIMALS
from conf_tokens import TEST_AMOUNTS


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
        "base": "0xb33Ff54b9F7242EF1593d2C9Bcd8f9df46c77935", # FAI
        "local": ZERO_ADDRESS,
    },
}


POOLS = {
    "usdc": {
        "base": "0xd0b53D9277642d899DF5C87A3966A349A798F224", # usdc/weth
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x68B27E9066d3aAdC6078E17C8611b37868F96A1D", # weth/fai
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
def test_uniswapV3_swap_max(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_uniswap_v3.legoId(), fromAsset, toToken)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_uniswapV3_swap_partial(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    getToToken,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    testLegoSwap(lego_uniswap_v3.legoId(), fromAsset, toToken, testAmount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_uniswapV3_swap_max_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    fromAsset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals()), sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_uniswap_v3.legoId(), fromAsset, toToken, MAX_UINT256, 0, pool)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_uniswapV3_swap_partial_with_pool(
    token_str,
    testLegoSwap,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    getToToken,
    getPool,
):
    # setup
    fromAsset, whale = getTokenAndWhale(token_str)
    testAmount = TEST_AMOUNTS[token_str] * (10 ** fromAsset.decimals())
    fromAsset.transfer(bob_ai_wallet.address, testAmount, sender=whale)
    toToken = getToToken(token_str)

    pool = getPool(token_str)
    testLegoSwap(lego_uniswap_v3.legoId(), fromAsset, toToken, testAmount // 2, 0, pool)


# add liquidity


@pytest.always
def test_uniswapV3_add_liquidity_new_position_more_token_A(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 50_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 1 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")
    uniswap_nft_token_manager = boa.from_etherscan(lego_uniswap_v3.getRegistries()[2])
    nftTokenId = testLegoLiquidityAdded(lego_uniswap_v3, uniswap_nft_token_manager, 0, pool, tokenA, tokenB, amountA, amountB)
    assert nftTokenId != 0


@pytest.always
def test_uniswapV3_add_liquidity_new_position_more_token_B(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 1_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 10 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")
    uniswap_nft_token_manager = boa.from_etherscan(lego_uniswap_v3.getRegistries()[2])
    nftTokenId = testLegoLiquidityAdded(lego_uniswap_v3, uniswap_nft_token_manager, 0, pool, tokenA, tokenB, amountA, amountB)
    assert nftTokenId != 0


@pytest.always
def test_uniswapV3_add_liquidity_increase_position(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    bob_agent,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 50_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 1 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")
    uniswap_nft_token_manager = boa.from_etherscan(lego_uniswap_v3.getRegistries()[2])

    # initial mint position
    liquidityAdded, _a, _b, _c, nftTokenId = bob_ai_wallet.addLiquidity(lego_uniswap_v3.legoId(), uniswap_nft_token_manager.address, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert liquidityAdded != 0
    assert nftTokenId != 0

    # add new amounts
    new_amount_a = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, new_amount_a, sender=whaleA)
    new_amount_b = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, new_amount_b, sender=whaleB)

    # increase liquidity
    testLegoLiquidityAdded(lego_uniswap_v3, uniswap_nft_token_manager, nftTokenId, pool, tokenA, tokenB, new_amount_a, new_amount_b)


# remove liquidity


@pytest.always
def test_uniswapV3_remove_liq_max(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    bob_agent,
):
    legoId = lego_uniswap_v3.legoId()
    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert nftTokenId != 0 and liquidityAdded != 0

    # test remove liquidity
    uniswap_nft_token_manager = boa.from_etherscan(lego_uniswap_v3.getRegistries()[2])
    testLegoLiquidityRemoved(lego_uniswap_v3, uniswap_nft_token_manager, nftTokenId, pool, tokenA, tokenB)


@pytest.always
def test_uniswapV3_remove_liq_partial(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    bob_agent,
):
    legoId = lego_uniswap_v3.legoId()
    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert nftTokenId != 0 and liquidityAdded != 0

    # test remove liquidity (partial)
    uniswap_nft_token_manager = boa.from_etherscan(lego_uniswap_v3.getRegistries()[2])
    testLegoLiquidityRemoved(lego_uniswap_v3, uniswap_nft_token_manager, nftTokenId, pool, tokenA, tokenB, liquidityAdded // 2)


# helper / utils


@pytest.always
def test_uniswapV3_get_best_pool(
    getTokenAndWhale,
    lego_uniswap_v3,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")

    best_pool = lego_uniswap_v3.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0xd0b53D9277642d899DF5C87A3966A349A798F224"
    assert best_pool.fee == 5
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2

    tokenA, _ = getTokenAndWhale("cbbtc")
    best_pool = lego_uniswap_v3.getDeepestLiqPool(tokenA, tokenB)
    assert best_pool.pool == "0x8c7080564B5A792A33Ef2FD473fbA6364d5495e5"
    assert best_pool.fee == 30
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2


@pytest.always
def test_uniswapV3_get_swap_amount_out(
    getTokenAndWhale,
    lego_uniswap_v3,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_out = lego_uniswap_v3.getSwapAmountOut("0xd0b53D9277642d899DF5C87A3966A349A798F224", tokenA, tokenB, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_out, 100)

    amount_out = lego_uniswap_v3.getSwapAmountOut("0xd0b53D9277642d899DF5C87A3966A349A798F224", tokenB, tokenA, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_out, 100)


@pytest.always
def test_uniswapV3_get_swap_amount_in(
    getTokenAndWhale,
    lego_uniswap_v3,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_in = lego_uniswap_v3.getSwapAmountIn("0xd0b53D9277642d899DF5C87A3966A349A798F224", tokenB, tokenA, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_in, 100)

    amount_in = lego_uniswap_v3.getSwapAmountIn("0xd0b53D9277642d899DF5C87A3966A349A798F224", tokenA, tokenB, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_in, 100)


@pytest.always
def test_uniswapV3_get_add_liq_amounts_in(
    getTokenAndWhale,
    lego_uniswap_v3,
    _test,
):
    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, _ = lego_uniswap_v3.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 3 * (10 ** tokenB.decimals()), 1_00)

    # set new amount b
    amountB = 10 * (10 ** tokenB.decimals())

    # reduce amount b
    liq_amount_a, liq_amount_b, _ = lego_uniswap_v3.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 10_000 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 4 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_uniswapV3_get_remove_liq_amounts_out(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_uniswap_v3,
    bob_agent,
    _test,
):
    legoId = lego_uniswap_v3.legoId()
    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")

    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 7_500 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert nftTokenId != 0 and liquidityAdded != 0

    # test
    amountAOut, amountBOut = lego_uniswap_v3.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(amountAOut, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(amountBOut, 3 * (10 ** tokenB.decimals()), 1_00)

    # re-arrange amounts
    first_amount, second_amount = lego_uniswap_v3.getRemoveLiqAmountsOut(pool, tokenB, tokenA, liquidityAdded)
    _test(first_amount, 3 * (10 ** tokenB.decimals()), 1_00)
    _test(second_amount, 7_500 * (10 ** tokenA.decimals()), 1_00)


@pytest.always
def test_uniswapV3_get_price(
    getTokenAndWhale,
    lego_uniswap_v3,
    governor,
    oracle_chainlink,
    oracle_registry,
    _test,
):
    pool = boa.from_etherscan("0xd0b53D9277642d899DF5C87A3966A349A798F224")

    tokenA, _ = getTokenAndWhale("usdc")
    assert oracle_chainlink.setChainlinkFeed(tokenA, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)
    assert oracle_chainlink.getPrice(tokenA) != 0
    assert oracle_registry.getPrice(tokenA, False) != 0

    tokenB, _ = getTokenAndWhale("weth")
    exp_weth_price = oracle_chainlink.getPrice(tokenB)
    assert exp_weth_price != 0
    assert oracle_registry.getPrice(tokenB, False) != 0

    price = lego_uniswap_v3.getPriceUnsafe(pool, tokenA)
    assert int(0.98 * EIGHTEEN_DECIMALS) <= price <= int(1.02 * EIGHTEEN_DECIMALS)

    price = lego_uniswap_v3.getPriceUnsafe(pool, tokenB)
    _test(exp_weth_price, price, 1_00)



