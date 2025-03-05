import pytest
import boa

from utils.BluePrint import CORE_TOKENS
from constants import ZERO_ADDRESS, HUNDRED_PERCENT, MAX_UINT256


#########
# Tests #
#########


@pytest.always
def test_get_routes_and_swap_instructions_amount_out(lego_helper, fork):
    """Test the high-level getRoutesAndSwapInstructionsAmountOut function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Test with 1% slippage
    slippage = 1_00  # 1%
    
    # Get swap instructions
    instructions = lego_helper.getRoutesAndSwapInstructionsAmountOut(
        usdc.address, weth.address, usdc_amount, slippage
    )
    
    # Verify we got valid instructions
    assert len(instructions) > 0
    
    # Check the first instruction
    instruction = instructions[0]
    assert instruction.legoId != 0
    assert instruction.amountIn > 0
    assert instruction.minAmountOut > 0
    assert len(instruction.tokenPath) >= 2
    assert len(instruction.poolPath) >= 1
    assert instruction.tokenPath[0] == usdc.address
    assert instruction.tokenPath[-1] == weth.address
    
    # Verify slippage calculation is correct
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, usdc_amount)
    expected_min_amount_out = routes[-1].amountOut * (HUNDRED_PERCENT - slippage) // HUNDRED_PERCENT
    assert instruction.minAmountOut == expected_min_amount_out


@pytest.always
def test_get_routes_and_swap_instructions_amount_in(lego_helper, fork):
    """Test the high-level getRoutesAndSwapInstructionsAmountIn function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    weth_amount = int(0.1 * (10 ** weth.decimals()))  # 0.1 WETH
    
    # Test with 1% slippage and 1000 USDC available
    slippage = 1_00  # 1%
    available_usdc = 1000 * (10 ** usdc.decimals())
    
    # Get swap instructions
    instructions = lego_helper.getRoutesAndSwapInstructionsAmountIn(
        usdc.address, weth.address, weth_amount, available_usdc, slippage
    )
    
    # Verify we got valid instructions
    assert len(instructions) > 0
    
    # Check the first instruction
    instruction = instructions[0]
    assert instruction.legoId != 0
    assert instruction.amountIn > 0
    assert instruction.amountIn <= available_usdc
    assert instruction.minAmountOut > 0
    assert len(instruction.tokenPath) >= 2
    assert len(instruction.poolPath) >= 1
    assert instruction.tokenPath[0] == usdc.address
    assert instruction.tokenPath[-1] == weth.address


@pytest.always
def test_prepare_swap_instructions_amount_out(lego_helper, fork):
    """Test the prepareSwapInstructionsAmountOut function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get routes
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, usdc_amount)
    assert len(routes) > 0
    
    # Test with 1% slippage
    slippage = 1_00  # 1%
    
    # Prepare swap instructions
    instructions = lego_helper.prepareSwapInstructionsAmountOut(slippage, routes)
    
    # Verify we got valid instructions
    assert len(instructions) > 0
    
    # Check the first instruction
    instruction = instructions[0]
    assert instruction.legoId == routes[0].legoId
    assert instruction.amountIn == routes[0].amountIn
    
    # Verify slippage calculation is correct
    expected_min_amount_out = routes[-1].amountOut * (HUNDRED_PERCENT - slippage) // HUNDRED_PERCENT
    assert instruction.minAmountOut == expected_min_amount_out


@pytest.always
def test_get_best_swap_routes_amount_out(lego_helper, fork):
    """Test the getBestSwapRoutesAmountOut function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get routes without specifying lego IDs
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, usdc_amount)
    
    # Verify we got valid routes
    assert len(routes) > 0
    
    # Check the first route
    route = routes[0]
    assert route.legoId != 0
    assert route.pool != ZERO_ADDRESS
    assert route.tokenIn == usdc.address
    assert route.amountIn == usdc_amount
    assert route.amountOut > 0
    
    # If there are multiple routes, check that they connect properly
    if len(routes) > 1:
        for i in range(1, len(routes)):
            assert routes[i-1].tokenOut == routes[i].tokenIn
    
    # Check the last route
    assert routes[-1].tokenOut == weth.address
    
    # Test with specific lego IDs
    uniswap_v3_id = lego_helper.uniswapV3Id()
    routes_with_specific_lego = lego_helper.getBestSwapRoutesAmountOut(
        usdc.address, weth.address, usdc_amount, [uniswap_v3_id]
    )
    
    # Verify we got valid routes
    if len(routes_with_specific_lego) > 0:
        # Check that all routes use the specified lego
        for route in routes_with_specific_lego:
            assert route.legoId == uniswap_v3_id


