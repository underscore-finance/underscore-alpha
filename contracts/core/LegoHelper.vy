# @version 0.4.0

from interfaces import LegoYield
from interfaces import LegoDex
from ethereum.ercs import IERC20

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view
    def isValidLegoId(_legoId: uint256) -> bool: view
    def legoInfo(_legoId: uint256) -> LegoInfo: view
    def numLegos() -> uint256: view

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

struct UnderlyingData:
    asset: address
    amount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    legoDesc: String[64]

struct LegoInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
    legoType: LegoType

ADDY_REGISTRY: public(immutable(address))

# key router tokens
ROUTER_TOKENA: public(immutable(address))
ROUTER_TOKENB: public(immutable(address))

# yield lego ids
AAVE_V3_ID: public(immutable(uint256))
COMPOUND_V3_ID: public(immutable(uint256))
EULER_ID: public(immutable(uint256))
FLUID_ID: public(immutable(uint256))
MOONWELL_ID: public(immutable(uint256))
MORPHO_ID: public(immutable(uint256))
SKY_ID: public(immutable(uint256))

# dex lego ids
UNISWAP_V2_ID: public(immutable(uint256))
UNISWAP_V3_ID: public(immutable(uint256))
AERODROME_ID: public(immutable(uint256))
AERODROME_SLIPSTREAM_ID: public(immutable(uint256))
CURVE_ID: public(immutable(uint256))

MAX_ROUTES: constant(uint256) = 3


@deploy
def __init__(
    _addyRegistry: address,
    _routerTokenA: address,
    _routerTokenB: address,
    # yield lego ids
    _aaveV3Id: uint256,
    _compoundV3Id: uint256,
    _eulerId: uint256,
    _fluidId: uint256,
    _moonwellId: uint256,
    _morphoId: uint256,
    _skyId: uint256,
    # dex lego ids
    _uniswapV2Id: uint256,
    _uniswapV3Id: uint256,
    _aerodromeId: uint256,
    _aerodromeSlipstreamId: uint256,
    _curveId: uint256,
):
    assert empty(address) not in [_addyRegistry, _routerTokenA, _routerTokenB] # dev: invalid address
    ADDY_REGISTRY = _addyRegistry
    ROUTER_TOKENA = _routerTokenA
    ROUTER_TOKENB = _routerTokenB

    # yield lego ids
    legoRegistry: address = staticcall AddyRegistry(_addyRegistry).getAddy(2)
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_aaveV3Id) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_compoundV3Id) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_eulerId) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_fluidId) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_moonwellId) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_morphoId) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_skyId) # dev: invalid id

    AAVE_V3_ID = _aaveV3Id
    COMPOUND_V3_ID = _compoundV3Id
    EULER_ID = _eulerId
    FLUID_ID = _fluidId
    MOONWELL_ID = _moonwellId
    MORPHO_ID = _morphoId
    SKY_ID = _skyId

    # dex lego ids
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_uniswapV2Id) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_uniswapV3Id) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_aerodromeId) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_aerodromeSlipstreamId) # dev: invalid id
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_curveId) # dev: invalid id

    UNISWAP_V2_ID = _uniswapV2Id
    UNISWAP_V3_ID = _uniswapV3Id
    AERODROME_ID = _aerodromeId
    AERODROME_SLIPSTREAM_ID = _aerodromeSlipstreamId
    CURVE_ID = _curveId


###############
# Yield Legos #
###############


@view
@external
def aaveV3() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(AAVE_V3_ID)


@view
@external
def aaveV3Id() -> uint256:
    return AAVE_V3_ID


@view
@external
def compoundV3() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(COMPOUND_V3_ID)


@view
@external
def compoundV3Id() -> uint256:
    return COMPOUND_V3_ID


@view
@external
def euler() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(EULER_ID)


@view
@external
def eulerId() -> uint256:
    return EULER_ID


@view
@external
def fluid() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(FLUID_ID)


