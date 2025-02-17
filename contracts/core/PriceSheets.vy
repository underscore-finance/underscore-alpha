# @version 0.4.0

initializes: gov
exports: gov.__interface__
import contracts.modules.Governable as gov

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governor() -> address: view

interface OracleRegistry:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view

flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP

struct TxPriceSheet:
    asset: address
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256

struct SubscriptionInfo:
    asset: address
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256

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

struct PendingTxPriceSheet:
    priceSheet: TxPriceSheet
    effectiveBlock: uint256

struct PendingSubPrice:
    subInfo: SubscriptionInfo
    effectiveBlock: uint256

event AgentSubPriceSet:
    agent: indexed(address)
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256

event PendingAgentSubPriceSet:
    agent: indexed(address)
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
    effectiveBlock: uint256

event ProtocolSubPriceSet:
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256

event AgentSubPriceRemoved:
    agent: indexed(address)
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256

event ProtocolSubPriceRemoved:
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256

event AgentSubPricingEnabled:
    isEnabled: bool

event AgentTxPriceSheetSet:
    agent: indexed(address)
    asset: indexed(address)
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256

event PendingAgentTxPriceSheetSet:
    agent: indexed(address)
    asset: indexed(address)
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    effectiveBlock: uint256

event ProtocolTxPriceSheetSet:
    asset: indexed(address)
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256

event AgentTxPriceSheetRemoved:
    agent: indexed(address)
    asset: indexed(address)
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256

event ProtocolTxPriceSheetRemoved:
    asset: indexed(address)
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256

event AgentTxPricingEnabled:
    isEnabled: bool

event ProtocolRecipientSet:
    recipient: indexed(address)

event PriceChangeDelaySet:
    delayBlocks: uint256

event PriceSheetsActivated:
    isActivated: bool

# protocol pricing
protocolRecipient: public(address) # protocol recipient
protocolTxPriceData: public(TxPriceSheet) # protocol transaction pricing
protocolSubPriceData: public(SubscriptionInfo) # protocol subscription pricing

# agent pricing
isAgentTxPricingEnabled: public(bool)
agentTxPriceData: public(HashMap[address, TxPriceSheet]) # agent -> transaction pricing
isAgentSubPricingEnabled: public(bool)
agentSubPriceData: public(HashMap[address, SubscriptionInfo]) # agent -> subscription pricing

# pending price changes
pendingAgentTxPrices: public(HashMap[address, PendingTxPriceSheet])
pendingAgentSubPrices: public(HashMap[address, PendingSubPrice])
priceChangeDelay: public(uint256) # number of blocks that must pass before price changes take effect

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_TX_FEE: constant(uint256) = 10_00 # 10.00%
MIN_TRIAL_PERIOD: constant(uint256) = 43_200 # 1 day on Base (2 seconds per block)
MAX_TRIAL_PERIOD: constant(uint256) = 1_296_000 # 1 month on Base (2 seconds per block)
MIN_PAY_PERIOD: constant(uint256) = 302_400 # 7 days on Base (2 seconds per block)
MAX_PAY_PERIOD: constant(uint256) = 3_900_000 # 3 months on Base (2 seconds per block)
MIN_PRICE_CHANGE_BUFFER: constant(uint256) = 43_200 # 1 day on Base (2 seconds per block)


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    gov.__init__(_addyRegistry)
    ADDY_REGISTRY = _addyRegistry
    self.protocolRecipient = staticcall AddyRegistry(_addyRegistry).governor()
    self.isActivated = True


######################
# Subscription Utils #
######################


