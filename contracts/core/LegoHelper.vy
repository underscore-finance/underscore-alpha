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
    assert empty(address) != _addyRegistry # dev: invalid address
    ADDY_REGISTRY = _addyRegistry
    legoRegistry: address = staticcall AddyRegistry(_addyRegistry).getAddy(2)

    # yield lego ids
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


# can't make this view function because of uni v3 + aerodrom slipstream
@external
def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> (address, uint256, uint256):
    bestPool: address = empty(address)
    bestAmountOut: uint256 = 0
    bestLegoId: uint256 = 0

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
        if pool != empty(address) and amountOut > bestAmountOut:
            bestPool = pool
            bestAmountOut = amountOut
            bestLegoId = i

    return bestPool, bestAmountOut, bestLegoId


# can't make this view function because of uni v3 + aerodrom slipstream
@external
def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (address, uint256, uint256):
    bestPool: address = empty(address)
    bestAmountIn: uint256 = max_value(uint256)
    bestLegoId: uint256 = 0

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
        if pool != empty(address) and amountIn != 0 and amountIn < bestAmountIn:
            bestPool = pool
            bestAmountIn = amountIn
            bestLegoId = i

    return bestPool, bestAmountIn, bestLegoId
