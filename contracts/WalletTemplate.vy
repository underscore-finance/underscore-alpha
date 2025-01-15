# @version 0.4.0

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view

event AgenticDeposit:
    user: indexed(address)
    asset: indexed(address)
    vault: indexed(address)
    assetAmountDeposited: uint256
    vaultToken: address
    vaultTokenAmountReceived: uint256
    legoId: uint256
    legoAddr: address
    isAgent: bool

event AgenticWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    vault: address
    legoId: uint256
    legoAddr: address
    isAgent: bool

event WhitelistAddrSet:
    addr: indexed(address)
    isAllowed: bool

# admin
owner: public(address)
agent: public(address)

# transfer whitelist
isRecipientAllowed: public(HashMap[address, bool])

# config
legoRegistry: public(address)
initialized: public(bool)

API_VERSION: constant(String[28]) = "0.0.1"


@deploy
def __init__():
    # make sure original reference contract can't be initialized
    self.initialized = True


@external
def initialize(_legoRegistry: address, _owner: address, _agent: address) -> bool:
    assert not self.initialized # dev: can only initialize once
    self.initialized = True

    assert empty(address) not in [_legoRegistry, _owner, _agent] # dev: invalid addrs
    self.legoRegistry = _legoRegistry
    self.owner = _owner
    self.agent = _agent

    return True


@pure
@external
def apiVersion() -> String[28]:
    return API_VERSION


###########
# Deposit #
###########


@nonreentrant
@external
def depositTokens(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _vault: address = empty(address),
) -> (uint256, address, uint256):
    isAgent: bool = msg.sender == self.agent
    assert isAgent or msg.sender == self.owner # dev: no perms
    return self._depositTokens(_legoId, _asset, _amount, _vault, isAgent)


@nonreentrant
@external
def depositTokensWithTransfer(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _vault: address = empty(address),
    _shouldSweep: bool = True,
) -> (uint256, address, uint256):
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, amount, default_return_value=True) # dev: transfer failed

    # can only sweep if have perms
    isAgent: bool = msg.sender == self.agent
    if _shouldSweep and (isAgent or msg.sender == self.owner):
        amount = max_value(uint256)

    return self._depositTokens(_legoId, _asset, amount, _vault, isAgent)


@internal
def _depositTokens(
    _legoId: uint256,
    _asset: address,
    _amount: uint256,
    _vault: address,
    _isAgent: bool,
) -> (uint256, address, uint256):
    legoAddr: address = staticcall LegoRegistry(self.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize amount
    wantedAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert wantedAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).approve(legoAddr, wantedAmount, default_return_value=True) # dev: approval failed

    # deposit into lego partner
    assetAmountDeposited: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = extcall LegoPartner(legoAddr).depositTokens(_asset, wantedAmount, _vault)
    assert extcall IERC20(_asset).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticDeposit(msg.sender, _asset, _vault, assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _legoId, legoAddr, _isAgent)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived


############
# Withdraw #
############


@nonreentrant
@external
def withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _amount: uint256 = max_value(uint256),
    _vault: address = empty(address),
) -> (uint256, uint256):
    isAgent: bool = msg.sender == self.agent
    assert isAgent or msg.sender == self.owner # dev: no perms
    return self._withdrawTokens(_legoId, _asset, _vaultToken, _amount, _vault, isAgent)


@internal
def _withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _amount: uint256,
    _vault: address,
    _isAgent: bool,
) -> (uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(self.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize vault token amount
    wantedVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(self))
    assert wantedVaultTokenAmount != 0 # dev: nothing to transfer

    # some vault tokens require max value approval (comp v3)
    assert extcall IERC20(_vaultToken).approve(legoAddr, max_value(uint256), default_return_value=True) # dev: approval failed

    # withdraw from lego partner
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned = extcall LegoPartner(legoAddr).withdrawTokens(_asset, _vaultToken, wantedVaultTokenAmount, _vault)
    assert extcall IERC20(_vaultToken).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticWithdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, vaultTokenAmountBurned, _vault, _legoId, legoAddr, _isAgent)
    return assetAmountReceived, vaultTokenAmountBurned


##################
# Transfer Funds #
##################


@external
def transferFunds(_recipient: address, _amount: uint256 = max_value(uint256), _asset: address = empty(address)) -> bool:
    isAgent: bool = msg.sender == self.agent
    assert isAgent or msg.sender == self.owner # dev: no perms

    # validate recipient
    if _recipient != self.owner:
        assert self.isRecipientAllowed[_recipient] # dev: recipient not allowed

    # finalize amount
    amount: uint256 = 0
    if _asset == empty(address):
        amount = min(_amount, self.balance)
    else:
        amount = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert amount != 0 # dev: nothing to transfer

    # transfer funds
    if _asset == empty(address):
        send(_recipient, amount)
    else:
        assert extcall IERC20(_asset).transfer(_recipient, amount, default_return_value=True) # dev: transfer failed

    return True


# whitelist


@view
@external 
def isValidWhitelistAddr(_addr: address, _isAllowed: bool) -> bool:
    return self._isValidWhitelistAddr(_addr, _isAllowed, self.owner)


@view
@internal 
def _isValidWhitelistAddr(_addr: address, _isAllowed: bool, _owner: address) -> bool:
    # owner is always allowed to receive funds
    # no checks here to disallow self.agent
    if _addr == empty(address) or _addr == _owner:
        return False
    return _isAllowed != self.isRecipientAllowed[_addr]


@external
def setWhitelistAddr(_addr: address, _isAllowed: bool) -> bool:
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms
    if not self._isValidWhitelistAddr(_addr, _isAllowed, owner):
        return False
    self.isRecipientAllowed[_addr] = _isAllowed
    log WhitelistAddrSet(_addr, _isAllowed)
    return True