@view
@external
def getCombinedSubData(_agent: address, _agentPaidThru: uint256, _protocolPaidThru: uint256, _oracleRegistry: address) -> (SubPaymentInfo, SubPaymentInfo):
    """
    @notice Get combined subscription data for an agent and protocol
    @dev Returns a struct containing payment amounts and paid through blocks for both agent and protocol
    @param _agent The address of the agent
    @param _agentPaidThru The paid through block for the agent
    @param _protocolPaidThru The paid through block for the protocol
    @param _oracleRegistry The address of the oracle registry
    @return protocolData struct containing payment amounts and paid through blocks for the protocol
    @return agentData struct containing payment amounts and paid through blocks for the agent
    """
    # protocol sub info
    protocolData: SubPaymentInfo = self._updatePaidThroughBlock(_protocolPaidThru, self.protocolSubPriceData, _oracleRegistry)
    if protocolData.amount != 0:
        protocolData.recipient = self.protocolRecipient

    # agent sub info
    agentData: SubPaymentInfo = empty(SubPaymentInfo)
    if _agent != empty(address):
        agentData = self._updatePaidThroughBlock(_agentPaidThru, self.agentSubPriceData[_agent], _oracleRegistry)
        agentData.recipient = _agent

    return protocolData, agentData


@view
@internal
def _updatePaidThroughBlock(_paidThroughBlock: uint256, _subData: SubscriptionInfo, _oracleRegistry: address) -> SubPaymentInfo:
    data: SubPaymentInfo = empty(SubPaymentInfo)

    # subscription was added (since last checked)
    if _paidThroughBlock == 0 and _subData.usdValue != 0:
        data.paidThroughBlock = block.number + _subData.trialPeriod
        data.didChange = True

    # subscription was removed (since last checked)
    elif _paidThroughBlock != 0 and _subData.usdValue == 0:
        data.paidThroughBlock = 0
        data.didChange = True

    # check if subscription needs to be paid
    if data.paidThroughBlock != 0 and block.number > data.paidThroughBlock:
        data.amount = staticcall OracleRegistry(_oracleRegistry).getAssetAmount(_subData.asset, _subData.usdValue)

        # if something fails with price feed, allow transaction through.
        # it's on agent developer to make sure price feed is working, so they can get paid
        if data.amount != 0:
            data.paidThroughBlock = block.number + _subData.payPeriod
            data.usdValue = _subData.usdValue
            data.asset = _subData.asset
            data.didChange = True

    return data


######################
# Agent Subscription #
######################


@view
@external
def getAgentSubPriceData(_agent: address) -> SubscriptionInfo:
    """
    @notice Get the subscription pricing data for a specific agent
    @dev Returns empty SubscriptionInfo if agent subscription pricing is disabled
    @param _agent The address of the agent to query
    @return SubscriptionInfo struct containing subscription details
    """
    if not self.isAgentSubPricingEnabled:
        return empty(SubscriptionInfo)
    return self.agentSubPriceData[_agent]


# set agent sub price


@view
@external
def isValidSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    """
    @notice Check if subscription price parameters are valid
    @dev Validates asset, USD value, trial period, and pay period against constraints
    @param _asset The token address for subscription payments
    @param _usdValue The USD value of the subscription
    @param _trialPeriod The trial period in blocks
    @param _payPeriod The payment period in blocks
    @return bool True if all parameters are valid
    """
    return self._isValidSubPrice(_asset, _usdValue, _trialPeriod, _payPeriod)


@view
@internal
def _isValidSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    if _asset == empty(address):
        return False

    if _payPeriod < MIN_PAY_PERIOD or _payPeriod > MAX_PAY_PERIOD:
        return False

    if _trialPeriod < MIN_TRIAL_PERIOD or _trialPeriod > MAX_TRIAL_PERIOD:
        return False

    return _usdValue != 0


