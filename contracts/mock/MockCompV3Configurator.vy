# @version 0.4.0

@deploy
def __init__():
    pass

@view
@external
def factory(_asset: address) -> address:
    return _asset