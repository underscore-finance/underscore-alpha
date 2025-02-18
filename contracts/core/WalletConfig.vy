# @version 0.4.0
# pragma optimize codesize

from ethereum.ercs import IERC20

interface PriceSheets:
    def getCombinedSubData(_agent: address, _agentPaidThru: uint256, _protocolPaidThru: uint256, _oracleRegistry: address) -> (SubPaymentInfo, SubPaymentInfo): view
    def getCombinedTxCostData(_agent: address, _action: ActionType, _usdValue: uint256, _oracleRegistry: address) -> (TxCostInfo, TxCostInfo): view
    def getAgentSubPriceData(_agent: address) -> SubscriptionInfo: view
    def protocolSubPriceData() -> SubscriptionInfo: view

interface LegoRegistry:
    def getUnderlyingForUser(_user: address, _asset: address) -> uint256: view
    def isValidLegoId(_legoId: uint256) -> bool: view

interface WethContract:
    def withdraw(_amount: uint256): nonpayable
    def deposit(): payable

interface WalletFunds:
    def trialFundsInitialAmount() -> uint256: view
    def trialFundsAsset() -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP
    CONVERSION

struct AgentInfo:
    isActive: bool
    installBlock: uint256
    paidThroughBlock: uint256
    allowedAssets: DynArray[address, MAX_ASSETS]
    allowedLegoIds: DynArray[uint256, MAX_LEGOS]
    allowedActions: AllowedActions

struct CoreData:
    owner: address
    wallet: address
    walletConfig: address
    legoRegistry: address
    priceSheets: address
    oracleRegistry: address
    trialFundsAsset: address
    trialFundsInitialAmount: uint256

struct SubPaymentInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    didChange: bool

struct TxCostInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256

struct ProtocolSub:
    installBlock: uint256
    paidThroughBlock: uint256

struct AllowedActions:
    isSet: bool
    canDeposit: bool
    canWithdraw: bool
    canRebalance: bool
    canTransfer: bool
    canSwap: bool
    canConvert: bool

struct ReserveAsset:
    asset: address
    amount: uint256

struct SubscriptionInfo:
    asset: address
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256

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

event AllowedActionsModified:
    agent: indexed(address)
    canDeposit: bool
    canWithdraw: bool
    canRebalance: bool
    canTransfer: bool
    canSwap: bool
    canConvert: bool

event WhitelistAddrSet:
    addr: indexed(address)
    isAllowed: bool

event ReserveAssetSet:
    asset: indexed(address)
    amount: uint256

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

# core
wallet: public(address)

# user settings
owner: public(address) # owner of the wallet
protocolSub: public(ProtocolSub) # subscription info
reserveAssets: public(HashMap[address, uint256]) # asset -> reserve amount
agentSettings: public(HashMap[address, AgentInfo]) # agent -> agent info
isRecipientAllowed: public(HashMap[address, bool]) # recipient -> is allowed

# config
addyRegistry: public(address)
initialized: public(bool)

API_VERSION: constant(String[28]) = "0.0.1"

MAX_ASSETS: constant(uint256) = 25
MAX_LEGOS: constant(uint256) = 20

# registry ids
LEGO_REGISTRY_ID: constant(uint256) = 2
PRICE_SHEETS_ID: constant(uint256) = 3
ORACLE_REGISTRY_ID: constant(uint256) = 4


@deploy
def __init__():
    # make sure original reference contract can't be initialized
    self.initialized = True


