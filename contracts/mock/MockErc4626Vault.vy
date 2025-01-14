# @version 0.4.0

from ethereum.ercs import IERC20

asset: public(address)
balanceOf: public(HashMap[address, uint256]) # user -> shares
totalSupply: public(uint256)

# NOTE: this does not include ALL required erc20/4626 methods. 
# This only includes what we use/need for our strats


@deploy
def __init__(_asset: address):
    self.asset = _asset


@external
def deposit(_amount: uint256, _receiver: address) -> uint256:
    assert extcall IERC20(self.asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_receiver] += _amount
    self.totalSupply += _amount
    return _amount


@external
def redeem(_shares: uint256, _receiver: address, _owner: address) -> uint256:
    shares: uint256 = min(_shares, self.balanceOf[_owner])
    amount: uint256 = min(shares, staticcall IERC20(self.asset).balanceOf(self))
    assert extcall IERC20(self.asset).transfer(_receiver, amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_owner] -= shares
    self.totalSupply -= shares
    return amount


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