@pytest.always
def test_get_best_swap_amount_out_with_router_pool(lego_helper, fork):
    """Test the getBestSwapAmountOutWithRouterPool function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Use a token that's likely to require routing through core tokens
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    
    # Get amount out and routes
    amount_out, routes = lego_helper.getBestSwapAmountOutWithRouterPool(
        usdc.address, well.address, usdc_amount
    )
    
    # If routes are found, verify they're valid
    if len(routes) > 0:
        assert amount_out > 0
        
        # Check the first route
        assert routes[0].tokenIn == usdc.address
        assert routes[0].amountIn == usdc_amount
        
        # Check the last route
        assert routes[-1].tokenOut == well.address
        assert routes[-1].amountOut == amount_out
        
        # Check that routes connect properly
        for i in range(1, len(routes)):
            assert routes[i-1].tokenOut == routes[i].tokenIn


@pytest.always
def test_get_best_swap_amount_out_single_pool(lego_helper, fork):
    """Test the getBestSwapAmountOutSinglePool function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get best swap route for a single pool
    route = lego_helper.getBestSwapAmountOutSinglePool(
        usdc.address, weth.address, usdc_amount
    )
    
    # Verify we got a valid route
    assert route.legoId != 0
    assert route.pool != ZERO_ADDRESS
    assert route.tokenIn == usdc.address
    assert route.tokenOut == weth.address
    assert route.amountIn == usdc_amount
    assert route.amountOut > 0
    
    # Test with specific lego IDs
    uniswap_v3_id = lego_helper.uniswapV3Id()
    route_with_specific_lego = lego_helper.getBestSwapAmountOutSinglePool(
        usdc.address, weth.address, usdc_amount, [uniswap_v3_id]
    )
    
    # If a route is found, verify it uses the specified lego
    if route_with_specific_lego.legoId != 0:
        assert route_with_specific_lego.legoId == uniswap_v3_id


@pytest.always
def test_get_swap_amount_out_via_router_pool(lego_helper, fork):
    """Test the getSwapAmountOutViaRouterPool function"""
    # Get router tokens (typically USDC and WETH)
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Get swap route via router pool
    route = lego_helper.getSwapAmountOutViaRouterPool(
        usdc.address, weth.address, usdc_amount
    )
    
    # Verify we got a valid route
    assert route.legoId != 0
    assert route.pool != ZERO_ADDRESS
    assert route.tokenIn == usdc.address
    assert route.tokenOut == weth.address
    assert route.amountIn == usdc_amount
    assert route.amountOut > 0


