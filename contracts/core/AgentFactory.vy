# @version 0.4.0

initializes: gov
exports: gov.__interface__
import contracts.modules.Governable as gov
from ethereum.ercs import IERC20

interface MainWallet:
    def initialize(_walletConfig: address, _addyRegistry: address, _wethAddr: address, _trialFundsAsset: address, _trialFundsInitialAmount: uint256) -> bool: nonpayable
    def recoverTrialFunds(_opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]) -> bool: nonpayable

interface WalletConfig:
    def initialize(_wallet: address, _addyRegistry: address, _owner: address, _initialAgent: address) -> bool: nonpayable

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

event AgenticWalletCreated:
    mainAddr: indexed(address)
    configAddr: indexed(address)
    owner: indexed(address)
    agent: address
    creator: address

event MainWalletTemplateSet:
    template: indexed(address)
    version: uint256

event WalletConfigTemplateSet:
    template: indexed(address)
    version: uint256

event TrialFundsDataSet:
    asset: indexed(address)
    amount: uint256

event WhitelistSet:
    addr: address
    shouldWhitelist: bool

event NumAgenticWalletsAllowedSet:
    numAllowed: uint256

event ShouldEnforceWhitelistSet:
    shouldEnforce: bool

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AgentFactoryActivated:
    isActivated: bool

# template info
mainWalletTemplateInfo: public(TemplateInfo)
walletConfigTemplateInfo: public(TemplateInfo)
trialFundsData: public(TrialFundsData)

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

MAX_LEGOS: constant(uint256) = 20


@deploy
def __init__(_addyRegistry: address, _wethAddr: address, _mainWalletTemplate: address, _walletConfigTemplate: address):
    assert empty(address) not in [_addyRegistry, _wethAddr] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry
    WETH_ADDR = _wethAddr
    gov.__init__(_addyRegistry)
    self.isActivated = True

    # set agent template
    if self._isValidMainWalletTemplate(_mainWalletTemplate) and self._isValidWalletConfigTemplate(_walletConfigTemplate):
        self._setMainWalletTemplate(_mainWalletTemplate)
        self._setWalletConfigTemplate(_walletConfigTemplate)


@view
@external
def currentMainWalletTemplate() -> address:
    """
    @notice Get the current wallet template address being used by the factory
    @dev This is a simple getter for the current template address stored in mainWalletTemplateInfo
    @return The address of the current wallet template
    """
    return self.mainWalletTemplateInfo.addr


@view
@external
def currentWalletConfigTemplate() -> address:
    """
    @notice Get the current wallet config template address being used by the factory
    @dev This is a simple getter for the current template address stored in walletConfigTemplateInfo
    @return The address of the current wallet config template
    """
    return self.walletConfigTemplateInfo.addr


#########################
# Create Agentic Wallet #
#########################


@view
@external 
def isValidWalletSetup(_owner: address, _agent: address) -> bool:
    """
    @notice Check if the provided owner and agent addresses form a valid wallet setup
    @dev Validates that both templates exist and owner/agent combination is valid
    @param _owner The address that will own the wallet
    @param _agent The address that will be the agent (can be empty)
    @return True if the setup is valid, False otherwise
    """
    return self._isValidWalletSetup(self.mainWalletTemplateInfo.addr, self.walletConfigTemplateInfo.addr, _owner, _agent)


@view
@internal 
def _isValidWalletSetup(_mainTemplate: address, _configTemplate: address, _owner: address, _agent: address) -> bool:
    if _mainTemplate == empty(address) or _configTemplate == empty(address):
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

    mainWalletTemplate: address = self.mainWalletTemplateInfo.addr
    walletConfigTemplate: address = self.walletConfigTemplateInfo.addr
    if not self._isValidWalletSetup(mainWalletTemplate, walletConfigTemplate, _owner, _agent):
        return empty(address)

    # check limits
    if self.shouldEnforceWhitelist and not self.whitelist[msg.sender]:
        return empty(address)
    if self.numAgenticWallets >= self.numAgenticWalletsAllowed:
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
    self.isAgenticWallet[mainWalletAddr] = True
    self.numAgenticWallets += 1

    log AgenticWalletCreated(mainWalletAddr, walletConfigAddr, _owner, _agent, msg.sender)
    return mainWalletAddr


