# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

initializes: gov
exports: gov.__interface__
import contracts.modules.LocalGov as gov
from ethereum.ercs import IERC20

interface MainWallet:
    def recoverTrialFunds(_opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]) -> bool: nonpayable
    def clawBackTrialFunds() -> bool: nonpayable
    def canBeAmbassador() -> bool: view
    def apiVersion() -> String[28]: view

interface AddyRegistry:
    def setIsUserWalletOrAgent(_addr: address, _isThing: bool, _setUserWalletMap: bool) -> bool: nonpayable
    def isUserWallet(_addr: address) -> bool: view
    def isAgent(_addr: address) -> bool: view

interface WalletConfig:
    def setWallet(_wallet: address) -> bool: nonpayable

flag AddressTypes:
    USER_WALLET_TEMPLATE
    USER_WALLET_CONFIG_TEMPLATE
    AGENT_TEMPLATE
    DEFAULT_AGENT

struct AddressInfo:
    addr: address
    version: uint256
    lastModified: uint256

struct PendingAddress:
    newAddr: address
    initiatedBlock: uint256
    confirmBlock: uint256

struct TrialFundsData:
    asset: address
    amount: uint256

struct TrialFundsOpp:
    legoId: uint256
    vaultToken: address

struct TrialFundsRecovery:
    wallet: address
    opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]

event UserWalletCreated:
    mainAddr: indexed(address)
    configAddr: indexed(address)
    owner: indexed(address)
    agent: address
    ambassador: address
    creator: address

event AgentCreated:
    agent: indexed(address)
    owner: indexed(address)
    creator: address

event AddressUpdateInitiated:
    prevAddr: indexed(address)
    newAddr: indexed(address)
    confirmBlock: uint256
    addressType: AddressTypes

event AddressUpdateConfirmed:
    prevAddr: indexed(address)
    newAddr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    addressType: AddressTypes

event AddressUpdateCancelled:
    cancelledTemplate: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    addressType: AddressTypes

event AddressChangeDelaySet:
    delayBlocks: uint256

event WhitelistSet:
    addr: address
    shouldWhitelist: bool

event ShouldEnforceWhitelistSet:
    shouldEnforce: bool

event NumUserWalletsAllowedSet:
    numAllowed: uint256

event NumAgentsAllowedSet:
    numAllowed: uint256

event AgentBlacklistSet:
    agentAddr: indexed(address)
    shouldBlacklist: bool

event CanCriticalCancelSet:
    addr: indexed(address)
    canCancel: bool

event TrialFundsDataSet:
    asset: indexed(address)
    amount: uint256

event AmbassadorYieldBonusPaid:
    user: indexed(address)
    ambassador: indexed(address)
    asset: indexed(address)
    amount: uint256
    ratio: uint256

event AmbassadorBonusRatioSet:
    ratio: uint256

event AgentFactoryFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AgentFactoryActivated:
    isActivated: bool

# user wallets
isUserWalletLocal: public(HashMap[address, bool])
numUserWallets: public(uint256)

# agents
isAgentLocal: public(HashMap[address, bool])
numAgents: public(uint256)

# important addresses (mostly templates)
addressInfo: public(HashMap[AddressTypes, AddressInfo])
pendingAddress: public(HashMap[AddressTypes, PendingAddress])
addressChangeDelay: public(uint256)

# ambassador bonus
ambassadorBonusRatio: public(uint256)

# trial funds
trialFundsData: public(TrialFundsData)

# limits / controls
numUserWalletsAllowed: public(uint256)
numAgentsAllowed: public(uint256)
whitelist: public(HashMap[address, bool])
shouldEnforceWhitelist: public(bool)
agentBlacklist: public(HashMap[address, bool])
canCriticalCancel: public(HashMap[address, bool])

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))
WETH_ADDR: public(immutable(address))

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_RECOVERIES: constant(uint256) = 100
MAX_LEGOS: constant(uint256) = 20

