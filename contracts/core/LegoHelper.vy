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
    def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (address, uint256): nonpayable

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


###############
# Dex Helpers #
###############


# amount out


@external
def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> DynArray[SwapRoute, 2]:
    directSwapRoute: SwapRoute = self._getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn)

    # check bridge routes
    bestBridgeAmountOut: uint256 = 0
    bestBridgeSwapRoutes: DynArray[SwapRoute, 2] = []
    bestBridgeAmountOut, bestBridgeSwapRoutes = self._getBestSwapAmountOutWithBridges(_tokenIn, _tokenOut, _amountIn)

    # nothing to do
    if directSwapRoute.pool == empty(address) and bestBridgeAmountOut == 0:
        return []

    # compare with raw amount out
    if directSwapRoute.amountOut > bestBridgeAmountOut:
        return [directSwapRoute]
    return bestBridgeSwapRoutes


@internal
def _getBestSwapAmountOutWithBridges(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> (uint256, DynArray[SwapRoute, 2]):
    usdc: address = USDC
    weth: address = WETH

    shouldCheckWethBridge: bool = (_tokenIn != weth and _tokenOut == usdc) or (_tokenIn == usdc and _tokenOut != weth)
    shouldCheckUsdcBridge: bool = (_tokenIn != usdc and _tokenOut == weth) or (_tokenIn == weth and _tokenOut != usdc)
    if _tokenIn not in [usdc, weth] and _tokenOut not in [usdc, weth]:
        shouldCheckWethBridge = True
        shouldCheckUsdcBridge = True

    # nothing to do
    if not shouldCheckWethBridge and not shouldCheckUsdcBridge:
        return 0, []

    # weth bridge routes
    wethBridgeAmountOut: uint256 = 0
    wethBridgeSwapRoutes: DynArray[SwapRoute, 2] = []
    if shouldCheckWethBridge:
        wethBridgeAmountOut, wethBridgeSwapRoutes = self._getBestSwapAmountOutSingleBridge(weth, _tokenIn, _tokenOut, _amountIn)

    # usdc bridge routes
    usdcBridgeAmountOut: uint256 = 0
    usdcBridgeSwapRoutes: DynArray[SwapRoute, 2] = []
    if shouldCheckUsdcBridge:
        usdcBridgeAmountOut, usdcBridgeSwapRoutes = self._getBestSwapAmountOutSingleBridge(usdc, _tokenIn, _tokenOut, _amountIn)

    # compare bridge routes
    bestBridgeAmountOut: uint256 = wethBridgeAmountOut
    bestBridgeSwapRoutes: DynArray[SwapRoute, 2] = wethBridgeSwapRoutes
    if usdcBridgeAmountOut > wethBridgeAmountOut:
        bestBridgeAmountOut = usdcBridgeAmountOut
        bestBridgeSwapRoutes = usdcBridgeSwapRoutes

    return bestBridgeAmountOut, bestBridgeSwapRoutes


@internal
def _getBestSwapAmountOutSingleBridge(_bridgeAsset: address, _tokenIn: address, _tokenOut: address, _amountIn: uint256) -> (uint256, DynArray[SwapRoute, 2]):
    firstSwapRoute: SwapRoute = self._getBestSwapAmountOut(_tokenIn, _bridgeAsset, _amountIn)
    if firstSwapRoute.pool == empty(address):
        return 0, []
    secondSwapRoute: SwapRoute = self._getBestSwapAmountOut(_bridgeAsset, _tokenOut, firstSwapRoute.amountOut)
    if secondSwapRoute.pool == empty(address):
        return 0, []
    return secondSwapRoute.amountOut, [firstSwapRoute, secondSwapRoute]


# can't make this view function because of uni v3 + aerodrom slipstream
@internal
def _getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> SwapRoute:
    swapRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=_amountIn,
        amountOut=0,
    )

    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.DEX:
            continue

        pool: address = empty(address)
        amountOut: uint256 = 0

        # non-view function
        if i == UNISWAP_V3_ID or i == AERODROME_SLIPSTREAM_ID:
            pool, amountOut = extcall LegoDexNonStandard(legoInfo.addr).getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn)

        # normal
        else:
            pool, amountOut = staticcall LegoDex(legoInfo.addr).getBestSwapAmountOut(_tokenIn, _tokenOut, _amountIn)
        
        # compare best
        if pool != empty(address) and amountOut > swapRoute.amountOut:
            swapRoute.pool = pool
            swapRoute.amountOut = amountOut
            swapRoute.legoId = i

    return swapRoute


# amount in


