# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

initializes: gov
exports: gov.__interface__
import contracts.modules.LocalGov as gov

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governance() -> address: view

interface OracleRegistry:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view

interface AgentFactory:
    def isAgent(_agent: address) -> bool: view

interface Agent:
    def owner() -> address: view

flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP
    CONVERSION
    ADD_LIQ
    REMOVE_LIQ
    CLAIM_REWARDS
    BORROW
    REPAY

struct TxPriceSheet:
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    addLiqFee: uint256
    removeLiqFee: uint256
    claimRewardsFee: uint256
    borrowFee: uint256
    repayFee: uint256

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

event ProtocolTxPriceSheetSet:
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    addLiqFee: uint256
    removeLiqFee: uint256
    claimRewardsFee: uint256
    borrowFee: uint256
    repayFee: uint256

event ProtocolTxPriceSheetRemoved:
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    addLiqFee: uint256
    removeLiqFee: uint256
    claimRewardsFee: uint256
    borrowFee: uint256
    repayFee: uint256

event ProtocolRecipientSet:
    recipient: indexed(address)

event PriceChangeDelaySet:
    delayBlocks: uint256

event AmbassadorRatioSet:
    ratio: uint256

event PriceSheetsActivated:
    isActivated: bool

# protocol pricing
protocolRecipient: public(address) # protocol recipient
protocolTxPriceData: public(TxPriceSheet) # protocol transaction pricing
protocolSubPriceData: public(SubscriptionInfo) # protocol subscription pricing

# agent pricing
isAgentSubPricingEnabled: public(bool)
agentSubPriceData: public(HashMap[address, SubscriptionInfo]) # agent -> subscription pricing

# pending price changes
pendingAgentSubPrices: public(HashMap[address, PendingSubPrice])
priceChangeDelay: public(uint256) # number of blocks that must pass before price changes take effect

# ambassador settings
ambassadorRatio: public(uint256) # ratio of ambassador proceeds

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)

# registry ids
AGENT_FACTORY_ID: constant(uint256) = 1

MIN_TRIAL_PERIOD: public(immutable(uint256))
MAX_TRIAL_PERIOD: public(immutable(uint256))
MIN_PAY_PERIOD: public(immutable(uint256))
MAX_PAY_PERIOD: public(immutable(uint256))
MIN_PRICE_CHANGE_BUFFER: public(immutable(uint256))

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_TX_FEE: constant(uint256) = 10_00 # 10.00%


@deploy
def __init__(
    _minTrialPeriod: uint256,
    _maxTrialPeriod: uint256,
    _minPayPeriod: uint256,
    _maxPayPeriod: uint256,
    _minPriceChangeBuffer: uint256,
    _addyRegistry: address,
):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    self.protocolRecipient = staticcall AddyRegistry(_addyRegistry).governance()
    self.isActivated = True
    gov.__init__(empty(address), _addyRegistry, 0, 0)

    ADDY_REGISTRY = _addyRegistry
    MIN_TRIAL_PERIOD = _minTrialPeriod
    MAX_TRIAL_PERIOD = _maxTrialPeriod
    MIN_PAY_PERIOD = _minPayPeriod
    MAX_PAY_PERIOD = _maxPayPeriod
    MIN_PRICE_CHANGE_BUFFER = _minPriceChangeBuffer


@view
@internal
def _isRegisteredAgent(_agent: address) -> bool:
    agentFactory: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(AGENT_FACTORY_ID)
    return staticcall AgentFactory(agentFactory).isAgent(_agent)



######################
# Subscription Utils #
######################


@view
@external
def getCombinedSubData(_user: address, _agent: address, _agentPaidThru: uint256, _protocolPaidThru: uint256, _oracleRegistry: address) -> (SubPaymentInfo, SubPaymentInfo):
    """
    @notice Get combined subscription data for an agent and protocol
    @dev Returns a struct containing payment amounts and paid through blocks for both agent and protocol
    @param _user The address of the user
    @param _agent The address of the agent
    @param _agentPaidThru The paid through block for the agent
    @param _protocolPaidThru The paid through block for the protocol
    @param _oracleRegistry The address of the oracle registry
    @return protocolData struct containing payment amounts and paid through blocks for the protocol
    @return agentData struct containing payment amounts and paid through blocks for the agent
    """
    # NOTE: in future, we may have different pricing tiers depending on the `_user`

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
    data.paidThroughBlock = _paidThroughBlock

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
    assert self._isRegisteredAgent(_agent) # dev: agent not registered
    isAgentOwner: bool = staticcall Agent(_agent).owner() == msg.sender
    assert isAgentOwner or gov._canGovern(msg.sender) # dev: no perms

    if isAgentOwner:
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
    log PendingAgentSubPriceSet(agent=_agent, asset=_asset, usdValue=_usdValue, trialPeriod=_trialPeriod, payPeriod=_payPeriod, effectiveBlock=effectiveBlock)

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
    log AgentSubPriceSet(agent=_agent, asset=_subInfo.asset, usdValue=_subInfo.usdValue, trialPeriod=_subInfo.trialPeriod, payPeriod=_subInfo.payPeriod)