@external
def setAgentSubPrice(_agent: address, _asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    """
    @notice Set subscription pricing for a specific agent
    @dev Creates a pending subscription price change that can be finalized after priceChangeDelay blocks
    @param _agent The address of the agent
    @param _asset The token address for subscription payments
    @param _usdValue The USD value of the subscription
    @param _trialPeriod The trial period in blocks
    @param _payPeriod The payment period in blocks
    @return bool True if pending subscription price was set successfully
    """
    isAgent: bool = msg.sender == _agent
    assert isAgent or gov._isGovernor(msg.sender) # dev: no perms

    if isAgent:
        assert self.isActivated # dev: not active

    # validation
    assert _agent != empty(address) # dev: invalid agent
    if not self._isValidSubPrice(_asset, _usdValue, _trialPeriod, _payPeriod):
        return False

    # create pending subscription price
    subInfo: SubscriptionInfo = SubscriptionInfo(
        asset=_asset,
        usdValue=_usdValue,
        trialPeriod=_trialPeriod,
        payPeriod=_payPeriod,
    )

    # set price change immediately if delay is 0
    priceChangeDelay: uint256 = self.priceChangeDelay
    if priceChangeDelay == 0:
        self._setAgentSubPrice(_agent, subInfo)
        return True

    # set pending price change
    effectiveBlock: uint256 = block.number + priceChangeDelay
    self.pendingAgentSubPrices[_agent] = PendingSubPrice(subInfo=subInfo, effectiveBlock=effectiveBlock)
    log PendingAgentSubPriceSet(_agent, _asset, _usdValue, _trialPeriod, _payPeriod, effectiveBlock)

    return True


# finalize agent sub price


@external
def finalizePendingAgentSubPrice(_agent: address) -> bool:
    """
    @notice Finalize a pending subscription price for an agent
    @dev Can only be called after priceChangeDelay blocks have passed since the pending change was created
    @param _agent The address of the agent
    @return bool True if subscription price was finalized successfully
    """
    assert self.isActivated # dev: not active

    pendingPrice: PendingSubPrice = self.pendingAgentSubPrices[_agent]
    assert pendingPrice.effectiveBlock != 0 and block.number >= pendingPrice.effectiveBlock # dev: time delay not reached
    self.pendingAgentSubPrices[_agent] = empty(PendingSubPrice)

    # apply pending subscription price
    self._setAgentSubPrice(_agent, pendingPrice.subInfo)
    return True


@internal
def _setAgentSubPrice(_agent: address, _subInfo: SubscriptionInfo):
    self.agentSubPriceData[_agent] = _subInfo
    log AgentSubPriceSet(_agent, _subInfo.asset, _subInfo.usdValue, _subInfo.trialPeriod, _subInfo.payPeriod)


# removing agent sub price


@external
def removeAgentSubPrice(_agent: address) -> bool:
    """
    @notice Remove subscription pricing for a specific agent
    @dev Only callable by governor
    @param _agent The address of the agent
    @return bool True if agent subscription price was removed successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    prevInfo: SubscriptionInfo = self.agentSubPriceData[_agent]
    if empty(address) in [prevInfo.asset, _agent]:
        return False

    self.agentSubPriceData[_agent] = empty(SubscriptionInfo)
    log AgentSubPriceRemoved(_agent, prevInfo.asset, prevInfo.usdValue, prevInfo.trialPeriod, prevInfo.payPeriod)
    return True


# enable / disable agent sub pricing


@external
def setAgentSubPricingEnabled(_isEnabled: bool) -> bool:
    """
    @notice Enable or disable agent subscription pricing
    @dev Only callable by governor
    @param _isEnabled True to enable, False to disable
    @return bool True if agent subscription pricing state was changed successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    assert _isEnabled != self.isAgentSubPricingEnabled # dev: no change
    self.isAgentSubPricingEnabled = _isEnabled
    log AgentSubPricingEnabled(_isEnabled)
    return True


#########################
# Protocol Subscription #
#########################


# set protocol sub price


@external
def setProtocolSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    """
    @notice Set subscription pricing for the protocol
    @dev Only callable by governor
    @param _asset The token address for subscription payments
    @param _usdValue The USD value of the subscription
    @param _trialPeriod The trial period in blocks
    @param _payPeriod The payment period in blocks
    @return bool True if protocol subscription price was set successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    # validation
    if not self._isValidSubPrice(_asset, _usdValue, _trialPeriod, _payPeriod):
        return False

    # save data
    self.protocolSubPriceData = SubscriptionInfo(
        asset=_asset,
        usdValue=_usdValue,
        trialPeriod=_trialPeriod,
        payPeriod=_payPeriod,
    )

    log ProtocolSubPriceSet(_asset, _usdValue, _trialPeriod, _payPeriod)
    return True


# removing protocol sub price


@external
def removeProtocolSubPrice() -> bool:
    """
    @notice Remove subscription pricing for the protocol
    @dev Only callable by governor
    @return bool True if protocol subscription price was removed successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    prevInfo: SubscriptionInfo = self.protocolSubPriceData
    if prevInfo.asset == empty(address):
        return False

    self.protocolSubPriceData = empty(SubscriptionInfo)
    log ProtocolSubPriceRemoved(prevInfo.asset, prevInfo.usdValue, prevInfo.trialPeriod, prevInfo.payPeriod)
    return True


#################
# Tx Fees Utils #
#################


@view
@external
def getCombinedTxCostData(_agent: address, _action: ActionType, _usdValue: uint256, _oracleRegistry: address) -> (TxCostInfo, TxCostInfo):
    """
    @notice Get combined transaction cost data for an agent and protocol
    @dev Returns a struct containing cost amounts and recipient addresses for both agent and protocol
    @param _agent The address of the agent
    @param _action The type of action being performed
    @param _usdValue The USD value of the transaction
    @param _oracleRegistry The address of the oracle registry
    @return protocolCost struct containing cost amounts and recipient addresses for the protocol
    @return agentCost struct containing cost amounts and recipient addresses for the agent
    """
    # protocol tx cost info
    protocolCost: TxCostInfo = self._getTransactionFeeData(_action, _usdValue, self.protocolTxPriceData, _oracleRegistry)
    if protocolCost.amount != 0:
        protocolCost.recipient = self.protocolRecipient

    # agent tx cost info
    agentCost: TxCostInfo = empty(TxCostInfo)
    if _agent != empty(address) and self.isAgentTxPricingEnabled:
        agentCost = self._getTransactionFeeData(_action, _usdValue, self.agentTxPriceData[_agent], _oracleRegistry)
        agentCost.recipient = _agent

    return protocolCost, agentCost


@view
@external
def getAgentTransactionFeeData(_agent: address, _action: ActionType, _usdValue: uint256) -> TxCostInfo:
    """
    @notice Get transaction fee data for a specific agent
    @dev Returns empty values if agent transaction pricing is disabled
    @param _agent The address of the agent
    @param _action The type of action being performed
    @param _usdValue The USD value of the transaction
    @return TxCostInfo struct containing cost amounts and recipient addresses for the agent
    """
    if not self.isAgentTxPricingEnabled:
        return empty(TxCostInfo)
    return self._getTransactionFeeData(_action, _usdValue, self.agentTxPriceData[_agent], staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4))