@external
def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> DynArray[SwapRoute, 2]:
    directSwapRoute: SwapRoute = self._getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut)

    # check bridge routes
    bestBridgeAmountIn: uint256 = 0
    bestBridgeSwapRoutes: DynArray[SwapRoute, 2] = []
    bestBridgeAmountIn, bestBridgeSwapRoutes = self._getBestSwapAmountInWithBridges(_tokenIn, _tokenOut, _amountOut)

    # compare with raw amount in
    if directSwapRoute.amountIn < bestBridgeAmountIn:
        return [directSwapRoute]
    elif bestBridgeAmountIn != max_value(uint256):
        return bestBridgeSwapRoutes
    return []


@internal
def _getBestSwapAmountInWithBridges(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (uint256, DynArray[SwapRoute, 2]):
    usdc: address = USDC
    weth: address = WETH

    shouldCheckWethBridge: bool = (_tokenIn != weth and _tokenOut == usdc) or (_tokenIn == usdc and _tokenOut != weth)
    shouldCheckUsdcBridge: bool = (_tokenIn != usdc and _tokenOut == weth) or (_tokenIn == weth and _tokenOut != usdc)
    if _tokenIn not in [usdc, weth] and _tokenOut not in [usdc, weth]:
        shouldCheckWethBridge = True
        shouldCheckUsdcBridge = True

    # nothing to do
    if not shouldCheckWethBridge and not shouldCheckUsdcBridge:
        return max_value(uint256), []

    # weth bridge routes
    wethBridgeAmountIn: uint256 = max_value(uint256)
    wethBridgeSwapRoutes: DynArray[SwapRoute, 2] = []
    if shouldCheckWethBridge:
        wethBridgeAmountIn, wethBridgeSwapRoutes = self._getBestSwapAmountInSingleBridge(weth, _tokenIn, _tokenOut, _amountOut)

    # usdc bridge routes
    usdcBridgeAmountIn: uint256 = max_value(uint256)
    usdcBridgeSwapRoutes: DynArray[SwapRoute, 2] = []
    if shouldCheckUsdcBridge:
        usdcBridgeAmountIn, usdcBridgeSwapRoutes = self._getBestSwapAmountInSingleBridge(usdc, _tokenIn, _tokenOut, _amountOut)

    # compare bridge routes
    bestBridgeAmountIn: uint256 = wethBridgeAmountIn
    bestBridgeSwapRoutes: DynArray[SwapRoute, 2] = wethBridgeSwapRoutes
    if usdcBridgeAmountIn < wethBridgeAmountIn:
        bestBridgeAmountIn = usdcBridgeAmountIn
        bestBridgeSwapRoutes = usdcBridgeSwapRoutes

    return bestBridgeAmountIn, bestBridgeSwapRoutes


@internal
def _getBestSwapAmountInSingleBridge(_bridgeAsset: address, _tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (uint256, DynArray[SwapRoute, 2]):
    firstSwapRoute: SwapRoute = self._getBestSwapAmountIn(_tokenIn, _bridgeAsset, _amountOut)
    if firstSwapRoute.pool == empty(address):
        return max_value(uint256), []
    secondSwapRoute: SwapRoute = self._getBestSwapAmountIn(_bridgeAsset, _tokenOut, firstSwapRoute.amountIn)
    if secondSwapRoute.pool == empty(address):
        return max_value(uint256), []
    return secondSwapRoute.amountIn, [firstSwapRoute, secondSwapRoute]


# can't make this view function because of uni v3 + aerodrom slipstream
@internal
def _getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> SwapRoute:
    swapRoute: SwapRoute = SwapRoute(
        legoId=0,
        pool=empty(address),
        tokenIn=_tokenIn,
        tokenOut=_tokenOut,
        amountIn=max_value(uint256),
        amountOut=_amountOut,
    )

    legoRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2)
    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = staticcall LegoRegistry(legoRegistry).legoInfo(i)
        if legoInfo.legoType != LegoType.DEX:
            continue

        pool: address = empty(address)
        amountIn: uint256 = max_value(uint256)

        # non-view function
        if i == UNISWAP_V3_ID or i == AERODROME_SLIPSTREAM_ID:
            pool, amountIn = extcall LegoDexNonStandard(legoInfo.addr).getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut)

        # normal
        else:
            pool, amountIn = staticcall LegoDex(legoInfo.addr).getBestSwapAmountIn(_tokenIn, _tokenOut, _amountOut)
        
        # compare best
        if pool != empty(address) and amountIn != 0 and amountIn < swapRoute.amountIn:
            swapRoute.pool = pool
            swapRoute.amountIn = amountIn
            swapRoute.legoId = i

    return swapRoute
