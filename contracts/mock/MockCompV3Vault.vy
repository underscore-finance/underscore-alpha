# @version 0.4.0

from ethereum.ercs import IERC20

baseToken: public(address)
balanceOf: public(HashMap[address, uint256]) # user -> shares
totalSupply: public(uint256)

# NOTE: this does not include ALL required erc20/4626 methods. 
# This only includes what we use/need for our strats


@deploy
def __init__(_asset: address):
    self.baseToken = _asset


@external
def supplyTo(_recipient: address, _asset: address, _amount: uint256):
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_recipient] += _amount
    self.totalSupply += _amount


@external
def withdrawTo(_recipient: address, _asset: address, _amount: uint256):
    shares: uint256 = min(_amount, self.balanceOf[msg.sender])
    amount: uint256 = min(shares, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).transfer(_recipient, amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[msg.sender] -= shares
    self.totalSupply -= shares


@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    return True