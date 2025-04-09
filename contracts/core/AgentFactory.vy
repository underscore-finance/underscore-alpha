# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

initializes: gov
exports: gov.__interface__
import contracts.modules.Governable as gov
from ethereum.ercs import IERC20

interface MainWallet:
    def initialize(_walletConfig: address, _addyRegistry: address, _wethAddr: address, _trialFundsAsset: address, _trialFundsInitialAmount: uint256) -> bool: nonpayable
    def recoverTrialFunds(_opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]) -> bool: nonpayable

interface WalletConfig:
    def initialize(_wallet: address, _addyRegistry: address, _owner: address, _initialAgent: address) -> bool: nonpayable

interface Agent:
    def initialize(_owner: address) -> bool: nonpayable

struct TemplateInfo:
    addr: address
    version: uint256
    lastModified: uint256

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
    creator: address

event AgentCreated:
    agent: indexed(address)
    owner: indexed(address)
    creator: address

event UserWalletTemplateSet:
    template: indexed(address)
    version: uint256

event UserWalletConfigTemplateSet:
    template: indexed(address)
    version: uint256

event AgentTemplateSet:
    template: indexed(address)
    version: uint256

event TrialFundsDataSet:
    asset: indexed(address)
    amount: uint256

event WhitelistSet:
    addr: address
    shouldWhitelist: bool

event NumUserWalletsAllowedSet:
    numAllowed: uint256

event NumAgentsAllowedSet:
    numAllowed: uint256

event ShouldEnforceWhitelistSet:
    shouldEnforce: bool

event AgentBlacklistSet:
    agentAddr: indexed(address)
    shouldBlacklist: bool

event AgentFactoryFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AgentFactoryActivated:
    isActivated: bool

trialFundsData: public(TrialFundsData)

# user wallets
userWalletTemplate: public(TemplateInfo)
userWalletConfig: public(TemplateInfo)
isUserWallet: public(HashMap[address, bool])
numUserWallets: public(uint256)

# agents
agentTemplateInfo: public(TemplateInfo)
isAgent: public(HashMap[address, bool])
numAgents: public(uint256)

# limits / controls
agentBlacklist: public(HashMap[address, bool])
numUserWalletsAllowed: public(uint256)
numAgentsAllowed: public(uint256)
whitelist: public(HashMap[address, bool])
shouldEnforceWhitelist: public(bool)

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))
WETH_ADDR: public(immutable(address))

MAX_RECOVERIES: constant(uint256) = 100
MAX_LEGOS: constant(uint256) = 20


@deploy
def __init__(
    _addyRegistry: address,
    _wethAddr: address,
    _userWalletTemplate: address,
    _userConfigTemplate: address,
    _agentTemplate: address,
):
    assert empty(address) not in [_addyRegistry, _wethAddr] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry
    WETH_ADDR = _wethAddr
    gov.__init__(_addyRegistry)
    self.isActivated = True

    # set agent template
    if self._isValidUserWalletTemplate(_userWalletTemplate) and self._isValidUserWalletConfigTemplate(_userConfigTemplate):
        self._setUserWalletTemplate(_userWalletTemplate)
        self._setUserWalletConfigTemplate(_userConfigTemplate)

    # set agent template
    if self._isValidAgentTemplate(_agentTemplate):
        self._setAgentTemplate(_agentTemplate)


@view
@external
def currentUserWalletTemplate() -> address:
    """
    @notice Get the current wallet template address being used by the factory
    @dev This is a simple getter for the current template address stored in userWalletTemplate
    @return The address of the current wallet template
    """
    return self.userWalletTemplate.addr


@view
@external
def currentUserWalletConfigTemplate() -> address:
    """
    @notice Get the current wallet config template address being used by the factory
    @dev This is a simple getter for the current template address stored in userWalletConfig
    @return The address of the current wallet config template
    """
    return self.userWalletConfig.addr


@view
@external
def currentAgentTemplate() -> address:
    """
    @notice Get the current agent template address being used by the factory
    @dev This is a simple getter for the current template address stored in agentTemplateInfo
    @return The address of the current agent template
    """
    return self.agentTemplateInfo.addr


######################
# Create User Wallet #
######################