############################
# Set Main Wallet Template #
############################


@view
@external 
def isValidMainWalletTemplate(_newAddr: address) -> bool:
    """
    @notice Check if a given address is valid to be used as a new main wallet template
    @dev Validates the address is a contract and different from current template
    @param _newAddr The address to validate as a potential new template
    @return True if the address can be used as a template, False otherwise
    """
    return self._isValidMainWalletTemplate(_newAddr)


@view
@internal 
def _isValidMainWalletTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.mainWalletTemplateInfo.addr


@external
def setMainWalletTemplate(_addr: address) -> bool:
    """
    @notice Set a new main wallet template address for future wallet deployments
    @dev Only callable by the governor, updates template info and emits event
    @param _addr The address of the new template to use
    @return True if template was successfully updated, False if invalid address
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidMainWalletTemplate(_addr):
        return False
    return self._setMainWalletTemplate(_addr)


@internal
def _setMainWalletTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.mainWalletTemplateInfo
    newData: TemplateInfo = TemplateInfo(
        addr=_addr,
        version=prevData.version + 1,
        lastModified=block.timestamp,
    )
    self.mainWalletTemplateInfo = newData
    log MainWalletTemplateSet(_addr, newData.version)
    return True


##############################
# Set Wallet Config Template #
##############################


@view
@external 
def isValidWalletConfigTemplate(_newAddr: address) -> bool:
    """
    @notice Check if a given address is valid to be used as a new wallet config template
    @dev Validates the address is a contract and different from current template
    @param _newAddr The address to validate as a potential new template
    @return True if the address can be used as a template, False otherwise
    """
    return self._isValidWalletConfigTemplate(_newAddr)


@view
@internal 
def _isValidWalletConfigTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.walletConfigTemplateInfo.addr


@external
def setWalletConfigTemplate(_addr: address) -> bool:
    """
    @notice Set a new wallet config template address for future wallet deployments
    @dev Only callable by the governor, updates template info and emits event
    @param _addr The address of the new template to use
    @return True if template was successfully updated, False if invalid address
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidWalletConfigTemplate(_addr):
        return False
    return self._setWalletConfigTemplate(_addr)


@internal
def _setWalletConfigTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.walletConfigTemplateInfo
    newData: TemplateInfo = TemplateInfo(
        addr=_addr,
        version=prevData.version + 1,
        lastModified=block.timestamp,
    )
    self.walletConfigTemplateInfo = newData
    log WalletConfigTemplateSet(_addr, newData.version)
    return True


###############
# Trial Funds #
###############


@view
@external 
def isValidTrialFundsData(_asset: address, _amount: uint256) -> bool:
    return self._isValidTrialFundsData(_asset, _amount)


@view
@internal 
def _isValidTrialFundsData(_asset: address, _amount: uint256) -> bool:
    if not _asset.is_contract or _asset == empty(address):
        return False
    return _amount != 0


@external
def setTrialFundsData(_asset: address, _amount: uint256) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidTrialFundsData(_asset, _amount):
        return False

    self.trialFundsData = TrialFundsData(
        asset=_asset,
        amount=_amount,
    )
    log TrialFundsDataSet(_asset, _amount)
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
    assert gov._isGovernor(msg.sender) # dev: no perms

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
    assert gov._isGovernor(msg.sender) # dev: no perms

    self.shouldEnforceWhitelist = _shouldEnforce
    log ShouldEnforceWhitelistSet(_shouldEnforce)
    return True


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log FundsRecovered(_asset, _recipient, balance)
    return True


@external
def recoverTrialFunds(_wallet: address, _opportunities: DynArray[TrialFundsOpp, MAX_LEGOS] = []) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms
    return extcall MainWallet(_wallet).recoverTrialFunds(_opportunities)


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
    log AgentFactoryActivated(_shouldActivate)
