# @version 0.4.0

@deploy
def __init__():
    pass

@view
@external
def isValidDeployment(_vault: address) -> bool:
    return True

@view
@external
def isProxy(_vault: address) -> bool:
    return True