@pytest.always
def test_get_best_swap_routes_amount_in(lego_helper, fork):
    """Test the getBestSwapRoutesAmountIn function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    weth_amount = int(0.1 * (10 ** weth.decimals()))  # 0.1 WETH
    
    # Get routes without specifying lego IDs
    routes = lego_helper.getBestSwapRoutesAmountIn(usdc.address, weth.address, weth_amount)
    
    # Verify we got valid routes
    assert len(routes) > 0
    
    # Check the first route
    route = routes[0]
    assert route.legoId != 0
    assert route.pool != ZERO_ADDRESS
    assert route.tokenIn == usdc.address
    assert route.amountIn > 0
    assert route.amountOut > 0
    
    # If there are multiple routes, check that they connect properly
    if len(routes) > 1:
        for i in range(1, len(routes)):
            assert routes[i-1].tokenOut == routes[i].tokenIn
    
    # Check the last route
    assert routes[-1].tokenOut == weth.address
    assert routes[-1].amountOut == weth_amount


@pytest.always
def test_get_best_swap_amount_in_with_router_pool(lego_helper, fork):
    """Test the getBestSwapAmountInWithRouterPool function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    # Use a token that's likely to require routing through core tokens
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    well_amount = 10 * (10 ** well.decimals())  # 10 WELL
    
    # Get amount in and routes
    amount_in, routes = lego_helper.getBestSwapAmountInWithRouterPool(
        usdc.address, well.address, well_amount
    )
    
    # If routes are found, verify they're valid
    if len(routes) > 0 and amount_in != 2**256 - 1:  # max_value(uint256)
        assert amount_in > 0
        
        # Check the first route
        assert routes[0].tokenIn == usdc.address
        assert routes[0].amountIn == amount_in
        
        # Check the last route
        assert routes[-1].tokenOut == well.address
        assert routes[-1].amountOut == well_amount
        
        # Check that routes connect properly
        for i in range(1, len(routes)):
            assert routes[i-1].tokenOut == routes[i].tokenIn


@pytest.always
def test_get_best_swap_amount_in_single_pool(lego_helper, fork):
    """Test the getBestSwapAmountInSinglePool function"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    weth_amount = int(0.1 * (10 ** weth.decimals()))  # 0.1 WETH
    
    # Get best swap route for a single pool
    route = lego_helper.getBestSwapAmountInSinglePool(
        usdc.address, weth.address, weth_amount
    )
    
    # Verify we got a valid route
    assert route.legoId != 0
    assert route.pool != ZERO_ADDRESS
    assert route.tokenIn == usdc.address
    assert route.tokenOut == weth.address
    assert route.amountIn > 0
    assert route.amountOut == weth_amount
    
    # Test with specific lego IDs
    uniswap_v3_id = lego_helper.uniswapV3Id()
    route_with_specific_lego = lego_helper.getBestSwapAmountInSinglePool(
        usdc.address, weth.address, weth_amount, [uniswap_v3_id]
    )
    
    # If a route is found, verify it uses the specified lego
    if route_with_specific_lego.legoId != 0 and route_with_specific_lego.amountIn != 2**256 - 1:
        assert route_with_specific_lego.legoId == uniswap_v3_id


@pytest.always
def test_get_swap_amount_in_via_router_pool(lego_helper, fork):
    """Test the getSwapAmountInViaRouterPool function"""
    # Get router tokens (typically USDC and WETH)
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    weth_amount = int(0.1 * (10 ** weth.decimals()))  # 0.1 WETH
    
    # Get swap route via router pool
    route = lego_helper.getSwapAmountInViaRouterPool(
        usdc.address, weth.address, weth_amount
    )
    
    # Verify we got a valid route if one exists
    if route.legoId != 0 and route.amountIn != 2**256 - 1:
        assert route.pool != ZERO_ADDRESS
        assert route.tokenIn == usdc.address
        assert route.tokenOut == weth.address
        assert route.amountIn > 0
        assert route.amountOut == weth_amount


@pytest.always
def test_multi_token_path_swap(lego_helper, fork):
    """Test swaps with multiple tokens in the path"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Try to find a token that might require multiple hops
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    
    # Get routes
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, well.address, usdc_amount)
    
    # If we found a multi-hop route, test it
    if len(routes) > 1:
        # Verify the routes connect properly
        for i in range(1, len(routes)):
            assert routes[i-1].tokenOut == routes[i].tokenIn
        
        # Test preparing swap instructions
        slippage = 1_00  # 1%
        instructions = lego_helper.prepareSwapInstructionsAmountOut(slippage, routes)
        
        # Check if instructions were consolidated when possible
        # If routes with the same legoId were consolidated, we should have fewer instructions than routes
        if all(routes[i].legoId == routes[0].legoId for i in range(len(routes))):
            assert len(instructions) == 1
            # The token path should include all tokens
            assert len(instructions[0].tokenPath) == len(routes) + 1
            # The pool path should include all pools
            assert len(instructions[0].poolPath) == len(routes)
        else:
            # Otherwise, we should have at least one instruction
            assert len(instructions) > 0


