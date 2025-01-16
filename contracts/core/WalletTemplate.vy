# @version 0.4.0

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view
    def isValidLegoId(_legoId: uint256) -> bool: view

struct AgentInfo:
    isActive: bool
    allowedAssets: DynArray[address, MAX_ASSETS]
    allowedLegoIds: DynArray[uint256, MAX_LEGOS]

event AgenticDeposit:
    user: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    refundAssetAmount: uint256
    legoId: uint256
    legoAddr: address
    isAgent: bool

event AgenticWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    refundVaultTokenAmount: uint256
    legoId: uint256
    legoAddr: address
    isAgent: bool

event WalletFundsTransferred:
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    isAgent: bool

event WhitelistAddrSet:
    addr: indexed(address)
    isAllowed: bool

event AgentAdded:
    agent: indexed(address)
    allowedAssets: uint256
    allowedLegoIds: uint256

event AgentModified:
    agent: indexed(address)
    allowedAssets: uint256
    allowedLegoIds: uint256

event AgentDisabled:
    agent: indexed(address)
    prevAllowedAssets: uint256
    prevAllowedLegoIds: uint256

event LegoIdAddedToAgent:
    agent: indexed(address)
    legoId: indexed(uint256)

event AssetAddedToAgent:
    agent: indexed(address)
    asset: indexed(address)

# settings
owner: public(address)
agentSettings: public(HashMap[address, AgentInfo])
isRecipientAllowed: public(HashMap[address, bool])

# config
legoRegistry: public(address)
initialized: public(bool)

API_VERSION: constant(String[28]) = "0.0.1"
MAX_ASSETS: constant(uint256) = 25
MAX_LEGOS: constant(uint256) = 10


@deploy
def __init__():
    # make sure original reference contract can't be initialized
    self.initialized = True


@external
def initialize(_legoRegistry: address, _owner: address, _initialAgent: address) -> bool:
    assert not self.initialized # dev: can only initialize once
    self.initialized = True

    assert empty(address) not in [_legoRegistry, _owner, _initialAgent] # dev: invalid addrs
    assert _initialAgent != _owner # dev: agent cannot be owner
    self.legoRegistry = _legoRegistry
    self.owner = _owner
    self.agentSettings[_initialAgent] = AgentInfo(isActive=True, allowedAssets=[], allowedLegoIds=[])

    return True


@pure
@external
def apiVersion() -> String[28]:
    return API_VERSION


################
# Agent Access #
################


@view
@internal
def _validateAgentAccess(_sender: address, _asset: address, _legoId: uint256) -> bool:
    agentPerms: AgentInfo = self.agentSettings[_sender]
    assert agentPerms.isActive # dev: agent not active

    # check allowed assets
    if _asset != empty(address) and len(agentPerms.allowedAssets) != 0:
        assert _asset in agentPerms.allowedAssets # dev: asset not allowed

    # check allowed lego ids
    if _legoId != 0 and len(agentPerms.allowedLegoIds) != 0:
        assert _legoId in agentPerms.allowedLegoIds # dev: lego id not allowed

    return True


@view
@internal
def _isAgentWithValidation(
    _sender: address,
    _owner: address,
    _asset: address = empty(address),
    _legoId: uint256 = 0,
) -> bool:
    isAgent: bool = False
    if _sender != _owner:
        isAgent = self._validateAgentAccess(_sender, _asset, _legoId)
    return isAgent


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
    isAgent: bool = self._isAgentWithValidation(msg.sender, self.owner, _asset, _legoId)
    return self._depositTokens(_legoId, _asset, _amount, _vault, isAgent)


@nonreentrant
@external
def depositTokensWithTransfer(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _vault: address = empty(address),
) -> (uint256, address, uint256):
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, amount, default_return_value=True) # dev: transfer failed
    return self._depositTokens(_legoId, _asset, amount, _vault, self.agentSettings[msg.sender].isActive)


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
    refundAssetAmount: uint256 = 0
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, refundAssetAmount = extcall LegoPartner(legoAddr).depositTokens(_asset, wantedAmount, _vault, self)
    assert extcall IERC20(_asset).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticDeposit(msg.sender, _asset, vaultToken, assetAmountDeposited, vaultTokenAmountReceived, refundAssetAmount, _legoId, legoAddr, _isAgent)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived


############
# Withdraw #
############


@nonreentrant
@external
def withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address = empty(address),
    _amount: uint256 = max_value(uint256),
) -> (uint256, uint256):
    isAgent: bool = self._isAgentWithValidation(msg.sender, self.owner, _asset, _legoId)
    return self._withdrawTokens(_legoId, _asset, _vaultToken, _amount, isAgent)


