# @version 0.4.0

interface LegoRegistry:
    def isValidLegoId(_legoId: uint256) -> bool: view
    def numLegos() -> uint256: view

interface AddyRegistry:
    def governor() -> address: view

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

struct ProtocolPricing:
    recipient: address
    asset: address
    txTakeRate: uint256
    minTxFeeUsdValue: uint256
    subTakeRate: uint256
    minSubFeeUsdValue: uint256

struct CostData:
    protocolRecipient: address
    protocolAsset: address
    protocolAssetAmount: uint256
    protocolUsdValue: uint256
    agentAsset: address
    agentAssetAmount: uint256
    agentUsdValue: uint256

event AgentSubPriceSet:
    agent: indexed(address)
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

event AgentTxPriceSheetSet:
    agent: indexed(address)
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

event ProtocolPricingSet:
    recipient: indexed(address)
    asset: indexed(address)
    txTakeRate: uint256
    minTxFeeUsdValue: uint256
    subTakeRate: uint256
    minSubFeeUsdValue: uint256

event ProtocolPricingRemoved:
    prevRecipient: indexed(address)
    prevAsset: indexed(address)
    prevTxTakeRate: uint256
    prevMinTxFeeUsdValue: uint256
    prevSubTakeRate: uint256
    prevMinSubFeeUsdValue: uint256

event AgentRegistryActivated:
    isActivated: bool

# protocol pricing
protocolPricing: public(ProtocolPricing)

# agent pricing
agentTxPriceData: public(HashMap[address, TxPriceSheet]) # agent -> transaction pricing
agentSubPriceData: public(HashMap[address, SubscriptionInfo]) # agent -> subscription pricing

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_AGENT_TX_FEE: constant(uint256) = 10_00 # 10.00%
MAX_PROTOCOL_TAKE_RATE: constant(uint256) = 50_00 # 50.00%
MIN_TRIAL_PERIOD: constant(uint256) = 43_200 # 1 day on Base (2 seconds per block)
MAX_TRIAL_PERIOD: constant(uint256) = 1_296_000 # 1 month on Base (2 seconds per block)
MIN_PAY_PERIOD: constant(uint256) = 302_400 # 7 days on Base (2 seconds per block)
MAX_PAY_PERIOD: constant(uint256) = 3_900_000 # 3 months on Base (2 seconds per block)


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


####################
# Agent Sub Prices #
####################


@view
@external
def getSubscriptionCost(_agent: address) -> CostData:
    cost: CostData = empty(CostData)
    cost.agentAsset, cost.agentAssetAmount, cost.agentUsdValue = self._getAgentSubFeeData(_agent)
    cost.protocolRecipient, cost.protocolAsset, cost.protocolAssetAmount, cost.protocolUsdValue = self._getProtocolFee(False, cost.agentUsdValue)
    return cost


@view
@external
def getAgentSubFeeData(_agent: address) -> (address, uint256, uint256):
    return self._getAgentSubFeeData(_agent)


@view
@internal
def _getAgentSubFeeData(_agent: address) -> (address, uint256, uint256):
    agentData: SubscriptionInfo = self.agentSubPriceData[_agent]
    if agentData.asset == empty(address):
        return empty(address), 0, 0

    # get subscription fee
    feeUsdValue: uint256 = agentData.usdValue
    assetAmount: uint256 = 0 # TODO: convert feeUsdValue to agent asset amount

    return agentData.asset, assetAmount, feeUsdValue


# set agent sub price


