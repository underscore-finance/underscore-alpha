# @version 0.4.0

from interfaces import LegoYield

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view
    def isValidLegoId(_legoId: uint256) -> bool: view
    def legoInfo(_legoId: uint256) -> LegoInfo: view
    def numLegos() -> uint256: view

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

# lego ids
AAVE_V3_ID: public(immutable(uint256))
COMPOUND_V3_ID: public(immutable(uint256))
EULER_ID: public(immutable(uint256))
FLUID_ID: public(immutable(uint256))
MOONWELL_ID: public(immutable(uint256))
MORPHO_ID: public(immutable(uint256))
SKY_ID: public(immutable(uint256))

@deploy
def __init__(
    _addyRegistry: address,
    _aaveV3Id: uint256,
    _compoundV3Id: uint256,
    _eulerId: uint256,
    _fluidId: uint256,
    _moonwellId: uint256,
    _morphoId: uint256,
    _skyId: uint256,
):
    assert empty(address) != _addyRegistry # dev: invalid address
    ADDY_REGISTRY = _addyRegistry

    # lego ids
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


#######################
# Yield Opportunities #
#######################


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


# utility functions


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