@external
def initialize(
    _wallet: address,
    _addyRegistry: address,
    _owner: address,
    _initialAgent: address,
) -> bool:
    """
    @notice Sets up the initial state of the wallet template
    @dev Can only be called once and sets core contract parameters
    @param _wallet The address of the wallet contract
    @param _addyRegistry The address of the core registry contract
    @param _owner The address that will own this wallet
    @param _initialAgent The address of the initial AI agent (if any)
    @return bool True if initialization was successful
    """
    assert not self.initialized # dev: can only initialize once
    self.initialized = True

    assert empty(address) not in [_wallet, _addyRegistry, _owner] # dev: invalid addrs
    assert _initialAgent != _owner # dev: agent cannot be owner
    self.wallet = _wallet
    self.addyRegistry = _addyRegistry
    self.owner = _owner

    priceSheets: address = staticcall AddyRegistry(_addyRegistry).getAddy(PRICE_SHEETS_ID)

    # initial agent setup
    if _initialAgent != empty(address):
        subInfo: SubscriptionInfo = staticcall PriceSheets(priceSheets).getAgentSubPriceData(_initialAgent)
        paidThroughBlock: uint256 = 0
        if subInfo.usdValue != 0:
            paidThroughBlock = block.number + subInfo.trialPeriod
        self.agentSettings[_initialAgent] = AgentInfo(
            isActive=True,
            installBlock=block.number,
            paidThroughBlock=paidThroughBlock,
            allowedAssets=[],
            allowedLegoIds=[],
            allowedActions=empty(AllowedActions),
        )
        log AgentAdded(_initialAgent, 0, 0)

    # protocol subscription
    protocolSub: ProtocolSub = empty(ProtocolSub)
    protocolSub.installBlock = block.number
    subInfo: SubscriptionInfo = staticcall PriceSheets(priceSheets).protocolSubPriceData()
    if subInfo.usdValue != 0:
        protocolSub.paidThroughBlock = block.number + subInfo.trialPeriod
    self.protocolSub = protocolSub

    return True


@pure
@external
def apiVersion() -> String[28]:
    """
    @notice Returns the current API version of the contract
    @dev Returns a constant string representing the contract version
    @return String[28] The API version string
    """
    return API_VERSION


#####################
# Agent Permissions #
#####################


@view
@external
def canAgentAccess(
    _agent: address,
    _action: ActionType,
    _assets: DynArray[address, MAX_ASSETS],
    _legoIds: DynArray[uint256, MAX_LEGOS],
) -> bool:
    return self._canAgentAccess(self.agentSettings[_agent], _action, _assets, _legoIds)


@view
@internal
def _canAgentAccess(
    _agent: AgentInfo,
    _action: ActionType,
    _assets: DynArray[address, MAX_ASSETS],
    _legoIds: DynArray[uint256, MAX_LEGOS],
) -> bool:
    if not _agent.isActive:
        return False

    # check allowed actions
    if not self._canAgentPerformAction(_action, _agent.allowedActions):
        return False

    # check allowed assets
    if len(_agent.allowedAssets) != 0:
        for i: uint256 in range(len(_assets), bound=MAX_ASSETS):
            asset: address = _assets[i]
            if asset != empty(address) and asset not in _agent.allowedAssets:
                return False

    # check allowed lego ids
    if len(_agent.allowedLegoIds) != 0:
        for i: uint256 in range(len(_legoIds), bound=MAX_LEGOS):
            legoId: uint256 = _legoIds[i]
            if legoId != 0 and legoId not in _agent.allowedLegoIds:
                return False

    return True


@view
@internal
def _canAgentPerformAction(_action: ActionType, _allowedActions: AllowedActions) -> bool:
    if not _allowedActions.isSet:
        return True
    if _action == ActionType.DEPOSIT:
        return _allowedActions.canDeposit
    elif _action == ActionType.WITHDRAWAL:
        return _allowedActions.canWithdraw
    elif _action == ActionType.REBALANCE:
        return _allowedActions.canRebalance
    elif _action == ActionType.TRANSFER:
        return _allowedActions.canTransfer
    elif _action == ActionType.SWAP:
        return _allowedActions.canSwap
    elif _action == ActionType.CONVERSION:
        return _allowedActions.canConvert
    else:
        return True # no action specified


@view
@external
def isAgentActive(_agent: address) -> bool:
    return self.agentSettings[_agent].isActive


##########################
# Subscription + Tx Fees #
##########################


# subscriptions


@view
@external
def getAgentSubscriptionStatus(_agent: address) -> SubPaymentInfo:
    cd: CoreData = self._getCoreData()
    na: SubPaymentInfo = empty(SubPaymentInfo)
    agentSub: SubPaymentInfo = empty(SubPaymentInfo)
    na, agentSub = staticcall PriceSheets(cd.priceSheets).getCombinedSubData(_agent, self.agentSettings[_agent].paidThroughBlock, 0, cd.oracleRegistry)
    return agentSub


@view
@external
def getProtocolSubscriptionStatus() -> SubPaymentInfo:
    cd: CoreData = self._getCoreData()
    protocolSub: SubPaymentInfo = empty(SubPaymentInfo)
    na: SubPaymentInfo = empty(SubPaymentInfo)
    protocolSub, na = staticcall PriceSheets(cd.priceSheets).getCombinedSubData(empty(address), 0, self.protocolSub.paidThroughBlock, cd.oracleRegistry)
    return protocolSub