MIN_OWNER_CHANGE_DELAY: public(immutable(uint256))
MAX_OWNER_CHANGE_DELAY: public(immutable(uint256))
MIN_ADDRESS_CHANGE_DELAY: public(immutable(uint256))
MAX_ADDRESS_CHANGE_DELAY: public(immutable(uint256))


@deploy
def __init__(
    _addyRegistry: address,
    _wethAddr: address,
    _userWalletTemplate: address,
    _userConfigTemplate: address,
    _agentTemplate: address,
    _defaultAgent: address,
    _minChangeDelay: uint256,
    _maxChangeDelay: uint256,
):
    assert empty(address) not in [_addyRegistry, _wethAddr] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry
    WETH_ADDR = _wethAddr

    assert _minChangeDelay <= _maxChangeDelay # dev: invalid delay
    MIN_OWNER_CHANGE_DELAY = _minChangeDelay
    MAX_OWNER_CHANGE_DELAY = _maxChangeDelay
    MIN_ADDRESS_CHANGE_DELAY = _minChangeDelay
    MAX_ADDRESS_CHANGE_DELAY = _maxChangeDelay

    self.addressChangeDelay = _minChangeDelay
    self.isActivated = True

    # set user wallet templates
    if self._isValidAddress(_userWalletTemplate, empty(address)) and self._isValidAddress(_userConfigTemplate, empty(address)):
        self._setAddress(AddressTypes.USER_WALLET_TEMPLATE, _userWalletTemplate, 1)
        self._setAddress(AddressTypes.USER_WALLET_CONFIG_TEMPLATE, _userConfigTemplate, 1)

    # set agent template
    if self._isValidAddress(_agentTemplate, empty(address)):
        self._setAddress(AddressTypes.AGENT_TEMPLATE, _agentTemplate, 1)

    # set default agent
    if self._isValidAddress(_defaultAgent, empty(address)):
        self._setAddress(AddressTypes.DEFAULT_AGENT, _defaultAgent, 1)

    # local gov
    gov.__init__(empty(address), _addyRegistry, 0, 0)


######################
# Create User Wallet #
######################


@view
@external
def isUserWallet(_addr: address) -> bool:
    """
    @notice Check if a given address is a user wallet within Underscore Protocol
    @dev Returns True if the address is a user wallet, False otherwise
    """
    return self._isUserWallet(_addr)


@view
@internal
def _isUserWallet(_addr: address) -> bool:
    isUserWallet: bool = self.isUserWalletLocal[_addr]
    if isUserWallet:
        return True
    return staticcall AddyRegistry(ADDY_REGISTRY).isUserWallet(_addr)