@view
@external
def getProtocolTransactionFeeData(_action: ActionType, _usdValue: uint256) -> TxCostInfo:
    """
    @notice Get transaction fee data for the protocol
    @dev Calculates protocol fees based on action type and transaction value
    @param _action The type of action being performed
    @param _usdValue The USD value of the transaction
    @return TxCostInfo struct containing cost amounts and recipient addresses for the protocol
    """
    return self._getTransactionFeeData(_action, _usdValue, self.protocolTxPriceData, staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4))


@view
@internal
def _getTransactionFeeData(_action: ActionType, _usdValue: uint256, _priceSheet: TxPriceSheet, _oracleRegistry: address) -> TxCostInfo:
    if _usdValue == 0 or _priceSheet.asset == empty(address):
        return empty(TxCostInfo)

    fee: uint256 = self._getTxFeeForAction(_action, _priceSheet)
    if fee == 0:
        return empty(TxCostInfo)

    usdValue: uint256 = _usdValue * fee // HUNDRED_PERCENT
    return TxCostInfo(
        recipient=empty(address),
        asset=_priceSheet.asset,
        amount=staticcall OracleRegistry(_oracleRegistry).getAssetAmount(_priceSheet.asset, usdValue, False),
        usdValue=usdValue,
    )


@view
@internal
def _getTxFeeForAction(_action: ActionType, _prices: TxPriceSheet) -> uint256:
    if _action == ActionType.DEPOSIT:
        return _prices.depositFee
    elif _action == ActionType.WITHDRAWAL:
        return _prices.withdrawalFee
    elif _action == ActionType.REBALANCE:
        return _prices.rebalanceFee
    elif _action == ActionType.TRANSFER:
        return _prices.transferFee
    elif _action == ActionType.SWAP:
        return _prices.swapFee
    else:
        return 0


#################
# Agent Tx Fees #
#################


