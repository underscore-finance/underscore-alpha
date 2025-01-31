# @version 0.4.0

implements: OraclePartner
import interfaces.OraclePartnerInterface as OraclePartner

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governor() -> address: view

struct CustomOracleData:
    price: uint256
    publishTime: uint256

event CustomPriceSet:
    asset: indexed(address)
    price: uint256

# config
priceData: public(HashMap[address, CustomOracleData])
oraclePartnerId: public(uint256)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry


#############
# Get Price #
#############


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    priceData: CustomOracleData = self.priceData[_asset]

    # price is too stale
    if _staleTime != 0 and block.timestamp - priceData.publishTime > _staleTime:
        return 0

    return priceData.price


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.priceData[_asset].price != 0


#####################
# Config Price Feed #
#####################


@external
def setPrice(_asset: address, _price: uint256):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.priceData[_asset] = CustomOracleData(
        price=_price,
        publishTime=block.timestamp,
    )
    log CustomPriceSet(_asset, _price)


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