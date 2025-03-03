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
USDC: public(immutable(address))
WETH: public(immutable(address))

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


@deploy
def __init__(
    _addyRegistry: address,
    _usdc: address,
    _weth: address,
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
    assert empty(address) not in [_addyRegistry, _usdc, _weth] # dev: invalid address
    ADDY_REGISTRY = _addyRegistry
    USDC = _usdc
    WETH = _weth

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
def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> DynArray[SwapRoute, 2]:
    if _tokenIn == _tokenOut or _amountIn == 0:
        return []
    
    # required data
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()

    # check direct swap route
    directSwapRoute: SwapRoute = self._getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry)

    # check hop routes
    withHopAmountOut: uint256 = 0
    hopSwapRoutes: DynArray[SwapRoute, 2] = []
    withHopAmountOut, hopSwapRoutes = self._getBestSwapAmountOutWithHop(_tokenIn, _tokenOut, _amountIn, numLegos, legoRegistry)

    # nothing to do
    if directSwapRoute.pool == empty(address) and withHopAmountOut == 0:
        return []

    # compare with raw amount out
    if directSwapRoute.amountOut > withHopAmountOut:
        return [directSwapRoute]
    return hopSwapRoutes


@internal
def _getBestSwapAmountOutWithHop(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> (uint256, DynArray[SwapRoute, 2]):
    usdc: address = USDC
    weth: address = WETH

    # nothing to do, already have best `directSwapRoute`
    if _tokenIn in [usdc, weth] and _tokenOut in [usdc, weth]:
        return 0, []

    firstRoute: SwapRoute = empty(SwapRoute)
    lastRoute: SwapRoute = empty(SwapRoute)

    # usdc -> weth -> tokenOut
    if _tokenIn == usdc:
        firstRoute = self._getSwapAmountOutWithBridgePool(usdc, weth, _amountIn, _numLegos, _legoRegistry)
        lastRoute = self._getBestSwapAmountOut(weth, _tokenOut, firstRoute.amountOut, _numLegos, _legoRegistry)

    # tokenIn -> weth -> usdc
    elif _tokenOut == usdc:
        firstRoute = self._getBestSwapAmountOut(_tokenIn, weth, _amountIn, _numLegos, _legoRegistry)
        lastRoute = self._getSwapAmountOutWithBridgePool(weth, usdc, firstRoute.amountOut, _numLegos, _legoRegistry)

    # weth -> usdc -> tokenOut
    elif _tokenIn == weth:
        firstRoute = self._getSwapAmountOutWithBridgePool(weth, usdc, _amountIn, _numLegos, _legoRegistry)
        lastRoute = self._getBestSwapAmountOut(usdc, _tokenOut, firstRoute.amountOut, _numLegos, _legoRegistry)

    # tokenIn -> usdc -> weth
    elif _tokenOut == weth:
        firstRoute = self._getBestSwapAmountOut(_tokenIn, usdc, _amountIn, _numLegos, _legoRegistry)
        lastRoute = self._getSwapAmountOutWithBridgePool(usdc, weth, firstRoute.amountOut, _numLegos, _legoRegistry)

    # let's try thru both paths
    else:
        # tokenIn -> usdc -> tokenOut
        usdcRouteA: SwapRoute = self._getBestSwapAmountOut(_tokenIn, usdc, _amountIn, _numLegos, _legoRegistry)
        usdcRouteB: SwapRoute = self._getBestSwapAmountOut(usdc, _tokenOut, usdcRouteA.amountOut, _numLegos, _legoRegistry)

        # tokenIn -> weth -> tokenOut
        wethRouteA: SwapRoute = self._getBestSwapAmountOut(_tokenIn, weth, _amountIn, _numLegos, _legoRegistry)
        wethRouteB: SwapRoute = self._getBestSwapAmountOut(weth, _tokenOut, wethRouteA.amountOut, _numLegos, _legoRegistry)

        # compare routes
        firstRoute = usdcRouteA
        lastRoute = usdcRouteB
        if wethRouteB.amountOut > usdcRouteB.amountOut:
            firstRoute = wethRouteA
            lastRoute = wethRouteB

    return lastRoute.amountOut, [firstRoute, lastRoute]


@internal
def _getBestSwapAmountOut(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    swapRoute: SwapRoute = SwapRoute(
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
        if pool != empty(address) and amountOut > swapRoute.amountOut:
            swapRoute.pool = pool
            swapRoute.amountOut = amountOut
            swapRoute.legoId = i

    return swapRoute


@internal
def _getSwapAmountOutWithBridgePool(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    swapRoute: SwapRoute = SwapRoute(
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

        # get bridge router pool
        pool: address = staticcall LegoDex(legoInfo.addr).getWethUsdcRouterPool()
        if pool == empty(address):
            continue
        
        amountOut: uint256 = 0
        if i in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
            amountOut = extcall LegoDexNonStandard(legoInfo.addr).getSwapAmountOut(pool, _tokenIn, _tokenOut, _amountIn)
        else:
            amountOut = staticcall LegoDex(legoInfo.addr).getSwapAmountOut(pool, _tokenIn, _tokenOut, _amountIn)
        
        # compare best
        if amountOut > swapRoute.amountOut:
            swapRoute.pool = pool
            swapRoute.amountOut = amountOut
            swapRoute.legoId = i

    return swapRoute


#######################
# Dex: Swap Amount In #
#######################


@external
def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> DynArray[SwapRoute, 2]:
    if _tokenIn == _tokenOut or _amountOut == 0:
        return []

    # required data
    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()

    # check direct swap route
    directSwapRoute: SwapRoute = self._getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry)

    # check hop routes
    withHopAmountIn: uint256 = 0
    hopSwapRoutes: DynArray[SwapRoute, 2] = []
    withHopAmountIn, hopSwapRoutes = self._getBestSwapAmountInWithHop(_tokenIn, _tokenOut, _amountOut, numLegos, legoRegistry)

    # compare with raw amount in
    if directSwapRoute.amountIn < withHopAmountIn:
        return [directSwapRoute]
    elif withHopAmountIn != max_value(uint256):
        return hopSwapRoutes
    return []


@internal
def _getBestSwapAmountInWithHop(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> (uint256, DynArray[SwapRoute, 2]):
    usdc: address = USDC
    weth: address = WETH

    # nothing to do, already have best `directSwapRoute`
    if _tokenIn in [usdc, weth] and _tokenOut in [usdc, weth]:
        return max_value(uint256), []

    firstRoute: SwapRoute = empty(SwapRoute)
    lastRoute: SwapRoute = empty(SwapRoute)

    # usdc -> weth -> tokenOut
    if _tokenIn == usdc:
        lastRoute = self._getBestSwapAmountIn(weth, _tokenOut, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getSwapAmountInWithBridgePool(usdc, weth, lastRoute.amountIn, _numLegos, _legoRegistry)

    # tokenIn -> weth -> usdc
    elif _tokenOut == usdc:
        lastRoute = self._getSwapAmountInWithBridgePool(weth, usdc, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getBestSwapAmountIn(_tokenIn, weth, lastRoute.amountIn, _numLegos, _legoRegistry)

    # weth -> usdc -> tokenOut
    elif _tokenIn == weth:
        lastRoute = self._getBestSwapAmountIn(usdc, _tokenOut, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getSwapAmountInWithBridgePool(weth, usdc, lastRoute.amountIn, _numLegos, _legoRegistry)

    # tokenIn -> usdc -> weth
    elif _tokenOut == weth:
        lastRoute = self._getSwapAmountInWithBridgePool(usdc, weth, _amountOut, _numLegos, _legoRegistry)
        firstRoute = self._getBestSwapAmountIn(_tokenIn, usdc, lastRoute.amountIn, _numLegos, _legoRegistry)

    # let's try thru both paths
    else:
        # tokenIn -> usdc -> tokenOut
        usdcRouteB: SwapRoute = self._getBestSwapAmountIn(usdc, _tokenOut, _amountOut, _numLegos, _legoRegistry)
        usdcRouteA: SwapRoute = self._getBestSwapAmountIn(_tokenIn, usdc, usdcRouteB.amountIn, _numLegos, _legoRegistry)

        # tokenIn -> weth -> tokenOut
        wethRouteB: SwapRoute = self._getBestSwapAmountIn(weth, _tokenOut, _amountOut, _numLegos, _legoRegistry)
        wethRouteA: SwapRoute = self._getBestSwapAmountIn(_tokenIn, weth, wethRouteB.amountIn, _numLegos, _legoRegistry)

        # compare routes
        firstRoute = usdcRouteA
        lastRoute = usdcRouteB
        if wethRouteA.amountIn < usdcRouteA.amountIn:
            firstRoute = wethRouteA
            lastRoute = wethRouteB

    return firstRoute.amountIn, [firstRoute, lastRoute]


@internal
def _getBestSwapAmountIn(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    swapRoute: SwapRoute = SwapRoute(
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
        if pool != empty(address) and amountIn != 0 and amountIn < swapRoute.amountIn:
            swapRoute.pool = pool
            swapRoute.amountIn = amountIn
            swapRoute.legoId = i

    return swapRoute


@internal
def _getSwapAmountInWithBridgePool(
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
    _numLegos: uint256,
    _legoRegistry: address,
) -> SwapRoute:

    swapRoute: SwapRoute = SwapRoute(
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

        # get bridge router pool
        pool: address = staticcall LegoDex(legoInfo.addr).getWethUsdcRouterPool()
        if pool == empty(address):
            continue
        
        amountIn: uint256 = max_value(uint256)
        if i in [UNISWAP_V3_ID, AERODROME_SLIPSTREAM_ID]:
            amountIn = extcall LegoDexNonStandard(legoInfo.addr).getSwapAmountIn(pool, _tokenIn, _tokenOut, _amountOut)
        else:
            amountIn = staticcall LegoDex(legoInfo.addr).getSwapAmountIn(pool, _tokenIn, _tokenOut, _amountOut)
        
        # compare best
        if amountIn != 0 and amountIn < swapRoute.amountIn:
            swapRoute.pool = pool
            swapRoute.amountIn = amountIn
            swapRoute.legoId = i

    return swapRoute