@view
@external
def canMakeSubscriptionPayments(_agent: address) -> (bool, bool):
    cd: CoreData = self._getCoreData()
    protocolSub: SubPaymentInfo = empty(SubPaymentInfo)
    agentSub: SubPaymentInfo = empty(SubPaymentInfo)
    protocolSub, agentSub = staticcall PriceSheets(cd.priceSheets).getCombinedSubData(_agent, self.agentSettings[_agent].paidThroughBlock, self.protocolSub.paidThroughBlock, cd.oracleRegistry)
    return self._checkIfSufficientFunds(protocolSub.asset, protocolSub.amount, agentSub.asset, agentSub.amount, cd)


@external
def handleSubscriptionsAndPermissions(
    _agent: address,
    _action: ActionType,
    _assets: DynArray[address, MAX_ASSETS],
    _legoIds: DynArray[uint256, MAX_LEGOS],
    _cd: CoreData,
) -> (SubPaymentInfo, SubPaymentInfo):
    """
    @notice Handles the subscription and permission data for the given agent and action
    @param _agent The address of the agent
    @param _action The action to handle
    @param _assets The assets to check
    @param _legoIds The legos to check
    @param _cd The core data
    @return protocolSub The protocol subscription data
    @return agentSub The agent subscription data
    """
    assert msg.sender == self.wallet # dev: no perms

    # check if agent can perform action with assets and legos
    userAgentData: AgentInfo = empty(AgentInfo)
    if _agent != empty(address):
        userAgentData = self.agentSettings[_agent]
        assert self._canAgentAccess(userAgentData, _action, _assets, _legoIds) # dev: agent not allowed

    userProtocolData: ProtocolSub = self.protocolSub

    # get latest sub data for agent and protocol
    protocolSub: SubPaymentInfo = empty(SubPaymentInfo)
    agentSub: SubPaymentInfo = empty(SubPaymentInfo)
    protocolSub, agentSub = staticcall PriceSheets(_cd.priceSheets).getCombinedSubData(_agent, userAgentData.paidThroughBlock, userProtocolData.paidThroughBlock, _cd.oracleRegistry)

    # check if sufficient funds
    canPayProtocol: bool = False
    canPayAgent: bool = False
    canPayProtocol, canPayAgent = self._checkIfSufficientFunds(protocolSub.asset, protocolSub.amount, agentSub.asset, agentSub.amount, _cd)
    assert canPayProtocol # dev: insufficient balance for protocol subscription payment
    assert canPayAgent # dev: insufficient balance for agent subscription payment

    # update and save new data
    if protocolSub.didChange:
        userProtocolData.paidThroughBlock = protocolSub.paidThroughBlock
        self.protocolSub = userProtocolData
    if agentSub.didChange:
        userAgentData.paidThroughBlock = agentSub.paidThroughBlock
        self.agentSettings[_agent] = userAgentData

    # actual payments will happen from wallet
    return protocolSub, agentSub


# transaction fees


@view
@external
def getTransactionCosts(_agent: address, _action: ActionType, _usdValue: uint256, _cd: CoreData) -> (TxCostInfo, TxCostInfo):
    """
    @notice Returns the transaction costs for the given agent and action
    @param _agent The address of the agent
    @param _action The action to check
    @param _usdValue The USD value of the transaction
    @param _cd The core data
    @return protocolCost The transaction cost for the protocol
    @return agentCost The transaction cost for the agent
    """
    protocolCost: TxCostInfo = empty(TxCostInfo)
    agentCost: TxCostInfo = empty(TxCostInfo)
    protocolCost, agentCost = staticcall PriceSheets(_cd.priceSheets).getCombinedTxCostData(_agent, _action, _usdValue, _cd.oracleRegistry)

    # check if sufficient funds
    canPayProtocol: bool = False
    canPayAgent: bool = False
    canPayProtocol, canPayAgent = self._checkIfSufficientFunds(protocolCost.asset, protocolCost.amount, agentCost.asset, agentCost.amount, _cd)
    assert canPayProtocol # dev: insufficient balance for protocol tx fee
    assert canPayAgent # dev: insufficient balance for agent tx fee

    # actual payments will happen from wallet
    return protocolCost, agentCost


