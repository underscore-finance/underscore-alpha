# @version 0.4.0

implements: OraclePartner
import interfaces.OraclePartnerInterface as OraclePartner

interface PythNetwork:
    def getPriceUnsafe(_priceFeedId: bytes32) -> PythPrice: view
    def priceFeedExists(_priceFeedId: bytes32) -> bool: view
    def getUpdateFee(_payLoad: Bytes[2048]) -> uint256: view
    def updatePriceFeeds(_payLoad: Bytes[2048]): payable

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governor() -> address: view

struct PythPrice:
    price: int64
    confidence: uint64
    exponent: int32
    publishTime: uint64

event PythFeedAdded:
    asset: indexed(address)
    feedId: indexed(bytes32)

event PythFeedDisabled:
    asset: indexed(address)

event PythPriceUpdated:
    payload: Bytes[2048]
    feeAmount: uint256
    caller: indexed(address)

event EthRecoveredFromPyth:
    recipient: indexed(address)
    amount: uint256

# config
feedConfig: public(HashMap[address, bytes32])
oraclePartnerId: public(uint256)
ADDY_REGISTRY: public(immutable(address))

# Base L2
PYTH: constant(address) = 0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a

NORMALIZED_DECIMALS: constant(uint256) = 18
MAX_PRICE_UPDATES: constant(uint256) = 15


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry


@payable
@external
def __default__():
    pass


#############
# Get Price #
#############


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    feedId: bytes32 = self.feedConfig[_asset]
    if feedId == empty(bytes32):
        return 0

    # NOTE: choosing to fail gracefully in Underscore

    priceData: PythPrice = staticcall PythNetwork(PYTH).getPriceUnsafe(feedId)

    # no price
    if priceData.price <= 0:
        return 0

    # price is too stale
    publishTime: uint256 = convert(priceData.publishTime, uint256)
    if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
        return 0

    price: uint256 = convert(priceData.price, uint256)
    confidence: uint256 = convert(priceData.confidence, uint256)

    # negative exponent: multiply by 10^(18-|exponent|)
    if priceData.exponent < 0:
        price = price * (10 ** NORMALIZED_DECIMALS) // (10 ** convert(-priceData.exponent, uint256))
        confidence = confidence * (10 ** NORMALIZED_DECIMALS) // (10 ** convert(-priceData.exponent, uint256))

    # positive exponent: multiply by 10^(18+exponent)
    else:
        price = price * (10 ** (NORMALIZED_DECIMALS + convert(priceData.exponent, uint256)))
        confidence = confidence * (10 ** (NORMALIZED_DECIMALS + convert(priceData.exponent, uint256)))

    # invalid price
    if confidence >= price:
        return 0

    return price - confidence


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self._hasPriceFeed(_asset)


@view
@internal
def _hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset] != empty(bytes32)


################
# Update Price #
################


@external
def updatePythPrices(_payloads: DynArray[Bytes[2048], MAX_PRICE_UPDATES]):
    for i: uint256 in range(len(_payloads), bound=MAX_PRICE_UPDATES):
        p: Bytes[2048] = _payloads[i]
        feeAmount: uint256 = staticcall PythNetwork(PYTH).getUpdateFee(p)
        extcall PythNetwork(PYTH).updatePriceFeeds(p, value=feeAmount)
        log PythPriceUpdated(p, feeAmount, msg.sender)


#####################
# Config Price Feed #
#####################


# set price feed


@view
@external
def isValidPythFeed(_asset: address, _feedId: bytes32) -> bool:
    return self._isValidPythFeed(_asset, _feedId)


@view
@internal
def _isValidPythFeed(_asset: address, _feedId: bytes32) -> bool:
    if _asset == empty(address):
        return False
    return staticcall PythNetwork(PYTH).priceFeedExists(_feedId)


@external
def setPythFeed(_asset: address, _feedId: bytes32) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    if not self._isValidPythFeed(_asset, _feedId):
        return False

    self.feedConfig[_asset] = _feedId
    log PythFeedAdded(_asset, _feedId)
    return True


# disable price feed


@external
def disablePythPriceFeed(_asset: address) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    if not self._hasPriceFeed(_asset):
        return False
    self.feedConfig[_asset] = empty(bytes32)
    log PythFeedDisabled(_asset)
    return True


#################
# Recover Funds #
#################


@view
@external
def isValidEthRecovery(_recipient: address) -> bool:
    return self._isValidEthRecovery(_recipient, self.balance)


@view
@internal
def _isValidEthRecovery(_recipient: address, _balance: uint256) -> bool:
    return _recipient != empty(address) and _balance != 0


@external
def recoverEthBalance(_recipient: address) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    balance: uint256 = self.balance
    if not self._isValidEthRecovery(_recipient, balance):
        return False
    send(_recipient, balance)
    log EthRecoveredFromPyth(_recipient, balance)
    return True


##########
# Config #
##########


@external
def setOraclePartnerId(_oracleId: uint256):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4) # dev: no perms
    prevId: uint256 = self.oraclePartnerId
    assert prevId == 0 or prevId == _oracleId # dev: invalid oracle id
    self.oraclePartnerId = _oracleId
