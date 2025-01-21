# @version 0.4.0

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view
    def isValidLegoId(_legoId: uint256) -> bool: view

LEGO_REGISTRY: public(immutable(address))

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
    _legoRegistry: address,
    _aaveV3Id: uint256,
    _compoundV3Id: uint256,
    _eulerId: uint256,
    _fluidId: uint256,
    _moonwellId: uint256,
    _morphoId: uint256,
    _skyId: uint256,
):
    LEGO_REGISTRY = _legoRegistry

    # lego ids
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_aaveV3Id) # dev: invalid id
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_compoundV3Id) # dev: invalid id
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_eulerId) # dev: invalid id
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_fluidId) # dev: invalid id
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_moonwellId) # dev: invalid id
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_morphoId) # dev: invalid id
    assert staticcall LegoRegistry(_legoRegistry).isValidLegoId(_skyId) # dev: invalid id

    AAVE_V3_ID = _aaveV3Id
    COMPOUND_V3_ID = _compoundV3Id
    EULER_ID = _eulerId
    FLUID_ID = _fluidId
    MOONWELL_ID = _moonwellId
    MORPHO_ID = _morphoId
    SKY_ID = _skyId

@view
@external
def aaveV3() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(AAVE_V3_ID)


@view
@external
def aaveV3Id() -> uint256:
    return AAVE_V3_ID


@view
@external
def compoundV3() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(COMPOUND_V3_ID)


@view
@external
def compoundV3Id() -> uint256:
    return COMPOUND_V3_ID


@view
@external
def euler() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(EULER_ID)


@view
@external
def eulerId() -> uint256:
    return EULER_ID


@view
@external
def fluid() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(FLUID_ID)


@view
@external
def fluidId() -> uint256:
    return FLUID_ID


@view
@external
def moonwell() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(MOONWELL_ID)


@view
@external
def moonwellId() -> uint256:
    return MOONWELL_ID


@view
@external
def morpho() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(MORPHO_ID)


@view
@external
def morphoId() -> uint256:
    return MORPHO_ID


@view
@external
def sky() -> address:
    return staticcall LegoRegistry(LEGO_REGISTRY).getLegoAddr(SKY_ID)


@view
@external
def skyId() -> uint256:
    return SKY_ID