# Edge Cases and Special Scenarios

@pytest.always
def test_edge_case_same_token(lego_helper, fork):
    """Test swapping between the same token (should return empty routes)"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Test getBestSwapRoutesAmountOut with same token
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, usdc.address, usdc_amount)
    assert len(routes) == 0
    
    # Test getBestSwapRoutesAmountIn with same token
    routes = lego_helper.getBestSwapRoutesAmountIn(usdc.address, usdc.address, usdc_amount)
    assert len(routes) == 0
    
    # Test getRoutesAndSwapInstructionsAmountOut with same token
    instructions = lego_helper.getRoutesAndSwapInstructionsAmountOut(
        usdc.address, usdc.address, usdc_amount, 1_00
    )
    assert len(instructions) == 0
    
    # Test getRoutesAndSwapInstructionsAmountIn with same token
    instructions = lego_helper.getRoutesAndSwapInstructionsAmountIn(
        usdc.address, usdc.address, usdc_amount, MAX_UINT256, 1_00
    )
    assert len(instructions) == 0


@pytest.always
def test_edge_case_zero_amount(lego_helper, fork):
    """Test swapping with zero amount (should return empty routes)"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Test getBestSwapRoutesAmountOut with zero amount
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, 0)
    assert len(routes) == 0
    
    # Test getBestSwapRoutesAmountIn with zero amount
    routes = lego_helper.getBestSwapRoutesAmountIn(usdc.address, weth.address, 0)
    assert len(routes) == 0
    
    # Test getRoutesAndSwapInstructionsAmountOut with zero amount
    instructions = lego_helper.getRoutesAndSwapInstructionsAmountOut(
        usdc.address, weth.address, 0, 1_00
    )
    assert len(instructions) == 0
    
    # Test getRoutesAndSwapInstructionsAmountIn with zero amount
    instructions = lego_helper.getRoutesAndSwapInstructionsAmountIn(
        usdc.address, weth.address, 0, MAX_UINT256, 1_00
    )
    assert len(instructions) == 0


@pytest.always
def test_edge_case_empty_address(lego_helper, fork):
    """Test swapping with empty address (should return empty routes)"""
    # Now that the contract handles empty addresses gracefully, we can test this functionality
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())

    # Test getBestSwapRoutesAmountOut with empty address
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, ZERO_ADDRESS, usdc_amount)
    assert len(routes) == 0
    
    routes = lego_helper.getBestSwapRoutesAmountOut(ZERO_ADDRESS, usdc.address, usdc_amount)
    assert len(routes) == 0

    # Test getBestSwapRoutesAmountIn with empty address
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    weth_amount = int(0.1 * (10 ** weth.decimals()))
    routes = lego_helper.getBestSwapRoutesAmountIn(usdc.address, ZERO_ADDRESS, weth_amount)
    assert len(routes) == 0
    
    routes = lego_helper.getBestSwapRoutesAmountIn(ZERO_ADDRESS, weth.address, weth_amount)
    assert len(routes) == 0


@pytest.always
def test_prepare_swap_instructions_empty_routes(lego_helper, fork):
    """Test preparing swap instructions with empty routes"""
    # Test prepareSwapInstructionsAmountOut with empty routes
    instructions = lego_helper.prepareSwapInstructionsAmountOut(1_00, [])
    assert len(instructions) == 0