@view
@external 
def isValidUserWalletSetup(_owner: address, _agent: address) -> bool:
    """
    @notice Check if the provided owner and agent addresses form a valid wallet setup
    @dev Validates that both templates exist and owner/agent combination is valid
    @param _owner The address that will own the wallet
    @param _agent The address that will be the agent (can be empty)
    @return True if the setup is valid, False otherwise
    """
    return self._isValidUserWalletSetup(self.userWalletTemplate.addr, self.userWalletConfig.addr, _owner, _agent)


@view
@internal 
def _isValidUserWalletSetup(_mainTemplate: address, _configTemplate: address, _owner: address, _agent: address) -> bool:
    if _mainTemplate == empty(address) or _configTemplate == empty(address):
        return False
    return _owner != empty(address) and _owner != _agent


@external
def createUserWallet(_owner: address = msg.sender, _agent: address = empty(address)) -> address:
    """
    @notice Create a new User Wallet with specified owner and optional agent
    @dev Creates a minimal proxy of the current template and initializes it
    @param _owner The address that will own the wallet (defaults to msg.sender)
    @param _agent The address that will be the agent (defaults to empty address, can add this later)
    @return The address of the newly created wallet, or empty address if setup is invalid
    """
    assert self.isActivated # dev: not activated

    mainWalletTemplate: address = self.userWalletTemplate.addr
    walletConfigTemplate: address = self.userWalletConfig.addr
    if not self._isValidUserWalletSetup(mainWalletTemplate, walletConfigTemplate, _owner, _agent):
        return empty(address)

    # check limits
    if self.shouldEnforceWhitelist and not self.whitelist[msg.sender]:
        return empty(address)
    if self.numUserWallets >= self.numUserWalletsAllowed:
        return empty(address)

    # create both contracts (main wallet and wallet config)
    mainWalletAddr: address = create_minimal_proxy_to(mainWalletTemplate)
    walletConfigAddr: address = create_minimal_proxy_to(walletConfigTemplate)

    # initial trial funds asset + amount
    trialFundsData: TrialFundsData = self.trialFundsData
    if trialFundsData.asset != empty(address):
        trialFundsData.amount = min(trialFundsData.amount, staticcall IERC20(trialFundsData.asset).balanceOf(self))

    # initalize main wallet and wallet config
    assert extcall MainWallet(mainWalletAddr).initialize(walletConfigAddr, ADDY_REGISTRY, WETH_ADDR, trialFundsData.asset, trialFundsData.amount) # dev: could not initialize main wallet
    assert extcall WalletConfig(walletConfigAddr).initialize(mainWalletAddr, ADDY_REGISTRY, _owner, _agent) # dev: could not initialize wallet config

    # transfer after initialization
    if trialFundsData.amount != 0:
        assert extcall IERC20(trialFundsData.asset).transfer(mainWalletAddr, trialFundsData.amount, default_return_value=True) # dev: gift transfer failed

    # update data
    self.isUserWallet[mainWalletAddr] = True
    self.numUserWallets += 1

    log UserWalletCreated(mainAddr=mainWalletAddr, configAddr=walletConfigAddr, owner=_owner, agent=_agent, creator=msg.sender)
    return mainWalletAddr


#########################
# User Wallet Templates #
#########################


# main user wallet


@view
@external 
def isValidUserWalletTemplate(_newAddr: address) -> bool:
    """
    @notice Check if a given address is valid to be used as a new user wallet template
    @dev Validates the address is a contract and different from current template
    @param _newAddr The address to validate as a potential new template
    @return True if the address can be used as a template, False otherwise
    """
    return self._isValidUserWalletTemplate(_newAddr)


@view
@internal 
def _isValidUserWalletTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.userWalletTemplate.addr