@view
@external
def fluidId() -> uint256:
    return FLUID_ID


@view
@external
def moonwell() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(MOONWELL_ID)


@view
@external
def moonwellId() -> uint256:
    return MOONWELL_ID


@view
@external
def morpho() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(MORPHO_ID)


@view
@external
def morphoId() -> uint256:
    return MORPHO_ID


@view
@external
def sky() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(SKY_ID)


@view
@external
def skyId() -> uint256:
    return SKY_ID


#############
# DEX Legos #
#############


@view
@external
def uniswapV2() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(UNISWAP_V2_ID)


@view
@external
def uniswapV2Id() -> uint256:
    return UNISWAP_V2_ID


@view
@external
def uniswapV3() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(UNISWAP_V3_ID)


@view
@external
def uniswapV3Id() -> uint256:
    return UNISWAP_V3_ID


@view
@external
def aerodrome() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(AERODROME_ID)


@view
@external
def aerodromeId() -> uint256:
    return AERODROME_ID


@view
@external
def aerodromeSlipstream() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(AERODROME_SLIPSTREAM_ID)


@view
@external
def aerodromeSlipstreamId() -> uint256:
    return AERODROME_SLIPSTREAM_ID


@view
@external
def curve() -> address:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(CURVE_ID)


@view
@external
def curveId() -> uint256:
    return CURVE_ID


#################
# Yield Helpers #
#################


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    if _assetAmount == 0 or _asset == empty(address) or _vaultToken == empty(address):
        return 0

    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)

    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.YIELD_OPP:
            continue

        vaultTokenAmount: uint256 = staticcall LegoYield(legoInfo.addr).getVaultTokenAmount(_asset, _assetAmount, _vaultToken)
        if vaultTokenAmount != 0:
            return vaultTokenAmount

    return 0


@view
@external
def getLegoFromVaultToken(_vaultToken: address) -> (uint256, address, String[64]):
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.YIELD_OPP:
            continue
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

    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.YIELD_OPP:
            continue

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
# Dex: Swap Amount Out #
########################


@external
def getSwapAmountOutWithData(
    _legoId: uint256,
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
) -> uint256:
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    legoInfo: LegoInfo = staticcall LegoRegistry(legoRegistry).legoInfo(_legoId)
    
    amountOut: uint256 = 0
    if _legoId in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
        amountOut = extcall LegoDexNonStandard(legoInfo.addr).getSwapAmountOut(_pool, _tokenIn, _tokenOut, _amountIn)
    else:
        amountOut = staticcall LegoDex(legoInfo.addr).getSwapAmountOut(_pool, _tokenIn, _tokenOut, _amountIn)
    return amountOut


@external
def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> DynArray[SwapRoute, MAX_ROUTES]:
    if _tokenIn == _tokenOut or _amountIn == 0:
        return []

    bestSwapRoutes: DynArray[SwapRoute, MAX_ROUTES] = []

    # required data
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    routerTokenA: address = ROUTER_TOKENA
    routerTokenB: address = ROUTER_TOKENB

    # direct swap route
    directSwapRoute: SwapRoute = self._getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry)

    # check with router pools
    withRouterHopAmountOut: uint256 = 0
    withHopRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
    withRouterHopAmountOut, withHopRoutes = self._getBestSwapAmountOutWithRouterPool(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry, routerTokenA, routerTokenB)

    # compare direct swap route with hop routes
    if directSwapRoute.amountOut > withRouterHopAmountOut:
        bestSwapRoutes = [directSwapRoute]

    # update router token pool (if possible)
    elif withRouterHopAmountOut != 0:
        bestSwapRoutes = self._replaceRouterPoolToSameLego(_tokenIn, _tokenOut, withHopRoutes, routerTokenA, routerTokenB, legoRegistry)

    return bestSwapRoutes


