# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

from interfaces import LegoYield
from interfaces import LegoDex
from ethereum.ercs import IERC20
import contracts.modules.Registry as registry

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view
    def isValidLegoId(_legoId: uint256) -> bool: view
    def legoIdToType(_legoId: uint256) -> LegoType: view
    def getLegoInfo(_legoId: uint256) -> registry.AddyInfo: view
    def numLegosRaw() -> uint256: view

interface LegoDexNonStandard:
    def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> (address, uint256): nonpayable
    def getSwapAmountOut(_pool: address, _tokenIn: address, _tokenOut: address, _amountIn: uint256) -> uint256: nonpayable
    def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (address, uint256): nonpayable
    def getSwapAmountIn(_pool: address, _tokenIn: address, _tokenOut: address, _amountOut: uint256) -> uint256: nonpayable

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

flag LegoType:
    YIELD_OPP
    DEX

struct SwapRoute:
    legoId: uint256
    pool: address
    tokenIn: address
    tokenOut: address
    amountIn: uint256
    amountOut: uint256

struct SwapInstruction:
    legoId: uint256
    amountIn: uint256
    minAmountOut: uint256
    tokenPath: DynArray[address, MAX_TOKEN_PATH]
    poolPath: DynArray[address, MAX_TOKEN_PATH - 1]

struct UnderlyingData:
    asset: address
    amount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    legoDesc: String[64]

ADDY_REGISTRY: public(immutable(address))

# key router tokens
ROUTER_TOKENA: public(immutable(address))
ROUTER_TOKENB: public(immutable(address))

MAX_ROUTES: constant(uint256) = 10
MAX_TOKEN_PATH: constant(uint256) = 5
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_LEGOS: constant(uint256) = 20
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%


@deploy
def __init__(
    _addyRegistry: address,
    _routerTokenA: address,
    _routerTokenB: address,
  ):
    assert empty(address) not in [_addyRegistry, _routerTokenA, _routerTokenB] # dev: invalid address
    ADDY_REGISTRY = _addyRegistry
    ROUTER_TOKENA = _routerTokenA
    ROUTER_TOKENB = _routerTokenB


#################
# Yield Helpers #
#################


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    if _assetAmount == 0 or _asset == empty(address) or _vaultToken == empty(address):
        return 0

    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)

    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = staticcall LegoRegistry(legoRegistry).legoIdToType(i)
        if legoType != LegoType.YIELD_OPP:
            continue

        legoAddr: address = staticcall LegoRegistry(legoRegistry).getLegoAddr(i)
        vaultTokenAmount: uint256 = staticcall LegoYield(legoAddr).getVaultTokenAmount(_asset, _assetAmount, _vaultToken)
        if vaultTokenAmount != 0:
            return vaultTokenAmount

    return 0


@view
@external
def getLegoFromVaultToken(_vaultToken: address) -> (uint256, address, String[64]):
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = staticcall LegoRegistry(legoRegistry).legoIdToType(i)
        if legoType != LegoType.YIELD_OPP:
            continue

        legoInfo: registry.AddyInfo = staticcall LegoRegistry(legoRegistry).getLegoInfo(i)
        if staticcall LegoYield(legoInfo.addr).isVaultToken(_vaultToken):
            return i, legoInfo.addr, legoInfo.description
    return 0, empty(address), ""


@view
@external
def getUnderlyingData(_asset: address, _amount: uint256) -> UnderlyingData:
    if _amount == 0 or _asset == empty(address):
        return empty(UnderlyingData)

    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    oracleRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)

    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = staticcall LegoRegistry(legoRegistry).legoIdToType(i)
        if legoType != LegoType.YIELD_OPP:
            continue

        legoInfo: registry.AddyInfo = staticcall LegoRegistry(legoRegistry).getLegoInfo(i)
        asset: address = empty(address)
        underlyingAmount: uint256 = 0
        usdValue: uint256 = 0
        asset, underlyingAmount, usdValue = staticcall LegoYield(legoInfo.addr).getUnderlyingData(_asset, _amount, oracleRegistry)
        if asset != empty(address):
            return UnderlyingData(
                asset=asset,
                amount=underlyingAmount,
                usdValue=usdValue,
                legoId=i,
                legoAddr=legoInfo.addr,
                legoDesc=legoInfo.description,
            )

    return UnderlyingData(
        asset=_asset,
        amount=_amount,
        usdValue=staticcall OracleRegistry(oracleRegistry).getUsdValue(_asset, _amount),
        legoId=0,
        legoAddr=empty(address),
        legoDesc="",
    )


