# @version 0.4.0

implements: OraclePartner
import interfaces.OraclePartnerInterface as OraclePartner

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governor() -> address: view

event CustomPriceSet:
    asset: indexed(address)
    price: uint256

# config
price: public(HashMap[address, uint256])
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
    return self.price[_asset]


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.price[_asset] != 0


#####################
# Config Price Feed #
#####################


@external
def setPrice(_asset: address, _price: uint256):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.price[_asset] = _price
    log CustomPriceSet(_asset, _price)


##########
# Config #
##########


@external
def setOraclePartnerId(_oracleId: uint256):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4) # dev: no perms
    prevId: uint256 = self.oraclePartnerId
    assert prevId == 0 or prevId == _oracleId # dev: invalid oracle id
    self.oraclePartnerId = _oracleId