# set agent tx price sheet


@view
@external
def isValidTxPriceSheet(
    _asset: address,
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
) -> bool:
    """
    @notice Check if transaction price sheet parameters are valid
    @dev Validates asset and fee percentages against constraints
    @param _asset The token address for fee payments
    @param _depositFee The fee percentage for deposits
    @param _withdrawalFee The fee percentage for withdrawals
    @param _rebalanceFee The fee percentage for rebalances
    @param _transferFee The fee percentage for transfers
    @param _swapFee The fee percentage for swaps
    @return bool True if all parameters are valid
    """
    return self._isValidTxPriceSheet(_asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee)


@view
@internal
def _isValidTxPriceSheet(
    _asset: address,
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
) -> bool:
    if _asset == empty(address):
        return False
    return _depositFee <= MAX_TX_FEE and _withdrawalFee <= MAX_TX_FEE and _rebalanceFee <= MAX_TX_FEE and _transferFee <= MAX_TX_FEE and _swapFee <= MAX_TX_FEE


@external
def setAgentTxPriceSheet(
    _agent: address,
    _asset: address,
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
) -> bool:
    """
    @notice Set transaction price sheet for a specific agent
    @dev Creates a pending price change that can be finalized after priceChangeDelay blocks
    @param _agent The address of the agent
    @param _asset The token address for fee payments
    @param _depositFee The fee percentage for deposits
    @param _withdrawalFee The fee percentage for withdrawals
    @param _rebalanceFee The fee percentage for rebalances
    @param _transferFee The fee percentage for transfers
    @param _swapFee The fee percentage for swaps
    @return bool True if pending price sheet was set successfully
    """
    isAgent: bool = msg.sender == _agent
    assert isAgent or gov._isGovernor(msg.sender) # dev: no perms

    if isAgent:
        assert self.isActivated # dev: not active

    # validation
    assert _agent != empty(address) # dev: invalid agent
    if not self._isValidTxPriceSheet(_asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee):
        return False

    # create pending price sheet
    priceSheet: TxPriceSheet = TxPriceSheet(
        asset=_asset,
        depositFee=_depositFee,
        withdrawalFee=_withdrawalFee,
        rebalanceFee=_rebalanceFee,
        transferFee=_transferFee,
        swapFee=_swapFee,
    )

    # set price change immediately if delay is 0
    priceChangeDelay: uint256 = self.priceChangeDelay
    if priceChangeDelay == 0:
        self._setPendingTxPriceSheet(_agent, priceSheet)
        return True

    # set pending price change
    effectiveBlock: uint256 = block.number + priceChangeDelay
    self.pendingAgentTxPrices[_agent] = PendingTxPriceSheet(priceSheet=priceSheet, effectiveBlock=effectiveBlock)
    log PendingAgentTxPriceSheetSet(_agent, _asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee, effectiveBlock)

    return True


# finalize pending tx price sheet


@external
def finalizePendingTxPriceSheet(_agent: address) -> bool:
    """
    @notice Finalize a pending transaction price sheet for an agent
    @dev Can only be called after priceChangeDelay blocks have passed since the pending change was created
    @param _agent The address of the agent
    @return bool True if price sheet was finalized successfully
    """
    assert self.isActivated # dev: not active

    pendingPrice: PendingTxPriceSheet = self.pendingAgentTxPrices[_agent]
    assert pendingPrice.effectiveBlock != 0 and block.number >= pendingPrice.effectiveBlock # dev: time delay not reached
    self.pendingAgentTxPrices[_agent] = empty(PendingTxPriceSheet)

    # apply pending price sheet
    self._setPendingTxPriceSheet(_agent, pendingPrice.priceSheet)
    return True


@internal
def _setPendingTxPriceSheet(_agent: address, _priceSheet: TxPriceSheet):
    self.agentTxPriceData[_agent] = _priceSheet
    log AgentTxPriceSheetSet(_agent, _priceSheet.asset, _priceSheet.depositFee, _priceSheet.withdrawalFee, _priceSheet.rebalanceFee, _priceSheet.transferFee, _priceSheet.swapFee)


# removing tx price sheet