@view
@external
def isValidAgentSubPrice(_agent: address, _asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    return self._isValidAgentSubPrice(_agent, _asset, _usdValue, _trialPeriod, _payPeriod)


@view
@internal
def _isValidAgentSubPrice(_agent: address, _asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    if empty(address) in [_agent, _asset]:
        return False
    
    if _payPeriod < MIN_PAY_PERIOD or _payPeriod > MAX_PAY_PERIOD:
        return False

    if _trialPeriod < MIN_TRIAL_PERIOD or _trialPeriod > MAX_TRIAL_PERIOD:
        return False

    return _usdValue != 0


@external
def setAgentSubPrice(_agent: address, _asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    # validation
    if not self._isValidAgentSubPrice(_agent, _asset, _usdValue, _trialPeriod, _payPeriod):
        return False

    # save data
    self.agentSubPriceData[_agent] = SubscriptionInfo(
        asset=_asset,
        usdValue=_usdValue,
        trialPeriod=_trialPeriod,
        payPeriod=_payPeriod,
    )

    log AgentSubPriceSet(_agent, _asset, _usdValue, _trialPeriod, _payPeriod)
    return True


# removing agent sub price


@view
@external
def isValidAgentSubPriceRemoval(_agent: address) -> bool:
    return self._isValidAgentSubPriceRemoval(_agent, self.agentSubPriceData[_agent])


@view
@internal
def _isValidAgentSubPriceRemoval(_agent: address, _prevInfo: SubscriptionInfo) -> bool:
    return empty(address) not in [_agent, _prevInfo.asset]


@external
def removeAgentSubPrice(_agent: address) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    prevInfo: SubscriptionInfo = self.agentSubPriceData[_agent]
    if not self._isValidAgentSubPriceRemoval(_agent, prevInfo):
        return False

    self.agentSubPriceData[_agent] = empty(SubscriptionInfo)
    log AgentSubPriceRemoved(_agent, prevInfo.asset, prevInfo.usdValue, prevInfo.trialPeriod, prevInfo.payPeriod)
    return True


###################
# Agent Tx Prices #
###################


@view
@external
def getTransactionCost(_agent: address, _action: ActionType, _usdValue: uint256) -> CostData:
    cost: CostData = empty(CostData)
    cost.agentAsset, cost.agentAssetAmount, cost.agentUsdValue = self._getAgentTxFeeData(_agent, _action, _usdValue)
    cost.protocolRecipient, cost.protocolAsset, cost.protocolAssetAmount, cost.protocolUsdValue = self._getProtocolFee(True, cost.agentUsdValue)
    return cost


@view
@external
def getAgentTxFeeData(_agent: address, _action: ActionType, _usdValue: uint256) -> (address, uint256, uint256):
    return self._getAgentTxFeeData(_agent, _action, _usdValue)


@view
@internal
def _getAgentTxFeeData(_agent: address, _action: ActionType, _usdValue: uint256) -> (address, uint256, uint256):
    if _usdValue == 0:
        return empty(address), 0, 0

    agentData: TxPriceSheet = self.agentTxPriceData[_agent]
    if agentData.asset == empty(address):
        return empty(address), 0, 0

    # get transaction fee
    fee: uint256 = self._getTxFeeForAction(_action, agentData)
    feeUsdValue: uint256 = _usdValue * fee // HUNDRED_PERCENT
    assetAmount: uint256 = 0 # TODO: convert feeUsdValue to agent asset amount

    return agentData.asset, assetAmount, feeUsdValue


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


# set agent tx price sheet


@view
@external
def isValidTxPriceSheet(
    _agent: address,
    _asset: address,
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
) -> bool:
    return self._isValidTxPriceSheet(_agent, _asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee)


@view
@internal
def _isValidTxPriceSheet(
    _agent: address,
    _asset: address,
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
) -> bool:
    if empty(address) in [_agent, _asset]:
        return False
    return _depositFee <= MAX_AGENT_TX_FEE and _withdrawalFee <= MAX_AGENT_TX_FEE and _rebalanceFee <= MAX_AGENT_TX_FEE and _transferFee <= MAX_AGENT_TX_FEE and _swapFee <= MAX_AGENT_TX_FEE


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
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    # validation
    if not self._isValidTxPriceSheet(_agent, _asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee):
        return False

    # save data
    self.agentTxPriceData[_agent] = TxPriceSheet(
        asset=_asset,
        depositFee=_depositFee,
        withdrawalFee=_withdrawalFee,
        rebalanceFee=_rebalanceFee,
        transferFee=_transferFee,
        swapFee=_swapFee,
    )

    log AgentTxPriceSheetSet(_agent, _asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee)
    return True


# removing agent tx price sheet


@view
@external
def isValidAgentTxPriceSheetRemoval(_agent: address) -> bool:
    return self._isValidAgentTxPriceSheetRemoval(_agent, self.agentTxPriceData[_agent])


@view
@internal
def _isValidAgentTxPriceSheetRemoval(_agent: address, _prevInfo: TxPriceSheet) -> bool:
    return empty(address) not in [_agent, _prevInfo.asset]


@external
def removeAgentTxPriceSheet(_agent: address) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    prevInfo: TxPriceSheet = self.agentTxPriceData[_agent]
    if not self._isValidAgentTxPriceSheetRemoval(_agent, prevInfo):
        return False

    self.agentTxPriceData[_agent] = empty(TxPriceSheet)
    log AgentTxPriceSheetRemoved(_agent, prevInfo.asset, prevInfo.depositFee, prevInfo.withdrawalFee, prevInfo.rebalanceFee, prevInfo.transferFee, prevInfo.swapFee)
    return True


####################
# Protocol Pricing #
####################


@view
@internal
def _getProtocolFee(_isTx: bool, _agentUsdValue: uint256) -> (address, address, uint256, uint256):
    data: ProtocolPricing = self.protocolPricing
    if data.asset == empty(address) or data.recipient == empty(address):
        return empty(address), empty(address), 0, 0

    takeRate: uint256 = 0
    minFee: uint256 = 0
    if _isTx:
        takeRate = data.txTakeRate
        minFee = data.minTxFeeUsdValue
    else:
        takeRate = data.subTakeRate
        minFee = data.minSubFeeUsdValue

    # get transaction fee
    feeUsdValue: uint256 = max(_agentUsdValue * takeRate // HUNDRED_PERCENT, minFee)
    assetAmount: uint256 = 0 
    if feeUsdValue != 0:
        assetAmount = 0 # TODO: convert feeUsdValue to protocol asset amount

    return data.recipient, data.asset, assetAmount, feeUsdValue


# set protocol pricing


@view
@external
def isValidProtocolPricing(
    _recipient: address,
    _asset: address,
    _txTakeRate: uint256,
    _minTxFeeUsdValue: uint256,
    _subTakeRate: uint256,
    _minSubFeeUsdValue: uint256,
) -> bool:
    return self._isValidProtocolPricing(_recipient, _asset, _txTakeRate, _minTxFeeUsdValue, _subTakeRate, _minSubFeeUsdValue)


@view
@internal
def _isValidProtocolPricing(
    _recipient: address,
    _asset: address,
    _txTakeRate: uint256,
    _minTxFeeUsdValue: uint256,
    _subTakeRate: uint256,
    _minSubFeeUsdValue: uint256,
) -> bool:
    if empty(address) in [_recipient, _asset]:
        return False

    if _txTakeRate > MAX_PROTOCOL_TAKE_RATE or _subTakeRate > MAX_PROTOCOL_TAKE_RATE:
        return False

    # one of these must be non-zero
    return _minTxFeeUsdValue != 0 or _minSubFeeUsdValue != 0


@external
def setProtocolPricing(
    _recipient: address,
    _asset: address,
    _txTakeRate: uint256,
    _minTxFeeUsdValue: uint256,
    _subTakeRate: uint256,
    _minSubFeeUsdValue: uint256,
) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    # validation
    if not self._isValidProtocolPricing(_recipient, _asset, _txTakeRate, _minTxFeeUsdValue, _subTakeRate, _minSubFeeUsdValue):
        return False

    # save data
    self.protocolPricing = ProtocolPricing(
        recipient=_recipient,
        asset=_asset,
        txTakeRate=_txTakeRate,
        minTxFeeUsdValue=_minTxFeeUsdValue,
        subTakeRate=_subTakeRate,
        minSubFeeUsdValue=_minSubFeeUsdValue,
    )

    log ProtocolPricingSet(_recipient, _asset, _txTakeRate, _minTxFeeUsdValue, _subTakeRate, _minSubFeeUsdValue)
    return True


# removing protocol pricing


@view
@external
def isValidProtocolPricingRemoval() -> bool:
    prevInfo: ProtocolPricing = self.protocolPricing
    return self._isValidProtocolPricingRemoval(prevInfo.recipient, prevInfo.asset)


@view
@internal
def _isValidProtocolPricingRemoval(_prevRecipient: address, _prevAsset: address) -> bool:
    return _prevRecipient != empty(address) and _prevAsset != empty(address)


@external
def removeProtocolPricing() -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    prevInfo: ProtocolPricing = self.protocolPricing
    if not self._isValidProtocolPricingRemoval(prevInfo.recipient, prevInfo.asset):
        return False

    self.protocolPricing = empty(ProtocolPricing)
    log ProtocolPricingRemoved(prevInfo.recipient, prevInfo.asset, prevInfo.txTakeRate, prevInfo.minTxFeeUsdValue, prevInfo.subTakeRate, prevInfo.minSubFeeUsdValue)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AgentRegistryActivated(_shouldActivate)