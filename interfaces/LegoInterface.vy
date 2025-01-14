# @version 0.3.10

@external
def depositTokens(_asset: address, _vault: address, _amount: uint256) -> (uint256, uint256):
    return 0, 0

# config

@view
@external
def isValidFundsRecovery(_asset: address, _recipient: address) -> bool:
    return False

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
def governor() -> address:
    return empty(address)

@view
@external 
def isValidGovernor(_newGovernor: address) -> bool:
    return False

@external
def setGovernor(_newGovernor: address) -> bool:
    return False

@view
@external
def isActivated() -> bool:
    return False

@external
def activate(_shouldActivate: bool):
    pass