@view
@external
def canPayTransactionFees(_agent: address, _action: ActionType, _usdValue: uint256) -> (bool, bool):
    cd: CoreData = self._getCoreData()
    protocolCost: TxCostInfo = empty(TxCostInfo)
    agentCost: TxCostInfo = empty(TxCostInfo)
    protocolCost, agentCost = staticcall PriceSheets(cd.priceSheets).getCombinedTxCostData(_agent, _action, _usdValue, cd.oracleRegistry)
    return self._checkIfSufficientFunds(protocolCost.asset, protocolCost.amount, agentCost.asset, agentCost.amount, cd)


@view
@external
def aggregateBatchTxCostData(
    _aggProtocolCost: TxCostInfo,
    _aggAgentCost: TxCostInfo,
    _agent: address,
    _action: ActionType,
    _usdValue: uint256,
    _priceSheets: address,
    _oracleRegistry: address,
) -> (TxCostInfo, TxCostInfo):
    aggProtocolCost: TxCostInfo = _aggProtocolCost
    aggAgentCost: TxCostInfo = _aggAgentCost

    # new transaction cost data
    newProtocolCost: TxCostInfo = empty(TxCostInfo)
    newAgentCost: TxCostInfo = empty(TxCostInfo)
    newProtocolCost, newAgentCost = staticcall PriceSheets(_priceSheets).getCombinedTxCostData(_agent, _action, _usdValue, _oracleRegistry)

    # protocol cost
    aggProtocolCost.amount += newProtocolCost.amount
    aggProtocolCost.usdValue += newProtocolCost.usdValue
    if aggProtocolCost.asset == empty(address) and newProtocolCost.asset != empty(address):
        aggProtocolCost.asset = newProtocolCost.asset
    if aggProtocolCost.recipient == empty(address) and newProtocolCost.recipient != empty(address):
        aggProtocolCost.recipient = newProtocolCost.recipient

    # agent cost
    aggAgentCost.amount += newAgentCost.amount
    aggAgentCost.usdValue += newAgentCost.usdValue
    if aggAgentCost.asset == empty(address) and newAgentCost.asset != empty(address):
        aggAgentCost.asset = newAgentCost.asset
    if aggAgentCost.recipient == empty(address) and newAgentCost.recipient != empty(address):
        aggAgentCost.recipient = newAgentCost.recipient

    return aggProtocolCost, aggAgentCost


####################
# Random Utilities #
####################


@view
@internal
def _getCoreData() -> CoreData:
    addyRegistry: address = self.addyRegistry
    wallet: address = self.wallet
    return CoreData(
        owner=self.owner,
        wallet=wallet,
        walletConfig=self,
        legoRegistry=staticcall AddyRegistry(addyRegistry).getAddy(LEGO_REGISTRY_ID),
        priceSheets=staticcall AddyRegistry(addyRegistry).getAddy(PRICE_SHEETS_ID),
        oracleRegistry=staticcall AddyRegistry(addyRegistry).getAddy(ORACLE_REGISTRY_ID),
        trialFundsAsset=staticcall WalletFunds(wallet).trialFundsAsset(),
        trialFundsInitialAmount=staticcall WalletFunds(wallet).trialFundsInitialAmount(),
    )


@view
@internal
def _checkIfSufficientFunds(_protocolAsset: address, _protocolAmount: uint256, _agentAsset: address, _agentAmount: uint256, _cd: CoreData) -> (bool, bool):
    canPayProtocol: bool = True
    canPayAgent: bool = True

    # check if any of these assets are also trial funds asset
    trialFundsCurrentBal: uint256 = 0
    trialFundsDeployed: uint256 = 0
    if (_protocolAsset != empty(address) and _protocolAsset == _cd.trialFundsAsset) or (_agentAsset != empty(address) and _agentAsset == _cd.trialFundsAsset):
        trialFundsCurrentBal = staticcall IERC20(_cd.trialFundsAsset).balanceOf(_cd.wallet)
        trialFundsDeployed = staticcall LegoRegistry(_cd.legoRegistry).getUnderlyingForUser(_cd.wallet, _cd.trialFundsAsset)

    # check if can make protocol payment
    if _protocolAmount != 0:
        availBalForProtocol: uint256 = self._getAvailBalAfterTrialFunds(_protocolAsset, _cd.wallet, _cd.trialFundsAsset, _cd.trialFundsInitialAmount, trialFundsCurrentBal, trialFundsDeployed)
        canPayProtocol = availBalForProtocol >= _protocolAmount

        # update trial funds balance
        if _protocolAsset != empty(address) and _protocolAsset == _cd.trialFundsAsset:
            trialFundsCurrentBal -= _protocolAmount

    # check if can make agent payment
    if _agentAmount != 0:
        availBalForAgent: uint256 = self._getAvailBalAfterTrialFunds(_agentAsset, _cd.wallet, _cd.trialFundsAsset, _cd.trialFundsInitialAmount, trialFundsCurrentBal, trialFundsDeployed)
        canPayAgent = availBalForAgent >= _agentAmount

    return canPayProtocol, canPayAgent