@external
def setUserWalletTemplate(_addr: address) -> bool:
    """
    @notice Set a new main wallet template address for future wallet deployments
    @dev Only callable by the governor, updates template info and emits event
    @param _addr The address of the new template to use
    @return True if template was successfully updated, False if invalid address
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidUserWalletTemplate(_addr):
        return False
    return self._setUserWalletTemplate(_addr)


@internal
def _setUserWalletTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.userWalletTemplate
    newData: TemplateInfo = TemplateInfo(
        addr=_addr,
        version=prevData.version + 1,
        lastModified=block.timestamp,
    )
    self.userWalletTemplate = newData
    log UserWalletTemplateSet(template=_addr, version=newData.version)
    return True


# user config


@view
@external 
def isValidUserWalletConfigTemplate(_newAddr: address) -> bool:
    """
    @notice Check if a given address is valid to be used as a new user wallet config template
    @dev Validates the address is a contract and different from current template
    @param _newAddr The address to validate as a potential new template
    @return True if the address can be used as a template, False otherwise
    """
    return self._isValidUserWalletConfigTemplate(_newAddr)


@view
@internal 
def _isValidUserWalletConfigTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.userWalletConfig.addr


@external
def setUserWalletConfigTemplate(_addr: address) -> bool:
    """
    @notice Set a new user wallet config template address for future wallet deployments
    @dev Only callable by the governor, updates template info and emits event
    @param _addr The address of the new template to use
    @return True if template was successfully updated, False if invalid address
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidUserWalletConfigTemplate(_addr):
        return False
    return self._setUserWalletConfigTemplate(_addr)


@internal
def _setUserWalletConfigTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.userWalletConfig
    newData: TemplateInfo = TemplateInfo(
        addr=_addr,
        version=prevData.version + 1,
        lastModified=block.timestamp,
    )
    self.userWalletConfig = newData
    log UserWalletConfigTemplateSet(template=_addr, version=newData.version)
    return True


################
# Create Agent #
################


@view
@external 
def isValidAgentSetup(_owner: address) -> bool:
    """
    @notice Check if the provided owner address forms a valid agent setup
    @dev Validates that the template exists and owner is not empty
    @param _owner The address that will own the agent
    @return True if the setup is valid, False otherwise
    """
    return self._isValidAgentSetup(self.agentTemplateInfo.addr, _owner)


@view
@internal 
def _isValidAgentSetup(_agentTemplateInfo: address, _owner: address) -> bool:
    if _agentTemplateInfo == empty(address):
        return False
    return _owner != empty(address)


@external
def createAgent(_owner: address = msg.sender) -> address:
    """
    @notice Create a new Agent with specified owner
    @dev Creates a minimal proxy of the current template and initializes it
    @param _owner The address that will own the agent (defaults to msg.sender)
    @return The address of the newly created agent, or empty address if setup is invalid
    """
    assert self.isActivated # dev: not activated

    agentTemplateInfo: address = self.agentTemplateInfo.addr
    if not self._isValidAgentSetup(agentTemplateInfo, _owner):
        return empty(address)

    # check limits
    if self.shouldEnforceWhitelist and not self.whitelist[msg.sender]:
        return empty(address)
    if self.numAgents >= self.numAgentsAllowed:
        return empty(address)

    # create agent contract
    agentAddr: address = create_minimal_proxy_to(agentTemplateInfo)
    assert extcall Agent(agentAddr).initialize(_owner) # dev: could not initialize agent

    # update data
    self.isAgent[agentAddr] = True
    self.numAgents += 1

    log AgentCreated(agent=agentAddr, owner=_owner, creator=msg.sender)
    return agentAddr


# agent template


@view
@external 
def isValidAgentTemplate(_newAddr: address) -> bool:
    """
    @notice Check if a given address is valid to be used as a new agent template
    @dev Validates the address is a contract and different from current template
    @param _newAddr The address to validate as a potential new template
    @return True if the address can be used as a template, False otherwise
    """
    return self._isValidAgentTemplate(_newAddr)


@view
@internal 
def _isValidAgentTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.agentTemplateInfo.addr


