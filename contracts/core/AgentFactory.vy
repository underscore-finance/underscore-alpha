# @version 0.4.0

interface AgenticWallet:
    def initialize(_AddyRegistry: address, _wethAddr: address, _owner: address, _agent: address) -> bool: nonpayable

interface AddyRegistry:
    def governor() -> address: view

struct TemplateInfo:
    addr: address
    version: uint256
    lastModified: uint256

event AgenticWalletCreated:
    addr: indexed(address)
    owner: indexed(address)
    agent: indexed(address)
    creator: address

event AgentTemplateSet:
    template: indexed(address)
    version: uint256

event WhitelistSet:
    addr: address
    shouldWhitelist: bool

event NumAgenticWalletsAllowedSet:
    numAllowed: uint256

event ShouldEnforceWhitelistSet:
    shouldEnforce: bool

event AgentFactoryActivated:
    isActivated: bool

# template info
agentTemplateInfo: public(TemplateInfo)

# agentic wallets
isAgenticWallet: public(HashMap[address, bool])
numAgenticWallets: public(uint256)

# limits
shouldEnforceWhitelist: public(bool)
whitelist: public(HashMap[address, bool])
numAgenticWalletsAllowed: public(uint256)

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))
WETH_ADDR: public(immutable(address))


@deploy
def __init__(_addyRegistry: address, _wethAddr: address, _walletTemplate: address):
    assert empty(address) not in [_addyRegistry, _wethAddr] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry
    WETH_ADDR = _wethAddr

    self.isActivated = True

    # set agent template
    if self._isValidWalletTemplate(_walletTemplate):
        self._setAgenticWalletTemplate(_walletTemplate)


@view
@external
def currentAgentTemplate() -> address:
    """
    @notice Get the current wallet template address being used by the factory
    @dev This is a simple getter for the current template address stored in agentTemplateInfo
    @return The address of the current wallet template
    """
    return self.agentTemplateInfo.addr


#########################
# Create Agentic Wallet #
#########################


@view
@external 
def isValidWalletSetup(_owner: address, _agent: address) -> bool:
    """
    @notice Check if the provided owner and agent addresses form a valid wallet setup
    @dev Validates that the template exists and owner/agent combination is valid
    @param _owner The address that will own the wallet
    @param _agent The address that will be the agent (can be empty)
    @return True if the setup is valid, False otherwise
    """
    return self._isValidWalletSetup(self.agentTemplateInfo.addr, _owner, _agent)


@view
@internal 
def _isValidWalletSetup(_template: address, _owner: address, _agent: address) -> bool:
    if _template == empty(address):
        return False
    return _owner != empty(address) and _owner != _agent


@external
def createAgenticWallet(_owner: address = msg.sender, _agent: address = empty(address)) -> address:
    """
    @notice Create a new Agentic Wallet with specified owner and optional agent
    @dev Creates a minimal proxy of the current template and initializes it
    @param _owner The address that will own the wallet (defaults to msg.sender)
    @param _agent The address that will be the agent (defaults to empty address, can add this later)
    @return The address of the newly created wallet, or empty address if setup is invalid
    """
    assert self.isActivated # dev: not activated

    agentTemplate: address = self.agentTemplateInfo.addr
    if not self._isValidWalletSetup(agentTemplate, _owner, _agent):
        return empty(address)

    # check limits
    if self.shouldEnforceWhitelist and not self.whitelist[msg.sender]:
        return empty(address)
    if self.numAgenticWallets >= self.numAgenticWalletsAllowed:
        return empty(address)

    # create agentic wallet
    newAgentAddr: address = create_minimal_proxy_to(agentTemplate)
    assert extcall AgenticWallet(newAgentAddr).initialize(ADDY_REGISTRY, WETH_ADDR, _owner, _agent)
    
    self.isAgenticWallet[newAgentAddr] = True
    self.numAgenticWallets += 1

    log AgenticWalletCreated(newAgentAddr, _owner, _agent, msg.sender)
    return newAgentAddr


#######################
# Set Wallet Template #
#######################


@view
@external 
def isValidWalletTemplate(_newAddr: address) -> bool:
    """
    @notice Check if a given address is valid to be used as a new wallet template
    @dev Validates the address is a contract and different from current template
    @param _newAddr The address to validate as a potential new template
    @return True if the address can be used as a template, False otherwise
    """
    return self._isValidWalletTemplate(_newAddr)


@view
@internal 
def _isValidWalletTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.agentTemplateInfo.addr


@external
def setAgenticWalletTemplate(_addr: address) -> bool:
    """
    @notice Set a new wallet template address for future wallet deployments
    @dev Only callable by the governor, updates template info and emits event
    @param _addr The address of the new template to use
    @return True if template was successfully updated, False if invalid address
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    if not self._isValidWalletTemplate(_addr):
        return False
    return self._setAgenticWalletTemplate(_addr)


@internal
def _setAgenticWalletTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.agentTemplateInfo
    newData: TemplateInfo = TemplateInfo(
        addr=_addr,
        version=prevData.version + 1,
        lastModified=block.timestamp,
    )
    self.agentTemplateInfo = newData
    log AgentTemplateSet(_addr, newData.version)
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
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.whitelist[_addr] = _shouldWhitelist
    log WhitelistSet(_addr, _shouldWhitelist)
    return True


@external
def setNumAgenticWalletsAllowed(_numAllowed: uint256 = max_value(uint256)) -> bool:
    """
    @notice Set the maximum number of agentic wallets allowed
    @dev Only callable by the governor, updates the maximum number of wallets
    @param _numAllowed The new maximum number of wallets allowed
    @return True if the maximum number was successfully updated, False otherwise
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.numAgenticWalletsAllowed = _numAllowed
    log NumAgenticWalletsAllowedSet(_numAllowed)
    return True


@external
def setShouldEnforceWhitelist(_shouldEnforce: bool) -> bool:
    """
    @notice Set whether to enforce the whitelist for wallet creation
    @dev Only callable by the governor, updates the whitelist enforcement state
    @param _shouldEnforce True to enforce whitelist, False to disable
    @return True if the whitelist enforcement state was successfully updated, False otherwise
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.shouldEnforceWhitelist = _shouldEnforce
    log ShouldEnforceWhitelistSet(_shouldEnforce)
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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AgentFactoryActivated(_shouldActivate)
