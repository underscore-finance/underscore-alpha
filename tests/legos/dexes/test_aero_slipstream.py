import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256, EIGHTEEN_DECIMALS
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


# add liquidity


@pytest.always
def test_aero_slipstream_add_liquidity_new_position_more_token_A(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 50_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 1 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")
    nft_token_manager = boa.from_etherscan(lego_aero_slipstream.getRegistries()[2])
    nftTokenId = testLegoLiquidityAdded(lego_aero_slipstream, nft_token_manager, 0, pool, tokenA, tokenB, amountA, amountB)
    assert nftTokenId != 0


@pytest.always
def test_aero_slipstream_add_liquidity_new_position_more_token_B(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 1_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 10 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")
    nft_token_manager = boa.from_etherscan(lego_aero_slipstream.getRegistries()[2])
    nftTokenId = testLegoLiquidityAdded(lego_aero_slipstream, nft_token_manager, 0, pool, tokenA, tokenB, amountA, amountB)
    assert nftTokenId != 0


@pytest.always
def test_aero_slipstream_add_liquidity_increase_position(
    testLegoLiquidityAdded,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    bob_agent,
):
    # setup
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 50_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 1 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")
    nft_token_manager = boa.from_etherscan(lego_aero_slipstream.getRegistries()[2])

    # initial mint position
    liquidityAdded, _a, _b, _c, nftTokenId = bob_ai_wallet.addLiquidity(lego_aero_slipstream.legoId(), nft_token_manager.address, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert liquidityAdded != 0
    assert nftTokenId != 0

    # add new amounts
    new_amount_a = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, new_amount_a, sender=whaleA)
    new_amount_b = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, new_amount_b, sender=whaleB)

    # increase liquidity
    testLegoLiquidityAdded(lego_aero_slipstream, nft_token_manager, nftTokenId, pool, tokenA, tokenB, new_amount_a, new_amount_b)


# remove liquidity


@pytest.always
def test_aero_slipstream_remove_liq_max(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    bob_agent,
):
    legoId = lego_aero_slipstream.legoId()
    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")

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
    nft_token_manager = boa.from_etherscan(lego_aero_slipstream.getRegistries()[2])
    testLegoLiquidityRemoved(lego_aero_slipstream, nft_token_manager, nftTokenId, pool, tokenA, tokenB)


@pytest.always
def test_aero_slipstream_remove_liq_partial(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    bob_agent,
):
    legoId = lego_aero_slipstream.legoId()
    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")

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
    nft_token_manager = boa.from_etherscan(lego_aero_slipstream.getRegistries()[2])
    testLegoLiquidityRemoved(lego_aero_slipstream, nft_token_manager, nftTokenId, pool, tokenA, tokenB, liquidityAdded // 2)


@pytest.always
def test_aero_slipstream_remove_liq_max_stable(
    testLegoLiquidityRemoved,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    bob_agent,
):
    legoId = lego_aero_slipstream.legoId()
    pool = boa.from_etherscan("0x47cA96Ea59C13F72745928887f84C9F52C3D7348")

    # setup
    tokenA, whaleA = getTokenAndWhale("weth")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenA.transfer(bob_ai_wallet.address, amountA, sender=whaleA)

    tokenB, whaleB = getTokenAndWhale("cbeth")
    amountB = 3 * (10 ** tokenB.decimals())
    tokenB.transfer(bob_ai_wallet.address, amountB, sender=whaleB)

    # add liquidity
    liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId = bob_ai_wallet.addLiquidity(legoId, ZERO_ADDRESS, 0, pool.address, tokenA.address, tokenB.address, amountA, amountB, sender=bob_agent)
    assert nftTokenId != 0 and liquidityAdded != 0

    # test remove liquidity
    nft_token_manager = boa.from_etherscan(lego_aero_slipstream.getRegistries()[2])
    testLegoLiquidityRemoved(lego_aero_slipstream, nft_token_manager, nftTokenId, pool, tokenA, tokenB)



# helper / utils


@pytest.always
def test_aero_slipstream_get_best_pool(
    getTokenAndWhale,
    lego_aero_slipstream,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")

    best_pool = lego_aero_slipstream.getBestPool(tokenA, tokenB)
    assert best_pool.pool == "0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59"
    assert best_pool.fee == 4
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2

    tokenA, _ = getTokenAndWhale("cbbtc")
    best_pool = lego_aero_slipstream.getBestPool(tokenA, tokenB)
    assert best_pool.pool == "0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1"
    assert best_pool.fee == 5
    assert best_pool.liquidity != 0
    assert best_pool.numCoins == 2


@pytest.always
def test_aero_slipstream_get_swap_amount_out(
    getTokenAndWhale,
    lego_aero_slipstream,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_out = lego_aero_slipstream.getSwapAmountOut("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59", tokenA, tokenB, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_out, 100)

    amount_out = lego_aero_slipstream.getSwapAmountOut("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59", tokenB, tokenA, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_out, 100)


@pytest.always
def test_aero_slipstream_get_swap_amount_in(
    getTokenAndWhale,
    lego_aero_slipstream,
    _test,
):
    tokenA, _ = getTokenAndWhale("usdc")
    tokenB, _ = getTokenAndWhale("weth")
    amount_in = lego_aero_slipstream.getSwapAmountIn("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59", tokenB, tokenA, 2_500 * (10 ** tokenA.decimals()))
    _test(1 * (10 ** tokenB.decimals()), amount_in, 100)

    amount_in = lego_aero_slipstream.getSwapAmountIn("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59", tokenA, tokenB, 1 * (10 ** tokenB.decimals()))
    _test(2_500 * (10 ** tokenA.decimals()), amount_in, 100)


@pytest.always
def test_aero_slipstream_get_add_liq_amounts_in(
    getTokenAndWhale,
    lego_aero_slipstream,
    _test,
):
    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")
    tokenA, whaleA = getTokenAndWhale("usdc")
    amountA = 10_000 * (10 ** tokenA.decimals())
    tokenB, whaleB = getTokenAndWhale("weth")
    amountB = 3 * (10 ** tokenB.decimals())

    # reduce amount a
    liq_amount_a, liq_amount_b, _ = lego_aero_slipstream.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 3 * (10 ** tokenB.decimals()), 1_00)

    # set new amount b
    amountB = 10 * (10 ** tokenB.decimals())

    # reduce amount b
    liq_amount_a, liq_amount_b, _ = lego_aero_slipstream.getAddLiqAmountsIn(pool, tokenA, tokenB, amountA, amountB)
    _test(liq_amount_a, 10_000 * (10 ** tokenA.decimals()), 1_00)
    _test(liq_amount_b, 4 * (10 ** tokenB.decimals()), 1_00)


@pytest.always
def test_aero_slipstream_get_remove_liq_amounts_out(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aero_slipstream,
    bob_agent,
    _test,
):
    legoId = lego_aero_slipstream.legoId()
    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")

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
    amountAOut, amountBOut = lego_aero_slipstream.getRemoveLiqAmountsOut(pool, tokenA, tokenB, liquidityAdded)
    _test(amountAOut, 7_500 * (10 ** tokenA.decimals()), 1_00)
    _test(amountBOut, 3 * (10 ** tokenB.decimals()), 1_00)

    # re-arrange amounts
    first_amount, second_amount = lego_aero_slipstream.getRemoveLiqAmountsOut(pool, tokenB, tokenA, liquidityAdded)
    _test(first_amount, 3 * (10 ** tokenB.decimals()), 1_00)
    _test(second_amount, 7_500 * (10 ** tokenA.decimals()), 1_00)


@pytest.always
def test_aero_slipstream_get_price(
    getTokenAndWhale,
    lego_aero_slipstream,
    governor,
    oracle_chainlink,
    oracle_registry,
    _test,
):
    pool = boa.from_etherscan("0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59")

    tokenA, _ = getTokenAndWhale("usdc")
    assert oracle_chainlink.setChainlinkFeed(tokenA, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)
    assert oracle_chainlink.getPrice(tokenA) != 0
    assert oracle_registry.getPrice(tokenA, False) != 0

    tokenB, _ = getTokenAndWhale("weth")
    exp_weth_price = oracle_chainlink.getPrice(tokenB)
    assert exp_weth_price != 0
    assert oracle_registry.getPrice(tokenB, False) != 0

    price = lego_aero_slipstream.getPriceUnsafe(pool, tokenA)
    assert int(0.98 * EIGHTEEN_DECIMALS) <= price <= int(1.02 * EIGHTEEN_DECIMALS)

    price = lego_aero_slipstream.getPriceUnsafe(pool, tokenB)
    _test(exp_weth_price, price, 1_00)