@internal
def _getBestSwapAmountOutWithRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _routerTokenA: address,
    _routerTokenB: address,
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
        firstRoute = self._getSwapAmountOutViaRouterPool(_routerTokenA, _routerTokenB, _amountIn, _numLegos, _legoRegistry)
        secondRoute = self._getBestSwapAmountOut(_routerTokenB, _tokenOut, firstRoute.amountOut, _numLegos, _legoRegistry)

    # tokenIn -> weth -> usdc
    elif _tokenOut == _routerTokenA:
        firstRoute = self._getBestSwapAmountOut(_tokenIn, _routerTokenB, _amountIn, _numLegos, _legoRegistry)
        secondRoute = self._getSwapAmountOutViaRouterPool(_routerTokenB, _routerTokenA, firstRoute.amountOut, _numLegos, _legoRegistry)

    # weth -> usdc -> tokenOut
    elif _tokenIn == _routerTokenB:
        firstRoute = self._getSwapAmountOutViaRouterPool(_routerTokenB, _routerTokenA, _amountIn, _numLegos, _legoRegistry)
        secondRoute = self._getBestSwapAmountOut(_routerTokenA, _tokenOut, firstRoute.amountOut, _numLegos, _legoRegistry)

    # tokenIn -> usdc -> weth
    elif _tokenOut == _routerTokenB:
        firstRoute = self._getBestSwapAmountOut(_tokenIn, _routerTokenA, _amountIn, _numLegos, _legoRegistry)
        secondRoute = self._getSwapAmountOutViaRouterPool(_routerTokenA, _routerTokenB, firstRoute.amountOut, _numLegos, _legoRegistry)

    # let's try multi hop routes
    else:
        isMultiHop = True

        # router token A as starting point
        viaRouterTokenAAmountOut: uint256 = 0
        viaRouterTokenARoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenAAmountOut, viaRouterTokenARoutes = self._checkRouterPoolForMiddleSwapAmountOut(_tokenIn, _tokenOut, _amountIn, _numLegos, _legoRegistry, _routerTokenA, _routerTokenB)

        # router token B as starting point
        viaRouterTokenBAmountOut: uint256 = 0
        viaRouterTokenBRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenBAmountOut, viaRouterTokenBRoutes = self._checkRouterPoolForMiddleSwapAmountOut(_tokenIn, _tokenOut, _amountIn, _numLegos, _legoRegistry, _routerTokenB, _routerTokenA)

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
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _firstRouterTokenHop: address,
    _secondRouterTokenHop: address,
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):
    secondHopToTokenOut: SwapRoute = empty(SwapRoute)

    # tokenIn -> first Router Token
    tokenInToFirstHop: SwapRoute = self._getBestSwapAmountOut(_tokenIn, _firstRouterTokenHop, _amountIn, _numLegos, _legoRegistry)
    if tokenInToFirstHop.amountOut == 0:
        return 0, []

    # first Router Token -> tokenOut
    firstHopToTokenOut: SwapRoute = self._getBestSwapAmountOut(_firstRouterTokenHop, _tokenOut, tokenInToFirstHop.amountOut, _numLegos, _legoRegistry)

    # first Router Token -> second Router Token -- this will always happen in router pools (i.e. usdc <-> weth)
    firstHopToSecondHop: SwapRoute = self._getSwapAmountOutViaRouterPool(_firstRouterTokenHop, _secondRouterTokenHop, tokenInToFirstHop.amountOut, _numLegos, _legoRegistry)

    # second Router Token -> tokenOut
    if firstHopToSecondHop.amountOut != 0:
        secondHopToTokenOut = self._getBestSwapAmountOut(_secondRouterTokenHop, _tokenOut, firstHopToSecondHop.amountOut, _numLegos, _legoRegistry)

    # compare routes
    if firstHopToTokenOut.amountOut > secondHopToTokenOut.amountOut:
        return firstHopToTokenOut.amountOut, [tokenInToFirstHop, firstHopToTokenOut]
    elif secondHopToTokenOut.amountOut != 0:
        return secondHopToTokenOut.amountOut, [tokenInToFirstHop, firstHopToSecondHop, secondHopToTokenOut]
    return 0, []