########################
# Dex: Swap High Level #
########################


@external
def getRoutesAndSwapInstructionsAmountOut(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _slippage: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]:
    routes: DynArray[SwapRoute, MAX_ROUTES] = self._getBestSwapRoutesAmountOut(_tokenIn, _tokenOut, _amountIn, _includeLegoIds)
    return self._prepareSwapInstructionsAmountOut(_slippage, routes)


@external
def getRoutesAndSwapInstructionsAmountIn(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _amountInAvailable: uint256,
    _slippage: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]:
    routes: DynArray[SwapRoute, MAX_ROUTES] = self._getBestSwapRoutesAmountIn(_tokenIn, _tokenOut, _amountOut, _includeLegoIds)
    if len(routes) == 0:
        return []

    # let's re-run the routes with amountIn as input (this is more accurate, for example, Aerodrome doesn't have getAmountIn for stable pools
    amountIn: uint256 = min(_amountInAvailable, routes[0].amountIn)
    routes = self._getBestSwapRoutesAmountOut(_tokenIn, _tokenOut, amountIn, _includeLegoIds)
    return self._prepareSwapInstructionsAmountOut(_slippage, routes)


########################
# Dex: Swap Amount Out #
########################


# prepare swap instructions (amountIn as input)


@external
def prepareSwapInstructionsAmountOut(_slippage: uint256, _routes: DynArray[SwapRoute, MAX_ROUTES]) -> DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]:
    return self._prepareSwapInstructionsAmountOut(_slippage, _routes)


@internal
def _prepareSwapInstructionsAmountOut(_slippage: uint256, _routes: DynArray[SwapRoute, MAX_ROUTES]) -> DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]:
    if len(_routes) == 0:
        return []

    instructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS] = []

    # start with first route
    prevRoute: SwapRoute = _routes[0]
    prevInstruction: SwapInstruction = self._createNewInstruction(prevRoute, _slippage)

    # iterate thru swap routes, skip first
    for i: uint256 in range(1, len(_routes), bound=MAX_ROUTES):
        newRoute: SwapRoute = _routes[i]
        assert prevRoute.tokenOut == newRoute.tokenIn # dev: invalid route

        # add to previous instruction
        if prevRoute.legoId == newRoute.legoId:
            prevInstruction.minAmountOut = newRoute.amountOut * (HUNDRED_PERCENT - _slippage) // HUNDRED_PERCENT
            prevInstruction.tokenPath.append(newRoute.tokenOut)
            prevInstruction.poolPath.append(newRoute.pool)
        
        # create new instruction
        else:
            instructions.append(prevInstruction)
            prevInstruction = self._createNewInstruction(newRoute, _slippage)

        # set previous item
        prevRoute = newRoute

    # add last instruction
    instructions.append(prevInstruction)
    return instructions


@view
@internal
def _createNewInstruction(_route: SwapRoute, _slippage: uint256) -> SwapInstruction:
    return SwapInstruction(
        legoId=_route.legoId,
        amountIn=_route.amountIn,
        minAmountOut=_route.amountOut * (HUNDRED_PERCENT - _slippage) // HUNDRED_PERCENT,
        tokenPath=[_route.tokenIn, _route.tokenOut],
        poolPath=[_route.pool],
    )


# best swap routes (amountIn as input)