@external
def createUserWallet(
    _owner: address = msg.sender,
    _ambassador: address = empty(address),
    _shouldUseTrialFunds: bool = True,
) -> address:
    """
    @notice Create a new User Wallet with specified owner and optional agent
    @dev Creates a minimal proxy of the current template and initializes it
    @param _owner The address that will own the wallet (defaults to msg.sender)
    @param _ambassador The address of the ambassador who invited the user (defaults to empty address)
    @param _shouldUseTrialFunds Whether to use trial funds (defaults to True)
    @return The address of the newly created wallet, or empty address if setup is invalid
    """
    assert self.isActivated # dev: not activated

    # get templates
    userWalletTemplate: address = self.addressInfo[AddressTypes.USER_WALLET_TEMPLATE].addr
    walletConfigTemplate: address = self.addressInfo[AddressTypes.USER_WALLET_CONFIG_TEMPLATE].addr
    assert empty(address) not in [userWalletTemplate, walletConfigTemplate, _owner] # dev: invalid setup

    # check safety / limits
    if self.shouldEnforceWhitelist and not self.whitelist[msg.sender]:
        return empty(address)
    if self.numUserWallets >= self.numUserWalletsAllowed:
        return empty(address)

    # validate ambassador
    ambassador: address = empty(address)
    if _ambassador != empty(address):
        assert self._isUserWallet(_ambassador) # dev: ambassador must be Underscore wallet
        version: String[28] = staticcall MainWallet(_ambassador).apiVersion()
        if version != "0.0.1" and version != "0.0.2" and staticcall MainWallet(_ambassador).canBeAmbassador():
            ambassador = _ambassador

    # initial trial funds asset + amount
    trialFundsData: TrialFundsData = self.trialFundsData
    if _shouldUseTrialFunds and trialFundsData.asset != empty(address):
        trialFundsData.amount = min(trialFundsData.amount, staticcall IERC20(trialFundsData.asset).balanceOf(self))

    # create wallet contracts
    defaultAgent: address = self.addressInfo[AddressTypes.DEFAULT_AGENT].addr
    walletConfigAddr: address = create_from_blueprint(walletConfigTemplate, _owner, defaultAgent, ambassador, ADDY_REGISTRY, MIN_OWNER_CHANGE_DELAY, MAX_OWNER_CHANGE_DELAY)
    mainWalletAddr: address = create_from_blueprint(userWalletTemplate, walletConfigAddr, ADDY_REGISTRY, WETH_ADDR, trialFundsData.asset, trialFundsData.amount)
    assert extcall WalletConfig(walletConfigAddr).setWallet(mainWalletAddr) # dev: could not set wallet

    # transfer after initialization
    if trialFundsData.amount != 0:
        assert extcall IERC20(trialFundsData.asset).transfer(mainWalletAddr, trialFundsData.amount, default_return_value=True) # dev: gift transfer failed

    # update data
    assert extcall AddyRegistry(ADDY_REGISTRY).setIsUserWalletOrAgent(mainWalletAddr, True, True) # dev: could not set is user wallet
    self.isUserWalletLocal[mainWalletAddr] = True
    self.numUserWallets += 1

    log UserWalletCreated(mainAddr=mainWalletAddr, configAddr=walletConfigAddr, owner=_owner, agent=defaultAgent, ambassador=ambassador, creator=msg.sender)
    return mainWalletAddr


################
# Create Agent #
################


@view
@external
def isAgent(_addr: address) -> bool:
    """
    @notice Check if a given address is an agent within Underscore Protocol
    @dev Returns True if the address is an agent, False otherwise
    """
    return self._isAgent(_addr)


@view
@internal
def _isAgent(_addr: address) -> bool:
    isAgent: bool = self.isAgentLocal[_addr]
    if isAgent:
        return True
    return staticcall AddyRegistry(ADDY_REGISTRY).isAgent(_addr)


@external
def createAgent(_owner: address = msg.sender) -> address:
    """
    @notice Create a new Agent with specified owner
    @dev Creates a minimal proxy of the current template and initializes it
    @param _owner The address that will own the agent (defaults to msg.sender)
    @return The address of the newly created agent, or empty address if setup is invalid
    """
    assert self.isActivated # dev: not activated

    agentTemplate: address = self.addressInfo[AddressTypes.AGENT_TEMPLATE].addr
    assert empty(address) not in [agentTemplate, _owner] # dev: invalid setup

    # check limits
    if self.shouldEnforceWhitelist and not self.whitelist[msg.sender]:
        return empty(address)
    if self.numAgents >= self.numAgentsAllowed:
        return empty(address)

    # create agent contract
    agentAddr: address = create_from_blueprint(agentTemplate, _owner, ADDY_REGISTRY, MIN_OWNER_CHANGE_DELAY, MAX_OWNER_CHANGE_DELAY)

    # update data
    assert extcall AddyRegistry(ADDY_REGISTRY).setIsUserWalletOrAgent(agentAddr, True, False) # dev: could not set is agent
    self.isAgentLocal[agentAddr] = True
    self.numAgents += 1

    log AgentCreated(agent=agentAddr, owner=_owner, creator=msg.sender)
    return agentAddr


#############
# Templates #
#############


# core user wallet