@pytest.always
def test_specific_lego_ids(lego_helper, fork):
    """Test swapping with specific lego IDs"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get all available lego IDs
    uniswap_v2_id = lego_helper.uniswapV2Id()
    uniswap_v3_id = lego_helper.uniswapV3Id()
    aerodrome_id = lego_helper.aerodromeId()
    
    # Test with multiple specific lego IDs
    lego_ids = [uniswap_v2_id, uniswap_v3_id, aerodrome_id]
    
    # Test getBestSwapRoutesAmountOut with specific lego IDs
    routes = lego_helper.getBestSwapRoutesAmountOut(
        usdc.address, weth.address, usdc_amount, lego_ids
    )
    
    # If routes are found, verify they use one of the specified legos
    if len(routes) > 0:
        for route in routes:
            assert route.legoId in lego_ids
    
    # Test getBestSwapRoutesAmountIn with specific lego IDs
    weth_amount = int(0.1 * (10 ** weth.decimals()))
    routes = lego_helper.getBestSwapRoutesAmountIn(
        usdc.address, weth.address, weth_amount, lego_ids
    )
    
    # If routes are found, verify they use one of the specified legos
    if len(routes) > 0:
        for route in routes:
            assert route.legoId in lego_ids


@pytest.always
def test_different_slippage_values(lego_helper, fork):
    """Test swapping with different slippage values"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get routes
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, usdc_amount)
    
    if len(routes) > 0:
        # Test with 0% slippage
        instructions_0 = lego_helper.prepareSwapInstructionsAmountOut(0, routes)
        assert instructions_0[0].minAmountOut == routes[-1].amountOut
        
        # Test with 1% slippage
        instructions_1 = lego_helper.prepareSwapInstructionsAmountOut(1_00, routes)
        expected_min_amount_out_1 = routes[-1].amountOut * (HUNDRED_PERCENT - 1_00) // HUNDRED_PERCENT
        assert instructions_1[0].minAmountOut == expected_min_amount_out_1
        
        # Test with 5% slippage
        instructions_5 = lego_helper.prepareSwapInstructionsAmountOut(5_00, routes)
        expected_min_amount_out_5 = routes[-1].amountOut * (HUNDRED_PERCENT - 5_00) // HUNDRED_PERCENT
        assert instructions_5[0].minAmountOut == expected_min_amount_out_5
        
        # Verify that higher slippage results in lower minAmountOut
        assert instructions_0[0].minAmountOut > instructions_1[0].minAmountOut
        assert instructions_1[0].minAmountOut > instructions_5[0].minAmountOut


@pytest.always
def test_router_token_swaps(lego_helper, fork):
    """Test swaps involving router tokens"""
    # Get router tokens (typically USDC and WETH)
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Test direct swap between router tokens
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Get routes for direct swap between router tokens
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, usdc_amount)
    assert len(routes) > 0
    
    # Test swap from router token to another token
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    
    # Get routes from router token to another token
    routes_from_router = lego_helper.getBestSwapRoutesAmountOut(usdc.address, well.address, usdc_amount)
    
    # Test swap from another token to router token
    well_amount = 10 * (10 ** well.decimals())
    
    # Get routes from another token to router token
    routes_to_router = lego_helper.getBestSwapRoutesAmountOut(well.address, usdc.address, well_amount)
    
    # At least one of these should return valid routes
    assert len(routes_from_router) > 0 or len(routes_to_router) > 0


