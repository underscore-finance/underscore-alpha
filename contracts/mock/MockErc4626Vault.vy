# @version 0.4.0

from ethereum.ercs import IERC20

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

asset: public(address)
balanceOf: public(HashMap[address, uint256]) # user -> shares
totalSupply: public(uint256)
allowance: public(HashMap[address, HashMap[address, uint256]])

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
def convertToAssets(_vaultTokenAmount: uint256) -> uint256:
    return _vaultTokenAmount


@external
def totalAssets() -> uint256:
    return staticcall IERC20(self.asset).balanceOf(self)


# erc20 methods


@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(msg.sender, _to, _value)
    return True


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    self.allowance[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True