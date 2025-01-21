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


@view
@external
def susds() -> address:
    return self


@view
@external
def usdc() -> address:
    return self.asset


@view
@external
def usds() -> address:
    return self.asset


@external
def deposit(_asset: address, _receiver: address, _amount: uint256) -> uint256:
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_receiver] += _amount
    self.totalSupply += _amount
    return _amount


@external
def withdraw(_asset: address, _receiver: address, _maxAssetsToWithdraw: uint256) -> uint256:
    shares: uint256 = min(_maxAssetsToWithdraw, self.balanceOf[msg.sender])
    amount: uint256 = min(shares, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).transfer(_receiver, amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[msg.sender] -= shares
    self.totalSupply -= shares
    return amount


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