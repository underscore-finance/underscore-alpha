# @version 0.4.0

cToken: public(address)

MAX_MARKETS: constant(uint256) = 50

@deploy
def __init__(_cToken: address):
    self.cToken = _cToken

@view
@external
def getAllMarkets() -> DynArray[address, MAX_MARKETS]:
    return [self.cToken]