# removing agent sub price


@external
def removeAgentSubPrice(_agent: address) -> bool:
    """
    @notice Remove subscription pricing for a specific agent
    @dev Only callable by governor
    @param _agent The address of the agent
    @return bool True if agent subscription price was removed successfully
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isRegisteredAgent(_agent) # dev: agent not registered

    prevInfo: SubscriptionInfo = self.agentSubPriceData[_agent]
    if empty(address) in [prevInfo.asset, _agent]:
        return False

    self.agentSubPriceData[_agent] = empty(SubscriptionInfo)
    log AgentSubPriceRemoved(agent=_agent, asset=prevInfo.asset, usdValue=prevInfo.usdValue, trialPeriod=prevInfo.trialPeriod, payPeriod=prevInfo.payPeriod)
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
    assert gov._canGovern(msg.sender) # dev: no perms

    assert _isEnabled != self.isAgentSubPricingEnabled # dev: no change
    self.isAgentSubPricingEnabled = _isEnabled
    log AgentSubPricingEnabled(isEnabled=_isEnabled)
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
    assert gov._canGovern(msg.sender) # dev: no perms

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

    log ProtocolSubPriceSet(asset=_asset, usdValue=_usdValue, trialPeriod=_trialPeriod, payPeriod=_payPeriod)
    return True


# removing protocol sub price


@external
def removeProtocolSubPrice() -> bool:
    """
    @notice Remove subscription pricing for the protocol
    @dev Only callable by governor
    @return bool True if protocol subscription price was removed successfully
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    prevInfo: SubscriptionInfo = self.protocolSubPriceData
    if prevInfo.asset == empty(address):
        return False

    self.protocolSubPriceData = empty(SubscriptionInfo)
    log ProtocolSubPriceRemoved(asset=prevInfo.asset, usdValue=prevInfo.usdValue, trialPeriod=prevInfo.trialPeriod, payPeriod=prevInfo.payPeriod)
    return True


####################
# Protocol Tx Fees #
####################


# utilities


@view
@external
def getTransactionFeeDataWithAmbassadorRatio(_user: address, _action: ActionType) -> (uint256, address, uint256):
    """
    @notice Get transaction fee data for the protocol
    @dev Returns a tuple containing the fee amount and recipient address for the protocol
    @param _user The address of the user
    @param _action The type of action being performed
    @return feeAmount The fee amount for the action
    @return recipient The recipient address for the fee
    @return ambassadorRatio The ratio of ambassador proceeds
    """
    # NOTE: in future, we may have different pricing tiers depending on the `_user`
    return self._getTxFeeForAction(_action, self.protocolTxPriceData), self.protocolRecipient, self.ambassadorRatio


@view
@external
def getTransactionFeeData(_user: address, _action: ActionType) -> (uint256, address):
    # NOTE: this function is still used by legacy wallets
    return self._getTxFeeForAction(_action, self.protocolTxPriceData), self.protocolRecipient


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
    elif _action == ActionType.ADD_LIQ:
        return _prices.addLiqFee
    elif _action == ActionType.REMOVE_LIQ:
        return _prices.removeLiqFee
    elif _action == ActionType.CLAIM_REWARDS:
        return _prices.claimRewardsFee
    elif _action == ActionType.BORROW:
        return _prices.borrowFee
    elif _action == ActionType.REPAY:
        return _prices.repayFee
    else:
        return 0


# set protocol tx price sheet


@view
@external
def isValidTxPriceSheet(
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
    _addLiqFee: uint256,
    _removeLiqFee: uint256,
    _claimRewardsFee: uint256,
    _borrowFee: uint256,
    _repayFee: uint256,
) -> bool:
    """
    @notice Check if transaction price sheet parameters are valid
    @dev Validates fee percentages against constraints
    @param _depositFee The fee percentage for deposits
    @param _withdrawalFee The fee percentage for withdrawals
    @param _rebalanceFee The fee percentage for rebalances
    @param _transferFee The fee percentage for transfers
    @param _swapFee The fee percentage for swaps
    @param _addLiqFee The fee percentage for adding liquidity
    @param _removeLiqFee The fee percentage for removing liquidity
    @param _claimRewardsFee The fee percentage for claiming rewards
    @param _borrowFee The fee percentage for borrowing
    @param _repayFee The fee percentage for repaying
    @return bool True if all parameters are valid
    """
    return self._isValidTxPriceSheet(_depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee, _addLiqFee, _removeLiqFee, _claimRewardsFee, _borrowFee, _repayFee)


