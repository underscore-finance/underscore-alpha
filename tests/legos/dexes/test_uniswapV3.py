import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256
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
    testNftLegoLiquidityAdded,
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
    nftTokenId = testNftLegoLiquidityAdded(lego_uniswap_v3.legoId(), uniswap_nft_token_manager, 0, pool, tokenA, tokenB, amountA, amountB)
    assert nftTokenId != 0


@pytest.always
def test_uniswapV3_add_liquidity_more_token_B(
    testNftLegoLiquidityAdded,
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
    nftTokenId = testNftLegoLiquidityAdded(lego_uniswap_v3.legoId(), uniswap_nft_token_manager, 0, pool, tokenA, tokenB, amountA, amountB)
    assert nftTokenId != 0