@external
def setAgentTemplate(_addr: address) -> bool:
    """
    @notice Set a new agent template address for future agent deployments
    @dev Only callable by the governor, updates template info and emits event
    @param _addr The address of the new template to use
    @return True if template was successfully updated, False if invalid address
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidAgentTemplate(_addr):
        return False
    return self._setAgentTemplate(_addr)


@internal
def _setAgentTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.agentTemplateInfo
    newData: TemplateInfo = TemplateInfo(
        addr=_addr,
        version=prevData.version + 1,
        lastModified=block.timestamp,
    )
    self.agentTemplateInfo = newData
    log AgentTemplateSet(template=_addr, version=newData.version)
    return True


###############
# Trial Funds #
###############


@view
@external 
def isValidTrialFundsData(_asset: address, _amount: uint256) -> bool:
    """
    @notice Check if the provided asset and amount form a valid trial funds setup
    @dev Validates that the asset is a contract and amount is not zero
    @param _asset The address of the asset to validate
    @param _amount The amount of the asset to validate
    @return True if the setup is valid, False otherwise
    """
    return self._isValidTrialFundsData(_asset, _amount)


@view
@internal 
def _isValidTrialFundsData(_asset: address, _amount: uint256) -> bool:
    if not _asset.is_contract or _asset == empty(address):
        return False
    return _amount != 0


@external
def setTrialFundsData(_asset: address, _amount: uint256) -> bool:
    """
    @notice Set the trial funds asset and amount for future wallet deployments
    @dev Only callable by the governor, updates the trial funds data
    @param _asset The address of the asset to set
    @param _amount The amount of the asset to set
    @return True if the data was successfully updated, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidTrialFundsData(_asset, _amount):
        return False

    self.trialFundsData = TrialFundsData(
        asset=_asset,
        amount=_amount,
    )
    log TrialFundsDataSet(asset=_asset, amount=_amount)
    return True


########################
# Whitelist and Limits #
########################


@external
def setWhitelist(_addr: address, _shouldWhitelist: bool) -> bool:
    """
    @notice Set the whitelist status for a given address
    @dev Only callable by the governor, updates the whitelist state
    @param _addr The address to set the whitelist status for
    @param _shouldWhitelist True to whitelist, False to unwhitelist
    @return True if the whitelist status was successfully updated, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

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
    assert gov._isGovernor(msg.sender) # dev: no perms

    self.shouldEnforceWhitelist = _shouldEnforce
    log ShouldEnforceWhitelistSet(shouldEnforce=_shouldEnforce)
    return True


@external
def setNumUserWalletsAllowed(_numAllowed: uint256 = max_value(uint256)) -> bool:
    """
    @notice Set the maximum number of user wallets allowed
    @dev Only callable by the governor, updates the maximum number of user wallets
    @param _numAllowed The new maximum number of user wallets allowed
    @return True if the maximum number was successfully updated, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

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
    assert gov._isGovernor(msg.sender) # dev: no perms

    self.numAgentsAllowed = _numAllowed
    log NumAgentsAllowedSet(numAllowed=_numAllowed)
    return True


###################
# Agent Blacklist #
###################


@external
def setAgentBlacklist(_agentAddr: address, _shouldBlacklist: bool) -> bool:
    """
    @notice Set the blacklist status for a given agent address
    @dev Only callable by the governor, updates the blacklist state
    @param _agentAddr The address to set the blacklist status for
    @param _shouldBlacklist True to blacklist, False to unblacklist
    @return True if the blacklist status was successfully updated, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    self.agentBlacklist[_agentAddr] = _shouldBlacklist
    log AgentBlacklistSet(agentAddr=_agentAddr, shouldBlacklist=_shouldBlacklist)
    return True


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    """
    @notice Recover funds from the factory
    @dev Only callable by the governor, transfers funds to the recipient
    @param _asset The address of the asset to recover
    @param _recipient The address to send the funds to
    @return True if the funds were successfully recovered, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log AgentFactoryFundsRecovered(asset=_asset, recipient=_recipient, balance=balance)
    return True


@external
def recoverTrialFunds(_wallet: address, _opportunities: DynArray[TrialFundsOpp, MAX_LEGOS] = []) -> bool:
    """
    @notice Recover trial funds from a wallet
    @dev Only callable by the governor, transfers funds back here
    @param _wallet The address of the wallet to recover funds from
    @param _opportunities The list of opportunities to recover funds for
    @return True if the funds were successfully recovered, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    return extcall MainWallet(_wallet).recoverTrialFunds(_opportunities)


@external
def recoverTrialFundsMany(_recoveries: DynArray[TrialFundsRecovery, MAX_RECOVERIES]) -> bool:
    """
    @notice Recover trial funds from a list of wallets
    @dev Only callable by the governor, transfers funds back here
    @param _recoveries The list of wallets and opportunities to recover funds for
    @return True if the funds were successfully recovered, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    for r: TrialFundsRecovery in _recoveries:
        assert extcall MainWallet(r.wallet).recoverTrialFunds(r.opportunities) # dev: recovery failed
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
    assert gov._isGovernor(msg.sender) # dev: no perms

    self.isActivated = _shouldActivate
    log AgentFactoryActivated(isActivated=_shouldActivate)
