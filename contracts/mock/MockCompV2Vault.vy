# @version 0.4.0

from ethereum.ercs import IERC20

underlying: public(address)
balanceOf: public(HashMap[address, uint256]) # user -> shares
totalSupply: public(uint256)

# NOTE: this does not include ALL required erc20/4626 methods. 
# This only includes what we use/need for our strats


@deploy
def __init__(_asset: address):
    self.underlying = _asset


@external
def mint(_amount: uint256) -> uint256:
    assert extcall IERC20(self.underlying).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[msg.sender] += _amount
    self.totalSupply += _amount
    return 0


@external
def redeem(_ctokenAmount: uint256) -> uint256:
    shares: uint256 = min(_ctokenAmount, self.balanceOf[msg.sender])
    amount: uint256 = min(shares, staticcall IERC20(self.underlying).balanceOf(self))
    assert extcall IERC20(self.underlying).transfer(msg.sender, amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[msg.sender] -= shares
    self.totalSupply -= shares
    return 0


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