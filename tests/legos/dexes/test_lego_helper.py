import pytest
import boa

from utils.BluePrint import CORE_TOKENS
from constants import ZERO_ADDRESS


#########
# Tests #
#########


@pytest.always
def test_get_best_swap_amount_out(lego_helper, fork):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())

    virtual = boa.from_etherscan(CORE_TOKENS[fork]["VIRTUAL"])
    virtual_amount = 100 * (10 ** virtual.decimals())

    routes = lego_helper.getBestSwapRoutesAmountOut(usdc, virtual, usdc_amount)
    assert len(routes) != 0

    routeA = routes[0]
    assert routeA.legoId != 0
    assert routeA.pool != ZERO_ADDRESS
    assert routeA.tokenIn == usdc.address
    assert routeA.amountIn == usdc_amount
    assert routeA.amountOut != 0

    if len(routes) == 1:
        assert routeA.tokenOut == virtual.address

    elif len(routes) == 2:
        routeB = routes[1]
        assert routeB.tokenOut == virtual.address


@pytest.always
def test_get_best_swap_amount_in(lego_helper, fork):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())

    virtual = boa.from_etherscan(CORE_TOKENS[fork]["VIRTUAL"])
    virtual_amount = 100 * (10 ** virtual.decimals())

    routes = lego_helper.getBestSwapAmountIn(usdc, virtual, virtual_amount)
    assert len(routes) != 0

    routeA = routes[0]
    assert routeA.legoId != 0
    assert routeA.pool != ZERO_ADDRESS
    assert routeA.tokenIn == usdc.address
    assert routeA.amountIn != 0

    if len(routes) == 1:
        assert routeA.tokenOut == virtual.address
        assert routeA.amountOut == virtual_amount

    elif len(routes) == 2:
        routeB = routes[1]
        assert routeB.tokenOut == virtual.address
        assert routeB.amountOut == virtual_amount