@internal
def _getBestSwapAmountOut(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=_amountIn,
        amountOut=0,
    )

    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(_legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.DEX:
            continue

        pool: address = empty(address)
        amountOut: uint256 = 0
        if i in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
            pool, amountOut = extcall LegoDexNonStandard(legoInfo.addr).getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn)
        else:
            pool, amountOut = staticcall LegoDex(legoInfo.addr).getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn)

        # compare best
        if pool != empty(address) and amountOut > bestRoute.amountOut:
            bestRoute.pool = pool
            bestRoute.amountOut = amountOut
            bestRoute.legoId = i

    return bestRoute


@internal
def _getSwapAmountOutViaRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=_amountIn,
        amountOut=0,
    )

    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(_legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.DEX:
            continue

        # get router pool
        pool: address = staticcall LegoDex(legoInfo.addr).getCoreRouterPool()
        if pool == empty(address):
            continue
        
        amountOut: uint256 = 0
        if i in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
            amountOut = extcall LegoDexNonStandard(legoInfo.addr).getSwapAmountOut(pool, _tokenIn, _tokenOut, _amountIn)
        else:
            amountOut = staticcall LegoDex(legoInfo.addr).getSwapAmountOut(pool, _tokenIn, _tokenOut, _amountIn)
        
        # compare best
        if amountOut > bestRoute.amountOut:
            bestRoute.pool = pool
            bestRoute.amountOut = amountOut
            bestRoute.legoId = i

    return bestRoute


#######################
# Dex: Swap Amount In #
#######################


@external
def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> DynArray[SwapRoute, MAX_ROUTES]:
    if _tokenIn == _tokenOut or _amountOut == 0:
        return []

    bestSwapRoutes: DynArray[SwapRoute, MAX_ROUTES] = []

    # required data
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    routerTokenA: address = ROUTER_TOKENA
    routerTokenB: address = ROUTER_TOKENB

    # direct swap route
    directSwapRoute: SwapRoute = self._getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry)

    # check with router pools
    withRouterHopAmountIn: uint256 = 0
    withHopRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
    withRouterHopAmountIn, withHopRoutes = self._getBestSwapAmountInWithRouterPool(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry, routerTokenA, routerTokenB)

    # compare direct swap route with hop routes
    if directSwapRoute.amountIn < withRouterHopAmountIn:
        bestSwapRoutes = [directSwapRoute]

    # update router token pool (if possible)
    elif withRouterHopAmountIn != max_value(uint256):
        bestSwapRoutes = self._replaceRouterPoolToSameLego(_tokenIn, _tokenOut, withHopRoutes, routerTokenA, routerTokenB, legoRegistry)

    return bestSwapRoutes


