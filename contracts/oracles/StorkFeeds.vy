# @version 0.4.0

implements: OraclePartner
initializes: gov
initializes: oad
exports: gov.__interface__
exports: oad.__interface__

import contracts.modules.Governable as gov
import contracts.modules.OracleAssetData as oad
import interfaces.OraclePartnerInterface as OraclePartner

interface StorkNetwork:
    def getTemporalNumericValueUnsafeV1(_priceFeedId: bytes32) -> TemporalNumericValue: view
    def updateTemporalNumericValuesV1(_payLoad: Bytes[2048]): payable
    def getUpdateFeeV1(_payLoad: Bytes[2048]) -> uint256: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct TemporalNumericValue:
    timestampNs: uint64
    quantizedValue: uint256

event StorkFeedAdded:
    asset: indexed(address)
    feedId: indexed(bytes32)

event StorkFeedDisabled:
    asset: indexed(address)

event StorkPriceUpdated:
    payload: Bytes[2048]
    feeAmount: uint256
    caller: indexed(address)

event EthRecoveredFromStork:
    recipient: indexed(address)
    amount: uint256

# stork config
STORK: public(immutable(address))
feedConfig: public(HashMap[address, bytes32])

# general config
oraclePartnerId: public(uint256)
ADDY_REGISTRY: public(immutable(address))

NORMALIZED_DECIMALS: constant(uint256) = 18
MAX_PRICE_UPDATES: constant(uint256) = 15


@deploy
def __init__(_addyRegistry: address, _stork: address):
    assert empty(address) not in [_addyRegistry, _stork] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry
    STORK = _stork
    gov.__init__(_addyRegistry)
    oad.__init__()


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
    return self._getPrice(feedId, _staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> (uint256, bool):
    feedId: bytes32 = self.feedConfig[_asset]
    if feedId == empty(bytes32):
        return 0, False
    return self._getPrice(feedId, _staleTime), True


@view
@internal
def _getPrice(_feedId: bytes32, _staleTime: uint256) -> uint256:
    priceData: TemporalNumericValue = staticcall StorkNetwork(STORK).getTemporalNumericValueUnsafeV1(_feedId)

    # NOTE: choosing to fail gracefully in Underscore

    # no price
    if priceData.quantizedValue == 0:
        return 0

    # price is too stale
    publishTime: uint256 = convert(priceData.timestampNs, uint256) // 1_000_000_000
    if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
        return 0

    return priceData.quantizedValue


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
def updateStorkPrices(_payloads: DynArray[Bytes[2048], MAX_PRICE_UPDATES]):
    for i: uint256 in range(len(_payloads), bound=MAX_PRICE_UPDATES):
        p: Bytes[2048] = _payloads[i]
        feeAmount: uint256 = staticcall StorkNetwork(STORK).getUpdateFeeV1(p)
        assert self.balance >= feeAmount # dev: insufficient balance
        extcall StorkNetwork(STORK).updateTemporalNumericValuesV1(p, value=feeAmount)
        log StorkPriceUpdated(p, feeAmount, msg.sender)


#####################
# Config Price Feed #
#####################


# set price feed


@view
@external
def isValidStorkFeed(_asset: address, _feedId: bytes32) -> bool:
    return self._isValidStorkFeed(_asset, _feedId)


@view
@internal
def _isValidStorkFeed(_asset: address, _feedId: bytes32) -> bool:
    if _asset == empty(address):
        return False
    priceData: TemporalNumericValue = staticcall StorkNetwork(STORK).getTemporalNumericValueUnsafeV1(_feedId)
    return priceData.timestampNs != 0


@external
def setStorkFeed(_asset: address, _feedId: bytes32) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms
    if not self._isValidStorkFeed(_asset, _feedId):
        return False
    self.feedConfig[_asset] = _feedId
    oad._addAsset(_asset)
    log StorkFeedAdded(_asset, _feedId)
    return True


# disable price feed


@external
def disableStorkPriceFeed(_asset: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms
    if not self._hasPriceFeed(_asset):
        return False
    self.feedConfig[_asset] = empty(bytes32)
    oad._removeAsset(_asset)
    log StorkFeedDisabled(_asset)
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
    assert gov._isGovernor(msg.sender) # dev: no perms
    balance: uint256 = self.balance
    if not self._isValidEthRecovery(_recipient, balance):
        return False
    send(_recipient, balance)
    log EthRecoveredFromStork(_recipient, balance)
    return True


##########
# Config #
##########


@external
def setOraclePartnerId(_oracleId: uint256) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4) # dev: no perms
    prevId: uint256 = self.oraclePartnerId
    assert prevId == 0 or prevId == _oracleId # dev: invalid oracle id
    self.oraclePartnerId = _oracleId
    return True