@view
@external
def getAvailableTxAmount(
    _asset: address,
    _wantedAmount: uint256,
    _shouldCheckTrialFunds: bool,
    _cd: CoreData = empty(CoreData),
) -> uint256:
    """
    @notice Returns the maximum amount that can be sent from the wallet
    @param _asset The address of the asset to check
    @param _wantedAmount The amount of the asset to send
    @param _shouldCheckTrialFunds Whether to check if the asset is a trial funds asset
    @param _cd The core data
    @return amount The maximum amount that can be sent
    """
    if _asset == empty(address):
        return max_value(uint256)

    cd: CoreData = _cd
    if cd.wallet == empty(address):
        cd = self._getCoreData()

    availableAmount: uint256 = staticcall IERC20(_asset).balanceOf(cd.wallet)

    # check if asset is trial funds asset
    if _shouldCheckTrialFunds and _asset == cd.trialFundsAsset:
        trialFundsDeployed: uint256 = staticcall LegoRegistry(cd.legoRegistry).getUnderlyingForUser(cd.wallet, _asset)
        availableAmount = self._getAvailBalAfterTrialFunds(_asset, cd.wallet, cd.trialFundsAsset, cd.trialFundsInitialAmount, availableAmount, trialFundsDeployed)

    # check if any reserve is set
    reservedAmount: uint256 = self.reserveAssets[_asset]
    if reservedAmount != 0:
        assert availableAmount > reservedAmount # dev: insufficient balance after reserve
        availableAmount -= reservedAmount

    # return min of wanted amount and available amount
    availableAmount = min(_wantedAmount, availableAmount)
    assert availableAmount != 0 # dev: no funds available

    return availableAmount


@view
@internal
def _getAvailBalAfterTrialFunds(
    _asset: address,
    _wallet: address,
    _trialFundsAsset: address,
    _trialFundsInitialAmount: uint256,
    _trialFundsCurrentBal: uint256,
    _trialFundsDeployed: uint256,
) -> uint256:
    if _asset != _trialFundsAsset:
        return staticcall IERC20(_asset).balanceOf(_wallet)

    # sufficient trial funds already deployed
    if _trialFundsDeployed >= _trialFundsInitialAmount:
        return _trialFundsCurrentBal

    lockedAmount: uint256 = _trialFundsInitialAmount - _trialFundsDeployed
    availAmount: uint256 = 0
    if _trialFundsCurrentBal > lockedAmount:
        availAmount = _trialFundsCurrentBal - lockedAmount

    return availAmount


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
    _allowedActions: AllowedActions = empty(AllowedActions),
) -> bool:
    """
    @notice Adds a new agent or modifies an existing agent's permissions
        If empty arrays are provided, the agent has access to all assets and lego ids
    @dev Can only be called by the owner
    @param _agent The address of the agent to add or modify
    @param _allowedAssets List of assets the agent can interact with
    @param _allowedLegoIds List of lego IDs the agent can use
    @param _allowedActions The actions the agent can perform
    @return bool True if the agent was successfully added or modified
    """
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms
    assert _agent != owner # dev: agent cannot be owner
    assert _agent != empty(address) # dev: invalid agent

    agentInfo: AgentInfo = self.agentSettings[_agent]
    agentInfo.isActive = True

    # allowed actions
    agentInfo.allowedActions = _allowedActions
    agentInfo.allowedActions.isSet = self._hasAllowedActionsSet(_allowedActions)

    # sanitize other input data
    agentInfo.allowedAssets, agentInfo.allowedLegoIds = self._sanitizeAgentInputData(_allowedAssets, _allowedLegoIds)

    # get subscription info
    priceSheets: address = staticcall AddyRegistry(self.addyRegistry).getAddy(PRICE_SHEETS_ID)
    subInfo: SubscriptionInfo = staticcall PriceSheets(priceSheets).getAgentSubPriceData(_agent)
    
    isNewAgent: bool = (agentInfo.installBlock == 0)
    if isNewAgent:
        agentInfo.installBlock = block.number
        if subInfo.usdValue != 0:
            agentInfo.paidThroughBlock = block.number + subInfo.trialPeriod

    # may not have had sub setup before
    elif subInfo.usdValue != 0:
        agentInfo.paidThroughBlock = max(agentInfo.paidThroughBlock, agentInfo.installBlock + subInfo.trialPeriod)

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
        legoRegistry: address = staticcall AddyRegistry(self.addyRegistry).getAddy(LEGO_REGISTRY_ID)
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
    """
    @notice Disables an existing agent
    @dev Can only be called by the owner
    @param _agent The address of the agent to disable
    @return bool True if the agent was successfully disabled
    """
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active
    agentInfo.isActive = False
    self.agentSettings[_agent] = agentInfo

    log AgentDisabled(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    return True


# add lego id for agent


@nonreentrant
@external
def addLegoIdForAgent(_agent: address, _legoId: uint256) -> bool:
    """
    @notice Adds a lego ID to an agent's allowed legos
    @dev Can only be called by the owner
    @param _agent The address of the agent
    @param _legoId The lego ID to add
    @return bool True if the lego ID was successfully added
    """
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active

    legoRegistry: address = staticcall AddyRegistry(self.addyRegistry).getAddy(LEGO_REGISTRY_ID)
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_legoId)
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
    """
    @notice Adds an asset to an agent's allowed assets
    @dev Can only be called by the owner
    @param _agent The address of the agent
    @param _asset The asset address to add
    @return bool True if the asset was successfully added
    """
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