@pytest.always
def test_multi_hop_consolidation(lego_helper, fork):
    """Test consolidation of multi-hop routes with the same lego ID"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Try to find a token that might require multiple hops
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    
    # Get routes
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, well.address, usdc_amount)
    
    # If we found a multi-hop route with the same lego ID, test consolidation
    if len(routes) > 1 and all(route.legoId == routes[0].legoId for route in routes):
        # Test preparing swap instructions
        slippage = 1_00  # 1%
        instructions = lego_helper.prepareSwapInstructionsAmountOut(slippage, routes)
        
        # Should be consolidated into a single instruction
        assert len(instructions) == 1
        
        # The token path should include all tokens
        assert len(instructions[0].tokenPath) == len(routes) + 1
        
        # The pool path should include all pools
        assert len(instructions[0].poolPath) == len(routes)
        
        # Verify the first and last tokens
        assert instructions[0].tokenPath[0] == routes[0].tokenIn
        assert instructions[0].tokenPath[-1] == routes[-1].tokenOut
        
        # Verify the amount in and min amount out
        assert instructions[0].amountIn == routes[0].amountIn
        expected_min_amount_out = routes[-1].amountOut * (HUNDRED_PERCENT - slippage) // HUNDRED_PERCENT
        assert instructions[0].minAmountOut == expected_min_amount_out


@pytest.always
def test_multi_hop_different_legos(lego_helper, fork):
    """Test multi-hop routes with different lego IDs"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Try to find a token that might require multiple hops
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    
    # Get routes
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, well.address, usdc_amount)
    
    # If we found a multi-hop route with different lego IDs
    if len(routes) > 1 and any(route.legoId != routes[0].legoId for route in routes):
        # Test preparing swap instructions
        slippage = 1_00  # 1%
        instructions = lego_helper.prepareSwapInstructionsAmountOut(slippage, routes)
        
        # Should have multiple instructions
        assert len(instructions) > 1
        
        # Verify the first and last tokens across all instructions
        assert instructions[0].tokenPath[0] == routes[0].tokenIn
        assert instructions[-1].tokenPath[-1] == routes[-1].tokenOut
        
        # Verify that instructions connect properly
        for i in range(1, len(instructions)):
            assert instructions[i-1].tokenPath[-1] == instructions[i].tokenPath[0]


@pytest.always
def test_large_amount_swaps(lego_helper, fork):
    """Test swaps with large amounts"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    # Test with a large amount (1 million USDC)
    large_usdc_amount = 1_000_000 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get routes for large amount
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, large_usdc_amount)
    
    # Should still find routes for large amounts
    if len(routes) > 0:
        assert routes[0].amountIn == large_usdc_amount
        assert routes[0].amountOut > 0
        
        # Test preparing swap instructions
        slippage = 1_00  # 1%
        instructions = lego_helper.prepareSwapInstructionsAmountOut(slippage, routes)
        
        # Verify we got valid instructions
        assert len(instructions) > 0
        assert instructions[0].amountIn == large_usdc_amount


@pytest.always
def test_small_amount_swaps(lego_helper, fork):
    """Test swaps with small amounts"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    # Test with a small amount (0.01 USDC)
    small_usdc_amount = int(0.01 * (10 ** usdc.decimals()))
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    # Get routes for small amount
    routes = lego_helper.getBestSwapRoutesAmountOut(usdc.address, weth.address, small_usdc_amount)
    
    # Should still find routes for small amounts
    if len(routes) > 0:
        assert routes[0].amountIn == small_usdc_amount
        assert routes[0].amountOut > 0
        
        # Test preparing swap instructions
        slippage = 1_00  # 1%
        instructions = lego_helper.prepareSwapInstructionsAmountOut(slippage, routes)
        
        # Verify we got valid instructions
        assert len(instructions) > 0
        assert instructions[0].amountIn == small_usdc_amount