@internal
def _withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _amount: uint256,
    _isAgent: bool,
) -> (uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(self.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize amount, this will look at vault token balance (not always 1:1 with underlying asset)
    withdrawAmount: uint256 = _amount
    if _vaultToken != empty(address):
        withdrawAmount = min(_amount, staticcall IERC20(_vaultToken).balanceOf(self))

        # some vault tokens require max value approval (comp v3)
        assert extcall IERC20(_vaultToken).approve(legoAddr, max_value(uint256), default_return_value=True) # dev: approval failed

    assert withdrawAmount != 0 # dev: nothing to withdraw

    # withdraw from lego partner
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    refundVaultTokenAmount: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount = extcall LegoPartner(legoAddr).withdrawTokens(_asset, withdrawAmount, _vaultToken, self)

    # zero out approvals
    if _vaultToken != empty(address):
        assert extcall IERC20(_vaultToken).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticWithdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount, _legoId, legoAddr, _isAgent)
    return assetAmountReceived, vaultTokenAmountBurned


##################
# Transfer Funds #
##################


@nonreentrant
@external
def transferFunds(_recipient: address, _amount: uint256 = max_value(uint256), _asset: address = empty(address)) -> bool:
    owner: address = self.owner
    isAgent: bool = self._isAgentWithValidation(msg.sender, owner, _asset)

    # validate recipient
    if _recipient != owner:
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

    log WalletFundsTransferred(_recipient, _asset, amount, isAgent)
    return True


# transfer whitelist


@nonreentrant
@external
def setWhitelistAddr(_addr: address, _isAllowed: bool) -> bool:
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms

    assert _addr != empty(address) # dev: invalid addr
    assert _addr != owner # dev: owner cannot be whitelisted
    assert _isAllowed != self.isRecipientAllowed[_addr] # dev: already set

    self.isRecipientAllowed[_addr] = _isAllowed
    log WhitelistAddrSet(_addr, _isAllowed)
    return True


##################
# Agent Settings #
##################


# add or modify agent settings


@nonreentrant
@external
def addOrModifyAgent(
    _agent: address,
    _allowedAssets: DynArray[address, MAX_ASSETS] = [],
    _allowedLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> bool:
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms
    assert _agent != owner # dev: agent cannot be owner
    assert _agent != empty(address) # dev: invalid agent

    agentInfo: AgentInfo = self.agentSettings[_agent]
    isNewAgent: bool = not agentInfo.isActive

    # sanitize input data
    agentInfo.allowedAssets, agentInfo.allowedLegoIds = self._sanitizeAgentInputData(_allowedAssets, _allowedLegoIds)

    # save data
    agentInfo.isActive = True
    self.agentSettings[_agent] = agentInfo

    # log event
    if isNewAgent:
        log AgentAdded(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    else:
        log AgentModified(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    return True


@view
@internal
def _sanitizeAgentInputData(
    _allowedAssets: DynArray[address, MAX_ASSETS],
    _allowedLegoIds: DynArray[uint256, MAX_LEGOS],
) -> (DynArray[address, MAX_ASSETS], DynArray[uint256, MAX_LEGOS]):

    # nothing to do here
    if len(_allowedAssets) == 0 and len(_allowedLegoIds) == 0:
        return _allowedAssets, _allowedLegoIds

    # sanitize and dedupe assets
    cleanAssets: DynArray[address, MAX_ASSETS] = []
    for i: uint256 in range(len(_allowedAssets), bound=MAX_ASSETS):
        asset: address = _allowedAssets[i]
        if asset == empty(address):
            continue
        if asset not in cleanAssets:
            cleanAssets.append(asset)

    # validate and dedupe lego ids
    cleanLegoIds: DynArray[uint256, MAX_LEGOS] = []
    if len(_allowedLegoIds) != 0:
        legoRegistry: address = self.legoRegistry
        for i: uint256 in range(len(_allowedLegoIds), bound=MAX_LEGOS):
            legoId: uint256 = _allowedLegoIds[i]
            if not staticcall LegoRegistry(legoRegistry).isValidLegoId(legoId):
                continue
            if legoId not in cleanLegoIds:
                cleanLegoIds.append(legoId)

    return cleanAssets, cleanLegoIds


# disable agent


@nonreentrant
@external
def disableAgent(_agent: address) -> bool:
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active
    self.agentSettings[_agent] = empty(AgentInfo)

    log AgentDisabled(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    return True


# add lego id for agent


@nonreentrant
@external
def addLegoIdForAgent(_agent: address, _legoId: uint256) -> bool:
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active

    assert staticcall LegoRegistry(self.legoRegistry).isValidLegoId(_legoId)
    assert _legoId not in agentInfo.allowedLegoIds # dev: lego id already saved

    # save data
    agentInfo.allowedLegoIds.append(_legoId)
    self.agentSettings[_agent] = agentInfo

    # log event
    log LegoIdAddedToAgent(_agent, _legoId)
    return True


# add asset for agent


@nonreentrant
@external
def addAssetForAgent(_agent: address, _asset: address) -> bool:
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active

    assert _asset != empty(address) # dev: invalid asset
    assert _asset not in agentInfo.allowedAssets # dev: asset already saved

    # save data
    agentInfo.allowedAssets.append(_asset)
    self.agentSettings[_agent] = agentInfo

    # log event
    log AssetAddedToAgent(_agent, _asset)
    return True