@external
def removeAgentTxPriceSheet(_agent: address) -> bool:
    """
    @notice Remove transaction price sheet for a specific agent
    @dev Only callable by governor
    @param _agent The address of the agent
    @return bool True if agent price sheet was removed successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    prevInfo: TxPriceSheet = self.agentTxPriceData[_agent]
    if empty(address) in [prevInfo.asset, _agent]:
        return False

    self.agentTxPriceData[_agent] = empty(TxPriceSheet)
    log AgentTxPriceSheetRemoved(_agent, prevInfo.asset, prevInfo.depositFee, prevInfo.withdrawalFee, prevInfo.rebalanceFee, prevInfo.transferFee, prevInfo.swapFee)
    return True


# enable / disable agent tx pricing


@external
def setAgentTxPricingEnabled(_isEnabled: bool) -> bool:
    """
    @notice Enable or disable agent transaction pricing
    @dev Only callable by governor
    @param _isEnabled True to enable, False to disable
    @return bool True if agent transaction pricing state was changed successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    assert _isEnabled != self.isAgentTxPricingEnabled # dev: no change
    self.isAgentTxPricingEnabled = _isEnabled
    log AgentTxPricingEnabled(_isEnabled)
    return True


####################
# Protocol Tx Fees #
####################


# set protocol tx price sheet


@external
def setProtocolTxPriceSheet(
    _asset: address,
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
) -> bool:
    """
    @notice Set transaction price sheet for the protocol
    @dev Only callable by governor
    @param _asset The token address for fee payments
    @param _depositFee The fee percentage for deposits
    @param _withdrawalFee The fee percentage for withdrawals
    @param _rebalanceFee The fee percentage for rebalances
    @param _transferFee The fee percentage for transfers
    @param _swapFee The fee percentage for swaps
    @return bool True if protocol price sheet was set successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    # validation
    if not self._isValidTxPriceSheet(_asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee):
        return False

    # save data
    self.protocolTxPriceData = TxPriceSheet(
        asset=_asset,
        depositFee=_depositFee,
        withdrawalFee=_withdrawalFee,
        rebalanceFee=_rebalanceFee,
        transferFee=_transferFee,
        swapFee=_swapFee,
    )

    log ProtocolTxPriceSheetSet(_asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee)
    return True


# remove protocol tx price sheet


@external
def removeProtocolTxPriceSheet() -> bool:
    """
    @notice Remove transaction price sheet for the protocol
    @dev Only callable by governor
    @return bool True if protocol price sheet was removed successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    prevInfo: TxPriceSheet = self.protocolTxPriceData
    if prevInfo.asset == empty(address):
        return False

    self.protocolTxPriceData = empty(TxPriceSheet)
    log ProtocolTxPriceSheetRemoved(prevInfo.asset, prevInfo.depositFee, prevInfo.withdrawalFee, prevInfo.rebalanceFee, prevInfo.transferFee, prevInfo.swapFee)
    return True


######################
# Protocol Recipient #
######################


@external
def setProtocolRecipient(_recipient: address) -> bool:
    """
    @notice Set the recipient address for protocol fees
    @dev Only callable by governor
    @param _recipient The address to receive protocol fees
    @return bool True if protocol recipient was set successfully
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    assert _recipient != empty(address) # dev: invalid recipient
    self.protocolRecipient = _recipient
    log ProtocolRecipientSet(_recipient)
    return True


######################
# Price Change Delay #
######################


@external
def setPriceChangeDelay(_delayBlocks: uint256) -> bool:
    """
    @notice Set the number of blocks required before price changes take effect
    @dev Only callable by governor
    @param _delayBlocks The number of blocks to wait before price changes take effect
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    assert _delayBlocks == 0 or _delayBlocks >= MIN_PRICE_CHANGE_BUFFER # dev: invalid delay
    self.priceChangeDelay = _delayBlocks
    log PriceChangeDelaySet(_delayBlocks)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    """
    @notice Activate or deactivate the price sheets registry
    @dev Only callable by governor. When deactivated, most functions cannot be called.
    @param _shouldActivate True to activate, False to deactivate
    """
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log PriceSheetsActivated(_shouldActivate)
