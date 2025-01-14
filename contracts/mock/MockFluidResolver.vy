# @version 0.4.0

fToken: public(address)

MAX_FTOKENS: constant(uint256) = 25

@deploy
def __init__(_fToken: address):
    self.fToken = _fToken

@view
@external
def getAllFTokens() -> DynArray[address, MAX_FTOKENS]:
    return [self.fToken]