# modify allowed actions


@nonreentrant
@external
def modifyAllowedActions(_agent: address, _allowedActions: AllowedActions = empty(AllowedActions)) -> bool:
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active

    agentInfo.allowedActions = _allowedActions
    agentInfo.allowedActions.isSet = self._hasAllowedActionsSet(_allowedActions)
    self.agentSettings[_agent] = agentInfo

    log AllowedActionsModified(_agent, _allowedActions.canDeposit, _allowedActions.canWithdraw, _allowedActions.canRebalance, _allowedActions.canTransfer, _allowedActions.canSwap, _allowedActions.canConvert)
    return True


@view
@internal
def _hasAllowedActionsSet(_actions: AllowedActions) -> bool:
    return _actions.canDeposit or _actions.canWithdraw or _actions.canRebalance or _actions.canTransfer or _actions.canSwap or _actions.canConvert


######################
# Transfer Whitelist #
######################


@nonreentrant
@external
def setWhitelistAddr(_addr: address, _isAllowed: bool) -> bool:
    """
    @notice Sets or removes an address from the transfer whitelist
    @dev Can only be called by the owner
    @param _addr The external address to whitelist/blacklist
    @param _isAllowed Whether the address can receive funds
    @return bool True if the whitelist was updated successfully
    """
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms

    assert _addr != empty(address) # dev: invalid addr
    assert _addr != owner # dev: owner cannot be whitelisted
    assert _addr != self # dev: wallet cannot be whitelisted
    assert _isAllowed != self.isRecipientAllowed[_addr] # dev: already set

    self.isRecipientAllowed[_addr] = _isAllowed
    log WhitelistAddrSet(_addr, _isAllowed)
    return True


##################
# Reserve Assets #
##################


@nonreentrant
@external
def setReserveAsset(_asset: address, _amount: uint256) -> bool:
    assert msg.sender == self.owner # dev: no perms
    assert _asset != empty(address) # dev: invalid asset
    self.reserveAssets[_asset] = _amount
    log ReserveAssetSet(_asset, _amount)
    return True


@nonreentrant
@external
def setManyReserveAssets(_assets: DynArray[ReserveAsset, MAX_ASSETS]) -> bool:
    assert msg.sender == self.owner # dev: no perms
    assert len(_assets) != 0 # dev: invalid array length
    for i: uint256 in range(len(_assets), bound=MAX_ASSETS):
        asset: address = _assets[i].asset
        amount: uint256 = _assets[i].amount
        assert asset != empty(address) # dev: invalid asset
        self.reserveAssets[asset] = amount
        log ReserveAssetSet(asset, amount)

    return True


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address) -> bool:
    """
    @notice transfers funds from the config contract to the main wallet
    @dev anyone can call this!
    @param _asset The address of the asset to recover
    @return bool True if the funds were recovered successfully
    """
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    wallet: address = self.wallet
    if empty(address) in [wallet, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(wallet, balance, default_return_value=True) # dev: recovery failed
    log FundsRecovered(_asset, wallet, balance)
    return True