@pytest.always
def test_compare_direct_vs_router_pool_routes(lego_helper, fork):
    """Test comparison between direct routes and router pool routes"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    # Try to find a token that might have both direct and router pool routes
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    
    # Get direct route
    direct_route = lego_helper.getBestSwapAmountOutSinglePool(
        usdc.address, well.address, usdc_amount
    )
    
    # Get router pool routes
    router_amount_out, router_routes = lego_helper.getBestSwapAmountOutWithRouterPool(
        usdc.address, well.address, usdc_amount
    )
    
    # Get the best routes (should choose the better of direct or router)
    best_routes = lego_helper.getBestSwapRoutesAmountOut(
        usdc.address, well.address, usdc_amount
    )
    
    # If both direct and router routes exist, verify that the best route is chosen
    if direct_route.amountOut > 0 and len(router_routes) > 0:
        if direct_route.amountOut > router_amount_out:
            # Direct route should be chosen
            assert len(best_routes) == 1
            assert best_routes[0].legoId == direct_route.legoId
            assert best_routes[0].pool == direct_route.pool
            assert best_routes[0].amountOut == direct_route.amountOut
        else:
            # Router routes should be chosen
            assert len(best_routes) == len(router_routes)
            assert best_routes[-1].amountOut == router_amount_out


@pytest.always
def test_compare_direct_vs_router_pool_routes_amount_in(lego_helper, fork):
    """Test comparison between direct routes and router pool routes for amount in"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    well = boa.from_etherscan(CORE_TOKENS[fork]["WELL"])
    well_amount = 10 * (10 ** well.decimals())
    
    # Get direct route
    direct_route = lego_helper.getBestSwapAmountInSinglePool(
        usdc.address, well.address, well_amount
    )
    
    # Get router pool routes
    router_amount_in, router_routes = lego_helper.getBestSwapAmountInWithRouterPool(
        usdc.address, well.address, well_amount
    )
    
    # Get the best routes (should choose the better of direct or router)
    best_routes = lego_helper.getBestSwapRoutesAmountIn(
        usdc.address, well.address, well_amount
    )
    
    # If both direct and router routes exist, verify that the best route is chosen
    if direct_route.amountIn != 2**256 - 1 and router_amount_in != 2**256 - 1 and len(router_routes) > 0:
        if direct_route.amountIn < router_amount_in:
            # Direct route should be chosen
            assert len(best_routes) == 1
            assert best_routes[0].legoId == direct_route.legoId
            assert best_routes[0].pool == direct_route.pool
            assert best_routes[0].amountIn == direct_route.amountIn
        else:
            # Router routes should be chosen
            assert len(best_routes) == len(router_routes)
            assert best_routes[0].amountIn == router_amount_in


@pytest.always
def test_get_routes_and_swap_instructions_amount_in_with_limited_amount(lego_helper, fork):
    """Test getRoutesAndSwapInstructionsAmountIn with limited available amount"""
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    weth_amount = int(0.1 * (10 ** weth.decimals()))  # 0.1 WETH
    
    # First get the amount needed without limiting
    routes = lego_helper.getBestSwapRoutesAmountIn(usdc.address, weth.address, weth_amount)
    
    if len(routes) > 0 and routes[0].amountIn != 2**256 - 1:
        required_amount = routes[0].amountIn
        
        # Now test with a limited amount that's less than required
        limited_amount = required_amount // 2
        slippage = 1_00  # 1%
        
        # Get swap instructions with limited amount
        instructions = lego_helper.getRoutesAndSwapInstructionsAmountIn(
            usdc.address, weth.address, weth_amount, limited_amount, slippage
        )
        
        # Verify we got valid instructions
        assert len(instructions) > 0
        
        # The amount in should be limited to the available amount
        assert instructions[0].amountIn <= limited_amount
        
        # The expected output should be less than the requested amount
        assert instructions[0].minAmountOut < weth_amount


@pytest.always
def test_all_dex_lego_ids(lego_helper, fork):
    """Test all available DEX lego IDs"""
    # Get all available DEX lego IDs
    uniswap_v2_id = lego_helper.uniswapV2Id()
    uniswap_v3_id = lego_helper.uniswapV3Id()
    aerodrome_id = lego_helper.aerodromeId()
    aerodrome_slipstream_id = lego_helper.aerodromeSlipstreamId()
    curve_id = lego_helper.curveId()
    
    # Verify all IDs are different
    lego_ids = [uniswap_v2_id, uniswap_v3_id, aerodrome_id, aerodrome_slipstream_id, curve_id]
    assert len(set(lego_ids)) == len(lego_ids)
    
    # Test with each lego ID individually
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"])
    usdc_amount = 100 * (10 ** usdc.decimals())
    
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"])
    
    for lego_id in lego_ids:
        # Test getBestSwapRoutesAmountOut with specific lego ID
        routes = lego_helper.getBestSwapRoutesAmountOut(
            usdc.address, weth.address, usdc_amount, [lego_id]
        )
        
        # If routes are found, verify they use the specified lego
        if len(routes) > 0:
            for route in routes:
                assert route.legoId == lego_id 