@external
def initiateUserWalletTemplateUpdate(_newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._initiateAddressUpdate(AddressTypes.USER_WALLET_TEMPLATE, _newAddr, self.addressInfo[AddressTypes.USER_WALLET_TEMPLATE].addr)


@external
def confirmUserWalletTemplateUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._confirmAddressUpdate(AddressTypes.USER_WALLET_TEMPLATE)


@external
def cancelUserWalletTemplateUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelAddressUpdate(AddressTypes.USER_WALLET_TEMPLATE)


@view
@external
def getUserWalletTemplateAddr() -> address:
    return self.addressInfo[AddressTypes.USER_WALLET_TEMPLATE].addr


@view
@external
def getUserWalletTemplateInfo() -> AddressInfo:
    return self.addressInfo[AddressTypes.USER_WALLET_TEMPLATE]


@view
@external
def getPendingUserWalletTemplateUpdate() -> PendingAddress:
    return self.pendingAddress[AddressTypes.USER_WALLET_TEMPLATE]


@view
@external
def hasPendingUserWalletTemplateUpdate() -> bool:
    return self._hasPendingAddressUpdate(AddressTypes.USER_WALLET_TEMPLATE)


# user wallet config


@external
def initiateUserWalletConfigTemplateUpdate(_newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._initiateAddressUpdate(AddressTypes.USER_WALLET_CONFIG_TEMPLATE, _newAddr, self.addressInfo[AddressTypes.USER_WALLET_CONFIG_TEMPLATE].addr)


@external
def confirmUserWalletConfigTemplateUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._confirmAddressUpdate(AddressTypes.USER_WALLET_CONFIG_TEMPLATE)


@external
def cancelUserWalletConfigTemplateUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelAddressUpdate(AddressTypes.USER_WALLET_CONFIG_TEMPLATE)


@view
@external
def getUserWalletConfigTemplateAddr() -> address:
    return self.addressInfo[AddressTypes.USER_WALLET_CONFIG_TEMPLATE].addr


@view
@external
def getUserWalletConfigTemplateInfo() -> AddressInfo:
    return self.addressInfo[AddressTypes.USER_WALLET_CONFIG_TEMPLATE]


@view
@external
def getPendingUserWalletConfigTemplateUpdate() -> PendingAddress:
    return self.pendingAddress[AddressTypes.USER_WALLET_CONFIG_TEMPLATE]


@view
@external
def hasPendingUserWalletConfigTemplateUpdate() -> bool:
    return self._hasPendingAddressUpdate(AddressTypes.USER_WALLET_CONFIG_TEMPLATE)


# agent template


@external
def initiateAgentTemplateUpdate(_newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._initiateAddressUpdate(AddressTypes.AGENT_TEMPLATE, _newAddr, self.addressInfo[AddressTypes.AGENT_TEMPLATE].addr)


@external
def confirmAgentTemplateUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._confirmAddressUpdate(AddressTypes.AGENT_TEMPLATE)


@external
def cancelAgentTemplateUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelAddressUpdate(AddressTypes.AGENT_TEMPLATE)


@view
@external
def getAgentTemplateAddr() -> address:
    return self.addressInfo[AddressTypes.AGENT_TEMPLATE].addr


@view
@external
def getAgentTemplateInfo() -> AddressInfo:
    return self.addressInfo[AddressTypes.AGENT_TEMPLATE]


@view
@external
def getPendingAgentTemplateUpdate() -> PendingAddress:
    return self.pendingAddress[AddressTypes.AGENT_TEMPLATE]


@view
@external
def hasPendingAgentTemplateUpdate() -> bool:
    return self._hasPendingAddressUpdate(AddressTypes.AGENT_TEMPLATE)


# shared utilities


@view
@internal
def _hasPendingAddressUpdate(_addressType: AddressTypes) -> bool:
    return self.pendingAddress[_addressType].confirmBlock != 0


@view
@internal
def _isValidAddress(_newAddr: address, _oldAddr: address) -> bool:
    if _newAddr == empty(address) or not _newAddr.is_contract:
        return False
    return _newAddr != _oldAddr


@internal
def _initiateAddressUpdate(_addressType: AddressTypes, _newAddr: address, _oldAddr: address) -> bool:
    """
    @notice Initiate an address update
    @dev Only callable by the governor, updates the address change delay
    @param _addressType The type of address to update
    @param _newAddr The new address
    @param _oldAddr The old address
    @return True if the address update was initiated successfully, False otherwise
    """
    if not self._isValidAddress(_newAddr, _oldAddr):
        return False

    confirmBlock: uint256 = block.number + self.addressChangeDelay
    self.pendingAddress[_addressType] = PendingAddress(
        newAddr= _newAddr,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log AddressUpdateInitiated(prevAddr=_oldAddr, newAddr=_newAddr, confirmBlock=confirmBlock, addressType=_addressType)
    return True


@internal
def _confirmAddressUpdate(_addressType: AddressTypes) -> bool:
    """
    @notice Confirm an address update
    @dev Only callable by the governor, updates the address
    @param _addressType The type of address to update
    @return True if the address update was confirmed successfully, False otherwise
    """
    data: PendingAddress = self.pendingAddress[_addressType]
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached

    prevTemplateInfo: AddressInfo = self.addressInfo[_addressType]
    if not self._isValidAddress(data.newAddr, prevTemplateInfo.addr):
        self.pendingAddress[_addressType] = empty(PendingAddress)
        return False

    self._setAddress(_addressType, data.newAddr, prevTemplateInfo.version + 1)
    self.pendingAddress[_addressType] = empty(PendingAddress)
    log AddressUpdateConfirmed(prevAddr=prevTemplateInfo.addr, newAddr=data.newAddr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, addressType=_addressType)
    return True


@internal
def _setAddress(_addressType: AddressTypes, _newAddr: address, _newVersion: uint256):
    self.addressInfo[_addressType] = AddressInfo(
        addr= _newAddr,
        version= _newVersion,
        lastModified=block.timestamp,
    )


@internal
def _cancelAddressUpdate(_addressType: AddressTypes) -> bool:
    """
    @notice Cancel an address update
    @dev Only callable by the governor, cancels the address update
    @param _addressType The type of address to update
    @return True if the address update was cancelled successfully, False otherwise
    """
    data: PendingAddress = self.pendingAddress[_addressType]
    assert data.confirmBlock != 0 # dev: no pending change

    self.pendingAddress[_addressType] = empty(PendingAddress)
    log AddressUpdateCancelled(cancelledTemplate=data.newAddr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, addressType=_addressType)
    return True


# time delay config


@external
def setAddressChangeDelay(_numBlocks: uint256):
    """
    @notice Set the address change delay
    @dev Only callable by the governor, updates the address change delay
    @param _numBlocks The new address change delay in blocks
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _numBlocks >= MIN_ADDRESS_CHANGE_DELAY and _numBlocks <= MAX_ADDRESS_CHANGE_DELAY # dev: invalid delay
    self.addressChangeDelay = _numBlocks
    log AddressChangeDelaySet(delayBlocks=_numBlocks)


###################
# Safety / Limits #
###################


# who can create wallets / agents


@external
def setWhitelist(_addr: address, _shouldWhitelist: bool) -> bool:
    """
    @notice Set the whitelist status for a given address
    @dev Only callable by the governor, updates the whitelist state
    @param _addr The address to set the whitelist status for
    @param _shouldWhitelist True to whitelist, False to unwhitelist
    @return True if the whitelist status was successfully updated, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    self.whitelist[_addr] = _shouldWhitelist
    log WhitelistSet(addr=_addr, shouldWhitelist=_shouldWhitelist)
    return True


@external
def setShouldEnforceWhitelist(_shouldEnforce: bool) -> bool:
    """
    @notice Set whether to enforce the whitelist for agent/wallet creation
    @dev Only callable by the governor, updates the whitelist enforcement state
    @param _shouldEnforce True to enforce whitelist, False to disable
    @return True if the whitelist enforcement state was successfully updated, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    self.shouldEnforceWhitelist = _shouldEnforce
    log ShouldEnforceWhitelistSet(shouldEnforce=_shouldEnforce)
    return True


# total num allowed (agents / wallets)


@external
def setNumUserWalletsAllowed(_numAllowed: uint256 = max_value(uint256)) -> bool:
    """
    @notice Set the maximum number of user wallets allowed
    @dev Only callable by the governor, updates the maximum number of user wallets
    @param _numAllowed The new maximum number of user wallets allowed
    @return True if the maximum number was successfully updated, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    self.numUserWalletsAllowed = _numAllowed
    log NumUserWalletsAllowedSet(numAllowed=_numAllowed)
    return True


@external
def setNumAgentsAllowed(_numAllowed: uint256 = max_value(uint256)) -> bool:
    """
    @notice Set the maximum number of agents allowed
    @dev Only callable by the governor, updates the maximum number of agents
    @param _numAllowed The new maximum number of agents allowed
    @return True if the maximum number was successfully updated, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    self.numAgentsAllowed = _numAllowed
    log NumAgentsAllowedSet(numAllowed=_numAllowed)
    return True


# agent blacklist


@external
def setAgentBlacklist(_agentAddr: address, _shouldBlacklist: bool) -> bool:
    """
    @notice Set the blacklist status for a given agent address
    @dev Only callable by the governor, updates the blacklist state
    @param _agentAddr The address to set the blacklist status for
    @param _shouldBlacklist True to blacklist, False to unblacklist
    @return True if the blacklist status was successfully updated, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    self.agentBlacklist[_agentAddr] = _shouldBlacklist
    log AgentBlacklistSet(agentAddr=_agentAddr, shouldBlacklist=_shouldBlacklist)
    return True


# cancel critical actions (on behalf of users)


@view
@external
def canCancelCriticalAction(_addr: address) -> bool:
    """
    @notice Check if an address can perform critical cancellations
    @dev Returns true if the address is whitelisted or the governor
    """
    return self.canCriticalCancel[_addr] or gov._canGovern(_addr)


@external
def setCanCriticalCancel(_addr: address, _canCancel: bool) -> bool:
    """
    @notice Set whether an address can perform critical cancellations
    @dev Only callable by the governor, updates the critical cancel state
    @param _addr The address to set the critical cancel state for
    @param _canCancel True to allow permissions for critical cancel, False to disallow
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    if _addr == empty(address) or self.canCriticalCancel[_addr] == _canCancel or gov._canGovern(_addr):
        return False

    self.canCriticalCancel[_addr] = _canCancel
    log CanCriticalCancelSet(addr=_addr, canCancel=_canCancel)
    return True


###############
# Trial Funds #
###############


@external
def setTrialFundsData(_asset: address, _amount: uint256) -> bool:
    """
    @notice Set the trial funds asset and amount for future wallet deployments
    @dev Only callable by the governor, updates the trial funds data
    @param _asset The address of the asset to set
    @param _amount The amount of the asset to set
    @return True if the data was successfully updated, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    if not _asset.is_contract or _asset == empty(address) or _amount == 0:
        return False

    self.trialFundsData = TrialFundsData(
        asset=_asset,
        amount=_amount,
    )
    log TrialFundsDataSet(asset=_asset, amount=_amount)
    return True


@external
def clawBackTrialFunds(_wallets: DynArray[address, MAX_RECOVERIES]) -> bool:
    """
    @notice Claw back trial funds from a list of wallets
    @dev Only callable by the governor or critical cancel address, transfers funds back here
    @param _wallets The list of wallets to claw back funds from
    @return True if the funds were successfully clawed back, False otherwise
    """
    assert self.canCriticalCancel[msg.sender] or gov._canGovern(msg.sender) # dev: no perms
    for w: address in _wallets:
        assert extcall MainWallet(w).clawBackTrialFunds() # dev: clawback failed
    return True


@external
def clawBackTrialFundsLegacy(_recoveries: DynArray[TrialFundsRecovery, MAX_RECOVERIES]) -> bool:
    assert self.canCriticalCancel[msg.sender] or gov._canGovern(msg.sender) # dev: no perms
    for r: TrialFundsRecovery in _recoveries:
        assert extcall MainWallet(r.wallet).recoverTrialFunds(r.opportunities) # dev: recovery failed
    return True


####################
# Ambassador Bonus #
####################


@external
def payAmbassadorYieldBonus(_ambassador: address, _asset: address, _amount: uint256) -> bool:
    """
    @notice Pay an ambassador yield bonus
    @dev Only callable by a wallet, transfers bonus to ambassador
    @param _ambassador The address of the ambassador to pay the bonus to
    @param _asset The address of the asset to pay the bonus from
    @param _amount The amount of the bonus to pay
    """
    if not self.isActivated:
        return False

    # make sure have correct inputs
    if _ambassador == empty(address) or _asset == empty(address) or _amount == 0:
        return False

    # make sure sender is a wallet
    wallet: address = msg.sender
    if not self._isUserWallet(wallet):
        return False

    # check if bonus ratio is set
    ambassadorBonusRatio: uint256 = self.ambassadorBonusRatio
    if ambassadorBonusRatio == 0:
        return False

    # calculate bonus amount, transfer to ambassador
    bonusAmount: uint256 = min(_amount * ambassadorBonusRatio // HUNDRED_PERCENT, staticcall IERC20(_asset).balanceOf(self))
    if bonusAmount == 0:
        return False

    assert extcall IERC20(_asset).transfer(_ambassador, bonusAmount, default_return_value=True) # dev: bonus transfer failed
    log AmbassadorYieldBonusPaid(user=wallet, ambassador=_ambassador, asset=_asset, amount=bonusAmount, ratio=ambassadorBonusRatio)
    return True


@external
def setAmbassadorBonusRatio(_bonusRatio: uint256) -> bool:
    """
    @notice Set the bonus ratio for ambassadors
    @dev Only callable by governor
    @param _bonusRatio The bonus ratio for ambassadors
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _bonusRatio <= HUNDRED_PERCENT # dev: invalid ratio
    self.ambassadorBonusRatio = _bonusRatio
    log AmbassadorBonusRatioSet(ratio=_bonusRatio)
    return True


#################
# Default Agent #
#################


@external
def initiateDefaultAgentUpdate(_newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if not self._isAgent(_newAddr):
        return False
    return self._initiateAddressUpdate(AddressTypes.DEFAULT_AGENT, _newAddr, self.addressInfo[AddressTypes.DEFAULT_AGENT].addr)


@external
def confirmDefaultAgentUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if not self._isAgent(self.pendingAddress[AddressTypes.DEFAULT_AGENT].newAddr):
        return False
    return self._confirmAddressUpdate(AddressTypes.DEFAULT_AGENT)


@external
def cancelDefaultAgentUpdate() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelAddressUpdate(AddressTypes.DEFAULT_AGENT)


@view
@external
def getDefaultAgentAddr() -> address:
    return self.addressInfo[AddressTypes.DEFAULT_AGENT].addr


@view
@external
def getDefaultAgentInfo() -> AddressInfo:
    return self.addressInfo[AddressTypes.DEFAULT_AGENT]


@view
@external
def getPendingDefaultAgentUpdate() -> PendingAddress:
    return self.pendingAddress[AddressTypes.DEFAULT_AGENT]


@view
@external
def hasPendingDefaultAgentUpdate() -> bool:
    return self._hasPendingAddressUpdate(AddressTypes.DEFAULT_AGENT)


####################################
# Recover Funds From Agent Factory #
####################################


@external
def recoverFundsFromAgentFactory(_asset: address, _recipient: address) -> bool:
    """
    @notice Recover funds from the factory
    @dev Only callable by the governor, transfers funds to the recipient
    @param _asset The address of the asset to recover
    @param _recipient The address to send the funds to
    @return True if the funds were successfully recovered, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log AgentFactoryFundsRecovered(asset=_asset, recipient=_recipient, balance=balance)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    """
    @notice Enable or disable the factory's ability to create new wallets
    @dev Only callable by the governor, toggles isActivated state
    @param _shouldActivate True to activate the factory, False to deactivate
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    self.isActivated = _shouldActivate
    log AgentFactoryActivated(isActivated=_shouldActivate)
