# @version 0.3.10

@external
def depositTokens(_asset: address, _vault: address, _amount: uint256) -> (uint256, address, uint256):
    return 0, empty(address), 0

# config

@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    return False

@view
@external
def legoId() -> uint256:
    return 0

@external
def setLegoId(_legoId: uint256) -> bool:
    return False

@view
@external
def isActivated() -> bool:
    return False

@external
def activate(_shouldActivate: bool):
    pass