@external
def getBestSwapRoutesAmountOut(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> DynArray[SwapRoute, MAX_ROUTES]:
    return self._getBestSwapRoutesAmountOut(_tokenIn, _tokenOut, _amountIn, _includeLegoIds)


@internal
def _getBestSwapRoutesAmountOut(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> DynArray[SwapRoute, MAX_ROUTES]:
    if _tokenIn == _tokenOut or _amountIn == 0 or empty(address) in [_tokenIn, _tokenOut]:
        return []

    bestSwapRoutes: DynArray[SwapRoute, MAX_ROUTES] = []

    # required data
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    routerTokenA: address = ROUTER_TOKENA
    routerTokenB: address = ROUTER_TOKENB

    # direct swap route
    directSwapRoute: SwapRoute = self._getBestSwapAmountOutSinglePool(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry, _includeLegoIds)

    # check with router pools
    withRouterHopAmountOut: uint256 = 0
    withHopRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
    withRouterHopAmountOut, withHopRoutes = self._getBestSwapAmountOutWithRouterPool(routerTokenA, routerTokenB, _tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry, _includeLegoIds)

    # compare direct swap route with hop routes
    if directSwapRoute.amountOut > withRouterHopAmountOut:
        bestSwapRoutes = [directSwapRoute]

    # update router token pool (if possible)
    elif withRouterHopAmountOut != 0:
        bestSwapRoutes = withHopRoutes

    return bestSwapRoutes


# check various routes via core router pools


@external
def getBestSwapAmountOutWithRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    return self._getBestSwapAmountOutWithRouterPool(ROUTER_TOKENA, ROUTER_TOKENB, _tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry, _includeLegoIds)


@internal
def _getBestSwapAmountOutWithRouterPool(
    _routerTokenA: address,
    _routerTokenB: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):

    # nothing to do, already have router pool to use
    if self._isRouterPool(_tokenIn, _tokenOut, _routerTokenA, _routerTokenB):
        return 0, []

    isMultiHop: bool = False
    finalAmountOut: uint256 = 0
    bestSwapRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
    firstRoute: SwapRoute = empty(SwapRoute)
    secondRoute: SwapRoute = empty(SwapRoute)

    # usdc -> weth -> tokenOut
    if _tokenIn == _routerTokenA:
        firstRoute = self._getSwapAmountOutViaRouterPool(_routerTokenA, _routerTokenB, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)
        secondRoute = self._getBestSwapAmountOutSinglePool(_routerTokenB, _tokenOut, firstRoute.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # tokenIn -> weth -> usdc
    elif _tokenOut == _routerTokenA:
        firstRoute = self._getBestSwapAmountOutSinglePool(_tokenIn, _routerTokenB, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)
        secondRoute = self._getSwapAmountOutViaRouterPool(_routerTokenB, _routerTokenA, firstRoute.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # weth -> usdc -> tokenOut
    elif _tokenIn == _routerTokenB:
        firstRoute = self._getSwapAmountOutViaRouterPool(_routerTokenB, _routerTokenA, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)
        secondRoute = self._getBestSwapAmountOutSinglePool(_routerTokenA, _tokenOut, firstRoute.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # tokenIn -> usdc -> weth
    elif _tokenOut == _routerTokenB:
        firstRoute = self._getBestSwapAmountOutSinglePool(_tokenIn, _routerTokenA, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)
        secondRoute = self._getSwapAmountOutViaRouterPool(_routerTokenA, _routerTokenB, firstRoute.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # let's try multi hop routes
    else:
        isMultiHop = True

        # router token A as starting point
        viaRouterTokenAAmountOut: uint256 = 0
        viaRouterTokenARoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenAAmountOut, viaRouterTokenARoutes = self._checkRouterPoolForMiddleSwapAmountOut(_routerTokenA, _routerTokenB, _tokenIn, _tokenOut, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)

        # router token B as starting point
        viaRouterTokenBAmountOut: uint256 = 0
        viaRouterTokenBRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenBAmountOut, viaRouterTokenBRoutes = self._checkRouterPoolForMiddleSwapAmountOut(_routerTokenB, _routerTokenA, _tokenIn, _tokenOut, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)

        # compare
        if viaRouterTokenAAmountOut > viaRouterTokenBAmountOut:
            finalAmountOut = viaRouterTokenAAmountOut
            bestSwapRoutes = viaRouterTokenARoutes
        elif viaRouterTokenBAmountOut != 0:
            finalAmountOut = viaRouterTokenBAmountOut
            bestSwapRoutes = viaRouterTokenBRoutes

    if not isMultiHop:
        finalAmountOut = secondRoute.amountOut
        bestSwapRoutes = [firstRoute, secondRoute]

    return finalAmountOut, bestSwapRoutes


@internal
def _checkRouterPoolForMiddleSwapAmountOut(
    _firstRouterTokenHop: address,
    _secondRouterTokenHop: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):
    secondHopToTokenOut: SwapRoute = empty(SwapRoute)

    # tokenIn -> first Router Token
    tokenInToFirstHop: SwapRoute = self._getBestSwapAmountOutSinglePool(_tokenIn, _firstRouterTokenHop, _amountIn, _numLegos, _legoRegistry, _includeLegoIds)
    if tokenInToFirstHop.amountOut == 0:
        return 0, []

    # first Router Token -> tokenOut
    firstHopToTokenOut: SwapRoute = self._getBestSwapAmountOutSinglePool(_firstRouterTokenHop, _tokenOut, tokenInToFirstHop.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # first Router Token -> second Router Token -- this will always happen in router pools (i.e. usdc <-> weth)
    firstHopToSecondHop: SwapRoute = self._getSwapAmountOutViaRouterPool(_firstRouterTokenHop, _secondRouterTokenHop, tokenInToFirstHop.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # second Router Token -> tokenOut
    if firstHopToSecondHop.amountOut != 0:
        secondHopToTokenOut = self._getBestSwapAmountOutSinglePool(_secondRouterTokenHop, _tokenOut, firstHopToSecondHop.amountOut, _numLegos, _legoRegistry, _includeLegoIds)

    # compare routes
    if firstHopToTokenOut.amountOut > secondHopToTokenOut.amountOut:
        return firstHopToTokenOut.amountOut, [tokenInToFirstHop, firstHopToTokenOut]
    elif secondHopToTokenOut.amountOut != 0:
        return secondHopToTokenOut.amountOut, [tokenInToFirstHop, firstHopToSecondHop, secondHopToTokenOut]
    return 0, []


# single pool


@external
def getBestSwapAmountOutSinglePool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> SwapRoute:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    return self._getBestSwapAmountOutSinglePool(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry, _includeLegoIds)


@internal
def _getBestSwapAmountOutSinglePool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> SwapRoute:

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=_amountIn,
        amountOut=0,
    )

    shouldCheckLegoIds: bool = len(_includeLegoIds) != 0
    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):

        # skip if we should check lego ids and it's not in the list
        if shouldCheckLegoIds and i not in _includeLegoIds:
            continue

        # get lego info
        legoType: LegoType = staticcall LegoRegistry(_legoRegistry).legoIdToType(i)
        if legoType != LegoType.DEX:
            continue

        legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(i)
        pool: address = empty(address)
        amountOut: uint256 = 0
        pool, amountOut = staticcall LegoDex(legoAddr).getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn)

        # compare best
        if pool != empty(address) and amountOut > bestRoute.amountOut:
            bestRoute.pool = pool
            bestRoute.amountOut = amountOut
            bestRoute.legoId = i

    return bestRoute


# router pool only


@external
def getSwapAmountOutViaRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> SwapRoute:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    return self._getSwapAmountOutViaRouterPool(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry, _includeLegoIds)


@internal
def _getSwapAmountOutViaRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> SwapRoute:

    # NOTE: _tokenIn and _tokenOut need to be ROUTER_TOKENA/ROUTER_TOKENB -- in the `getCoreRouterPool()` pool

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=_amountIn,
        amountOut=0,
    )

    shouldCheckLegoIds: bool = len(_includeLegoIds) != 0
    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):

        # skip if we should check lego ids and it's not in the list
        if shouldCheckLegoIds and i not in _includeLegoIds:
            continue

        # get lego info
        legoType: LegoType = staticcall LegoRegistry(_legoRegistry).legoIdToType(i)
        if legoType != LegoType.DEX:
            continue

        # get router pool
        legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(i)
        pool: address = staticcall LegoDex(legoAddr).getCoreRouterPool()
        if pool == empty(address):
            continue
        
        amountOut: uint256 = staticcall LegoDex(legoAddr).getSwapAmountOut(pool, _tokenIn, _tokenOut, _amountIn)
        
        # compare best
        if amountOut > bestRoute.amountOut:
            bestRoute.pool = pool
            bestRoute.amountOut = amountOut
            bestRoute.legoId = i

    return bestRoute


#######################
# Dex: Swap Amount In #
#######################


# best swap routes (amountOut as input)


@external
def getBestSwapRoutesAmountIn(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> DynArray[SwapRoute, MAX_ROUTES]:
    return self._getBestSwapRoutesAmountIn(_tokenIn, _tokenOut, _amountOut, _includeLegoIds)


@internal
def _getBestSwapRoutesAmountIn(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> DynArray[SwapRoute, MAX_ROUTES]:
    if _tokenIn == _tokenOut or _amountOut == 0 or empty(address) in [_tokenIn, _tokenOut]:
        return []

    bestSwapRoutes: DynArray[SwapRoute, MAX_ROUTES] = []

    # required data
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    routerTokenA: address = ROUTER_TOKENA
    routerTokenB: address = ROUTER_TOKENB

    # direct swap route
    directSwapRoute: SwapRoute = self._getBestSwapAmountInSinglePool(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry, _includeLegoIds)

    # check with router pools
    withRouterHopAmountIn: uint256 = 0
    withHopRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
    withRouterHopAmountIn, withHopRoutes = self._getBestSwapAmountInWithRouterPool(routerTokenA, routerTokenB, _tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry, _includeLegoIds)

    # compare direct swap route with hop routes
    if directSwapRoute.amountIn < withRouterHopAmountIn:
        bestSwapRoutes = [directSwapRoute]

    # update router token pool (if possible)
    elif withRouterHopAmountIn != max_value(uint256):
        bestSwapRoutes = withHopRoutes

    return bestSwapRoutes


# check various routes via core router pools


@external
def getBestSwapAmountInWithRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    return self._getBestSwapAmountInWithRouterPool(ROUTER_TOKENA, ROUTER_TOKENB, _tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry, _includeLegoIds)


@internal
def _getBestSwapAmountInWithRouterPool(
    _routerTokenA: address,
    _routerTokenB: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):

    # nothing to do, already have router pool to use
    if self._isRouterPool(_tokenIn, _tokenOut, _routerTokenA, _routerTokenB):
        return max_value(uint256), []

    isMultiHop: bool = False
    finalAmountIn: uint256 = max_value(uint256)
    bestSwapRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
    firstRoute: SwapRoute = empty(SwapRoute)
    secondRoute: SwapRoute = empty(SwapRoute)

    # usdc -> weth -> tokenOut
    if _tokenIn == _routerTokenA:
        secondRoute = self._getBestSwapAmountInSinglePool(_routerTokenB, _tokenOut, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)
        firstRoute = self._getSwapAmountInViaRouterPool(_routerTokenA, _routerTokenB, secondRoute.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # tokenIn -> weth -> usdc
    elif _tokenOut == _routerTokenA:
        secondRoute = self._getSwapAmountInViaRouterPool(_routerTokenB, _routerTokenA, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)
        firstRoute = self._getBestSwapAmountInSinglePool(_tokenIn, _routerTokenB, secondRoute.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # weth -> usdc -> tokenOut
    elif _tokenIn == _routerTokenB:
        secondRoute = self._getBestSwapAmountInSinglePool(_routerTokenA, _tokenOut, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)
        firstRoute = self._getSwapAmountInViaRouterPool(_routerTokenB, _routerTokenA, secondRoute.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # tokenIn -> usdc -> weth
    elif _tokenOut == _routerTokenB:
        secondRoute = self._getSwapAmountInViaRouterPool(_routerTokenA, _routerTokenB, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)
        firstRoute = self._getBestSwapAmountInSinglePool(_tokenIn, _routerTokenA, secondRoute.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # let's try multi hop routes
    else:
        isMultiHop = True

        # router token A as starting point
        viaRouterTokenAAmountIn: uint256 = 0
        viaRouterTokenARoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenAAmountIn, viaRouterTokenARoutes = self._checkRouterPoolForMiddleSwapAmountIn(_routerTokenA, _routerTokenB, _tokenIn, _tokenOut, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)

        # router token B as starting point
        viaRouterTokenBAmountIn: uint256 = 0
        viaRouterTokenBRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenBAmountIn, viaRouterTokenBRoutes = self._checkRouterPoolForMiddleSwapAmountIn(_routerTokenB, _routerTokenA, _tokenIn, _tokenOut, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)

        # compare
        if viaRouterTokenAAmountIn < viaRouterTokenBAmountIn:
            finalAmountIn = viaRouterTokenAAmountIn
            bestSwapRoutes = viaRouterTokenARoutes
        elif viaRouterTokenBAmountIn != max_value(uint256):
            finalAmountIn = viaRouterTokenBAmountIn
            bestSwapRoutes = viaRouterTokenBRoutes

    if not isMultiHop:
        finalAmountIn = firstRoute.amountIn
        bestSwapRoutes = [firstRoute, secondRoute]

    return finalAmountIn, bestSwapRoutes


@internal
def _checkRouterPoolForMiddleSwapAmountIn(
    _firstRouterToken: address,
    _secondRouterToken: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):
    tokenInToFirstHop: SwapRoute = empty(SwapRoute)
    tokenInToFirstHop.amountIn = max_value(uint256)

    # second Router Token -> tokenOut
    secondHopToTokenOut: SwapRoute = self._getBestSwapAmountInSinglePool(_secondRouterToken, _tokenOut, _amountOut, _numLegos, _legoRegistry, _includeLegoIds)
    if secondHopToTokenOut.amountIn == max_value(uint256):
        return max_value(uint256), []

    # tokenIn -> second Router Token
    tokenInToSecondHop: SwapRoute = self._getBestSwapAmountInSinglePool(_tokenIn, _secondRouterToken, secondHopToTokenOut.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # first Router Token -> second Router Token -- this will always happen in router pools (i.e. usdc <-> weth)
    firstHopToSecondHop: SwapRoute = self._getSwapAmountInViaRouterPool(_firstRouterToken, _secondRouterToken, secondHopToTokenOut.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # tokenIn -> first Router Token
    if firstHopToSecondHop.amountIn != max_value(uint256):
        tokenInToFirstHop = self._getBestSwapAmountInSinglePool(_tokenIn, _firstRouterToken, firstHopToSecondHop.amountIn, _numLegos, _legoRegistry, _includeLegoIds)

    # compare routes
    if tokenInToSecondHop.amountIn < tokenInToFirstHop.amountIn:
        return tokenInToSecondHop.amountIn, [tokenInToSecondHop, secondHopToTokenOut]
    elif tokenInToFirstHop.amountIn != max_value(uint256):
        return tokenInToFirstHop.amountIn, [tokenInToFirstHop, firstHopToSecondHop, secondHopToTokenOut]
    return max_value(uint256), []


# single pool


@external
def getBestSwapAmountInSinglePool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> SwapRoute:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    return self._getBestSwapAmountInSinglePool(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry, _includeLegoIds)


@internal
def _getBestSwapAmountInSinglePool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> SwapRoute:

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=max_value(uint256),
        amountOut=_amountOut,
    )

    shouldCheckLegoIds: bool = len(_includeLegoIds) != 0
    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):

        # skip if we should check lego ids and it's not in the list
        if shouldCheckLegoIds and i not in _includeLegoIds:
            continue

        legoType: LegoType = staticcall LegoRegistry(_legoRegistry).legoIdToType(i)
        if legoType != LegoType.DEX:
            continue

        pool: address = empty(address)
        amountIn: uint256 = max_value(uint256)
        legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(i)
        pool, amountIn = staticcall LegoDex(legoAddr).getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut)

        # compare best
        if pool != empty(address) and amountIn != 0 and amountIn < bestRoute.amountIn:
            bestRoute.pool = pool
            bestRoute.amountIn = amountIn
            bestRoute.legoId = i

    return bestRoute


# router pool only


@external
def getSwapAmountInViaRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> SwapRoute:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegosRaw()
    return self._getSwapAmountInViaRouterPool(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry, _includeLegoIds)


@internal
def _getSwapAmountInViaRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _includeLegoIds: DynArray[uint256, MAX_LEGOS],
) -> SwapRoute:

    # NOTE: _tokenIn and _tokenOut need to be ROUTER_TOKENA/ROUTER_TOKENB -- in the `getCoreRouterPool()` pool

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=max_value(uint256),
        amountOut=_amountOut,
    )

    shouldCheckLegoIds: bool = len(_includeLegoIds) != 0
    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):

        # skip if we should check lego ids and it's not in the list
        if shouldCheckLegoIds and i not in _includeLegoIds:
            continue

        legoType: LegoType = staticcall LegoRegistry(_legoRegistry).legoIdToType(i)
        if legoType != LegoType.DEX:
            continue

        # get router pool
        legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(i)
        pool: address = staticcall LegoDex(legoAddr).getCoreRouterPool()
        if pool == empty(address):
            continue
        
        amountIn: uint256 = staticcall LegoDex(legoAddr).getSwapAmountIn(pool, _tokenIn, _tokenOut, _amountOut)
        
        # compare best
        if amountIn != 0 and amountIn < bestRoute.amountIn:
            bestRoute.pool = pool
            bestRoute.amountIn = amountIn
            bestRoute.legoId = i

    return bestRoute


@view
@internal
def _isRouterPool(_tokenIn: address, _tokenOut: address, _routerTokenA: address, _routerTokenB: address) -> bool:
    return _tokenIn in [_routerTokenA, _routerTokenB] and _tokenOut in [_routerTokenA, _routerTokenB]