@internal
def _getBestSwapAmountInWithRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _routerTokenA: address,
    _routerTokenB: address,
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
        secondRoute = self._getBestSwapAmountIn(_routerTokenB, _tokenOut, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getSwapAmountInViaRouterPool(_routerTokenA, _routerTokenB, secondRoute.amountIn, _numLegos, _legoRegistry)

    # tokenIn -> weth -> usdc
    elif _tokenOut == _routerTokenA:
        secondRoute = self._getSwapAmountInViaRouterPool(_routerTokenB, _routerTokenA, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getBestSwapAmountIn(_tokenIn, _routerTokenB, secondRoute.amountIn, _numLegos, _legoRegistry)

    # weth -> usdc -> tokenOut
    elif _tokenIn == _routerTokenB:
        secondRoute = self._getBestSwapAmountIn(_routerTokenA, _tokenOut, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getSwapAmountInViaRouterPool(_routerTokenB, _routerTokenA, secondRoute.amountIn, _numLegos, _legoRegistry)

    # tokenIn -> usdc -> weth
    elif _tokenOut == _routerTokenB:
        secondRoute = self._getSwapAmountInViaRouterPool(_routerTokenA, _routerTokenB, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getBestSwapAmountIn(_tokenIn, _routerTokenA, secondRoute.amountIn, _numLegos, _legoRegistry)

    # let's try multi hop routes
    else:
        isMultiHop = True

        # router token A as starting point
        viaRouterTokenAAmountIn: uint256 = 0
        viaRouterTokenARoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenAAmountIn, viaRouterTokenARoutes = self._checkRouterPoolForMiddleSwapAmountIn(_tokenIn, _tokenOut, _amountOut, _numLegos, _legoRegistry, _routerTokenA, _routerTokenB)

        # router token B as starting point
        viaRouterTokenBAmountIn: uint256 = 0
        viaRouterTokenBRoutes: DynArray[SwapRoute, MAX_ROUTES] = []
        viaRouterTokenBAmountIn, viaRouterTokenBRoutes = self._checkRouterPoolForMiddleSwapAmountIn(_tokenIn, _tokenOut, _amountOut, _numLegos, _legoRegistry, _routerTokenB, _routerTokenA)

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
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
    _firstRouterToken: address,
    _secondRouterToken: address,
) -> (uint256, DynArray[SwapRoute, MAX_ROUTES]):
    tokenInToFirstHop: SwapRoute = empty(SwapRoute)
    tokenInToFirstHop.amountIn = max_value(uint256)

    # second Router Token -> tokenOut
    secondHopToTokenOut: SwapRoute = self._getBestSwapAmountIn(_secondRouterToken, _tokenOut, _amountOut, _numLegos, _legoRegistry)
    if secondHopToTokenOut.amountIn == max_value(uint256):
        return max_value(uint256), []

    # tokenIn -> second Router Token
    tokenInToSecondHop: SwapRoute = self._getBestSwapAmountIn(_tokenIn, _secondRouterToken, secondHopToTokenOut.amountIn, _numLegos, _legoRegistry)

    # first Router Token -> second Router Token -- this will always happen in router pools (i.e. usdc <-> weth)
    firstHopToSecondHop: SwapRoute = self._getSwapAmountInViaRouterPool(_firstRouterToken, _secondRouterToken, secondHopToTokenOut.amountIn, _numLegos, _legoRegistry)

    # tokenIn -> first Router Token
    if firstHopToSecondHop.amountIn != max_value(uint256):
        tokenInToFirstHop = self._getBestSwapAmountIn(_tokenIn, _firstRouterToken, firstHopToSecondHop.amountIn, _numLegos, _legoRegistry)

    # compare routes
    if tokenInToSecondHop.amountIn < tokenInToFirstHop.amountIn:
        return tokenInToSecondHop.amountIn, [tokenInToSecondHop, secondHopToTokenOut]
    elif tokenInToFirstHop.amountIn != max_value(uint256):
        return tokenInToFirstHop.amountIn, [tokenInToFirstHop, firstHopToSecondHop, secondHopToTokenOut]
    return max_value(uint256), []


@internal
def _getBestSwapAmountIn(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=max_value(uint256),
        amountOut=_amountOut,
    )

    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(_legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.DEX:
            continue

        pool: address = empty(address)
        amountIn: uint256 = max_value(uint256)
        if i in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
            pool, amountIn = extcall LegoDexNonStandard(legoInfo.addr).getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut)
        else:
            pool, amountIn = staticcall LegoDex(legoInfo.addr).getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut)

        # compare best
        if pool != empty(address) and amountIn != 0 and amountIn < bestRoute.amountIn:
            bestRoute.pool = pool
            bestRoute.amountIn = amountIn
            bestRoute.legoId = i

    return bestRoute


@internal
def _getSwapAmountInViaRouterPool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    bestRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=max_value(uint256),
        amountOut=_amountOut,
    )

    for i: uint256 in range(1, _numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(_legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.DEX:
            continue

        # get router pool
        pool: address = staticcall LegoDex(legoInfo.addr).getCoreRouterPool()
        if pool == empty(address):
            continue
        
        amountIn: uint256 = max_value(uint256)
        if i in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
            amountIn = extcall LegoDexNonStandard(legoInfo.addr).getSwapAmountIn(pool, _tokenIn, _tokenOut, _amountOut)
        else:
            amountIn = staticcall LegoDex(legoInfo.addr).getSwapAmountIn(pool, _tokenIn, _tokenOut, _amountOut)
        
        # compare best
        if amountIn != 0 and amountIn < bestRoute.amountIn:
            bestRoute.pool = pool
            bestRoute.amountIn = amountIn
            bestRoute.legoId = i

    return bestRoute


####################
# Shared Utilities #
####################


@internal
def _replaceRouterPoolToSameLego(
    _tokenIn: address,
    _tokenOut: address,
    _hopSwapRoutes: DynArray[SwapRoute, MAX_ROUTES],
    _routerTokenA: address,
    _routerTokenB: address,
    _legoRegistry: address,
) -> DynArray[SwapRoute, MAX_ROUTES]:
    updatedRoutes: DynArray[SwapRoute, MAX_ROUTES] = _hopSwapRoutes

    # 1 pool -- nothing to do here
    if len(_hopSwapRoutes) == 1:
        return _hopSwapRoutes

    # 2 pools
    elif len(_hopSwapRoutes) == 2:
        firstRoute: SwapRoute = _hopSwapRoutes[0]
        lastRoute: SwapRoute = _hopSwapRoutes[1]

        if self._isRouterPool(firstRoute.tokenIn, firstRoute.tokenOut, _routerTokenA, _routerTokenB):
            firstRoute.legoId, firstRoute.pool = self._getNewRouterPool(firstRoute.legoId, firstRoute.pool, lastRoute.legoId, _legoRegistry)
        elif self._isRouterPool(lastRoute.tokenIn, lastRoute.tokenOut, _routerTokenA, _routerTokenB):
            lastRoute.legoId, lastRoute.pool = self._getNewRouterPool(lastRoute.legoId, lastRoute.pool, firstRoute.legoId, _legoRegistry)

        if firstRoute.pool != empty(address) and lastRoute.pool != empty(address):
            updatedRoutes = [firstRoute, lastRoute]

    # 3 pools -- router pool must be middle route
    elif len(_hopSwapRoutes) == 3:
        firstRoute: SwapRoute = _hopSwapRoutes[0]
        middleRoute: SwapRoute = _hopSwapRoutes[1]
        lastRoute: SwapRoute = _hopSwapRoutes[2]

        # only switching if first and last route legos are the same
        if firstRoute.legoId == lastRoute.legoId and self._isRouterPool(middleRoute.tokenIn, middleRoute.tokenOut, _routerTokenA, _routerTokenB):
            middleRoute.legoId, middleRoute.pool = self._getNewRouterPool(middleRoute.legoId, middleRoute.pool, firstRoute.legoId, _legoRegistry)
            if middleRoute.pool != empty(address):
                updatedRoutes = [firstRoute, middleRoute, lastRoute]

    return updatedRoutes


@view
@internal
def _isRouterPool(_tokenIn: address, _tokenOut: address, _routerTokenA: address, _routerTokenB: address) -> bool:
    return _tokenIn in [_routerTokenA, _routerTokenB] and _tokenOut in [_routerTokenA, _routerTokenB]


@internal
def _getNewRouterPool(
    _targetRouteLegoId: uint256,
    _targetPool: address,
    _altRouteLegoId: uint256,
    _legoRegistry: address,
) -> (uint256, address):
    if _targetRouteLegoId == _altRouteLegoId:
        return _targetRouteLegoId, _targetPool

    # get router pool from same lego as other swap route
    legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(_altRouteLegoId)
    return _altRouteLegoId, staticcall LegoDex(legoAddr).getCoreRouterPool()