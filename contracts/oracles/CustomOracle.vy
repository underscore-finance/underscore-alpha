# @version 0.4.0

implements: OraclePartner
initializes: gov
initializes: oad
exports: gov.__interface__
exports: oad.__interface__

import contracts.modules.Governable as gov
import contracts.modules.OracleAssetData as oad
import interfaces.OraclePartnerInterface as OraclePartner

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct CustomOracleData:
    price: uint256
    publishTime: uint256

event CustomPriceSet:
    asset: indexed(address)
    price: uint256

event CustomPriceDisabled:
    asset: indexed(address)

# custom config
priceData: public(HashMap[address, CustomOracleData])

# general config
oraclePartnerId: public(uint256)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    gov.__init__(_addyRegistry)
    oad.__init__()


#############
# Get Price #
#############


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    priceData: CustomOracleData = self.priceData[_asset]
    if priceData.price == 0:
        return 0
    return self._getPrice(priceData, _staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> (uint256, bool):
    priceData: CustomOracleData = self.priceData[_asset]
    if priceData.price == 0:
        return 0, False
    return self._getPrice(priceData, _staleTime), True


@view
@internal
def _getPrice(_priceData: CustomOracleData, _staleTime: uint256) -> uint256:

    # price is too stale
    if _staleTime != 0 and block.timestamp - _priceData.publishTime > _staleTime:
        return 0

    return _priceData.price


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.priceData[_asset].price != 0


#####################
# Config Price Feed #
#####################


@external
def setPrice(_asset: address, _price: uint256):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.priceData[_asset] = CustomOracleData(
        price=_price,
        publishTime=block.timestamp,
    )
    oad._addAsset(_asset)
    log CustomPriceSet(_asset, _price)


# disable price feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms
    if self.priceData[_asset].price == 0:
        return False
    self.priceData[_asset] = empty(CustomOracleData)
    oad._removeAsset(_asset)
    log CustomPriceDisabled(_asset)
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