@view
@internal
def _isValidTxPriceSheet(
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
    _addLiqFee: uint256,
    _removeLiqFee: uint256,
    _claimRewardsFee: uint256,
    _borrowFee: uint256,
    _repayFee: uint256,
) -> bool:
    return _depositFee <= MAX_TX_FEE and _withdrawalFee <= MAX_TX_FEE and _rebalanceFee <= MAX_TX_FEE and _transferFee <= MAX_TX_FEE and _swapFee <= MAX_TX_FEE and _addLiqFee <= MAX_TX_FEE and _removeLiqFee <= MAX_TX_FEE and _claimRewardsFee <= MAX_TX_FEE and _borrowFee <= MAX_TX_FEE and _repayFee <= MAX_TX_FEE


@external
def setProtocolTxPriceSheet(
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
    _addLiqFee: uint256,
    _removeLiqFee: uint256,
    _claimRewardsFee: uint256,
    _borrowFee: uint256,
    _repayFee: uint256,
) -> bool:
    """
    @notice Set transaction price sheet for the protocol
    @dev Only callable by governor
    @param _depositFee The fee percentage for deposits
    @param _withdrawalFee The fee percentage for withdrawals
    @param _rebalanceFee The fee percentage for rebalances
    @param _transferFee The fee percentage for transfers
    @param _swapFee The fee percentage for swaps
    @param _addLiqFee The fee percentage for adding liquidity
    @param _removeLiqFee The fee percentage for removing liquidity
    @param _claimRewardsFee The fee percentage for claiming rewards
    @param _borrowFee The fee percentage for borrowing
    @param _repayFee The fee percentage for repaying
    @return bool True if protocol price sheet was set successfully
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    # validation
    if not self._isValidTxPriceSheet(_depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee, _addLiqFee, _removeLiqFee, _claimRewardsFee, _borrowFee, _repayFee):
        return False

    # save data
    self.protocolTxPriceData = TxPriceSheet(
        depositFee=_depositFee,
        withdrawalFee=_withdrawalFee,
        rebalanceFee=_rebalanceFee,
        transferFee=_transferFee,
        swapFee=_swapFee,
        addLiqFee=_addLiqFee,
        removeLiqFee=_removeLiqFee,
        claimRewardsFee=_claimRewardsFee,
        borrowFee=_borrowFee,
        repayFee=_repayFee,
    )

    log ProtocolTxPriceSheetSet(depositFee=_depositFee, withdrawalFee=_withdrawalFee, rebalanceFee=_rebalanceFee, transferFee=_transferFee, swapFee=_swapFee, addLiqFee=_addLiqFee, removeLiqFee=_removeLiqFee, claimRewardsFee=_claimRewardsFee, borrowFee=_borrowFee, repayFee=_repayFee)
    return True


# remove protocol tx price sheet


@external
def removeProtocolTxPriceSheet() -> bool:
    """
    @notice Remove transaction price sheet for the protocol
    @dev Only callable by governor
    @return bool True if protocol price sheet was removed successfully
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    prevInfo: TxPriceSheet = self.protocolTxPriceData
    self.protocolTxPriceData = empty(TxPriceSheet)
    log ProtocolTxPriceSheetRemoved(depositFee=prevInfo.depositFee, withdrawalFee=prevInfo.withdrawalFee, rebalanceFee=prevInfo.rebalanceFee, transferFee=prevInfo.transferFee, swapFee=prevInfo.swapFee, addLiqFee=prevInfo.addLiqFee, removeLiqFee=prevInfo.removeLiqFee, claimRewardsFee=prevInfo.claimRewardsFee, borrowFee=prevInfo.borrowFee, repayFee=prevInfo.repayFee)
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
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _recipient != empty(address) # dev: invalid recipient
    self.protocolRecipient = _recipient
    log ProtocolRecipientSet(recipient=_recipient)
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
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _delayBlocks == 0 or _delayBlocks >= MIN_PRICE_CHANGE_BUFFER # dev: invalid delay
    self.priceChangeDelay = _delayBlocks
    log PriceChangeDelaySet(delayBlocks=_delayBlocks)
    return True


#######################
# Ambassador Settings #
#######################


@external
def setAmbassadorRatio(_ratio: uint256) -> bool:
    """
    @notice Set the ratio of ambassador proceeds
    @dev Only callable by governor
    @param _ratio The ratio of ambassador proceeds
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _ratio <= HUNDRED_PERCENT # dev: invalid ratio
    self.ambassadorRatio = _ratio
    log AmbassadorRatioSet(ratio=_ratio)
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
    assert gov._canGovern(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log PriceSheetsActivated(isActivated=_shouldActivate)
