# @version 0.4.0

interface LegoRegistry:
    def isValidLegoId(_legoId: uint256) -> bool: view
    def governor() -> address: view
    def numLegos() -> uint256: view

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
    asset: address
    txTakeRate: uint256
    subTakeRate: uint256

struct CostData:
    protocolAsset: address
    protocolAssetAmount: uint256
    protocolUsdValue: uint256
    agentAsset: address
    agentAssetAmount: uint256
    agentUsdValue: uint256

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

event ProtocolPricingSet:
    asset: indexed(address)
    txTakeRate: uint256
    subTakeRate: uint256

event ProtocolPricingRemoved:
    prevAsset: indexed(address)

event AgentRegistryActivated:
    isActivated: bool

# protocol pricing
protocolPricing: public(ProtocolPricing)

# agent pricing
agentTxPriceData: public(HashMap[address, TxPriceSheet]) # agent -> transaction pricing
agentSubPriceData: public(HashMap[address, SubscriptionInfo]) # agent -> subscription pricing

# system
isActivated: public(bool)
LEGO_REGISTRY: public(immutable(address))

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_AGENT_TX_FEE: constant(uint256) = 10_00 # 10.00%
MAX_PROTOCOL_TAKE_RATE: constant(uint256) = 50_00 # 50.00%


@deploy
def __init__(_legoRegistry: address):
    assert empty(address) not in [_legoRegistry] # dev: invalid addrs
    LEGO_REGISTRY = _legoRegistry
    self.isActivated = True


@view
@external
def getTransactionCost(_agent: address, _action: ActionType, _usdValue: uint256) -> CostData:
    cost: CostData = empty(CostData)
    cost.agentAsset, cost.agentAssetAmount, cost.agentUsdValue = self._getAgentTxFeeData(_agent, _action, _usdValue)
    cost.protocolAsset, cost.protocolAssetAmount, cost.protocolUsdValue = self._getProtocolFee(True, cost.agentUsdValue)
    return cost


###################
# Agent Tx Prices #
###################


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
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms

    # validation
    assert empty(address) not in [_agent, _asset] # dev: invalid addrs
    self._validateTxPriceSheet(_depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee)

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


@view
@internal
def _validateTxPriceSheet(_depositFee: uint256, _withdrawalFee: uint256, _rebalanceFee: uint256, _transferFee: uint256, _swapFee: uint256):
    assert _depositFee <= MAX_AGENT_TX_FEE # dev: invalid deposit fee
    assert _withdrawalFee <= MAX_AGENT_TX_FEE # dev: invalid withdrawal fee
    assert _rebalanceFee <= MAX_AGENT_TX_FEE # dev: invalid rebalance fee
    assert _transferFee <= MAX_AGENT_TX_FEE # dev: invalid transfer fee
    assert _swapFee <= MAX_AGENT_TX_FEE # dev: invalid swap fee


# removing agent tx price sheet


@external
def removeAgentTxPriceSheet(_agent: address) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms

    assert empty(address) != _agent # dev: invalid addr
    self.agentTxPriceData[_agent] = empty(TxPriceSheet)

    log AgentTxPriceSheetRemoved(_agent)
    return True


####################
# Protocol Pricing #
####################


@view
@internal
def _getProtocolFee(_isTx: bool, _agentUsdValue: uint256) -> (address, uint256, uint256):
    if _agentUsdValue == 0:
        return empty(address), 0, 0

    data: ProtocolPricing = self.protocolPricing
    if data.asset == empty(address):
        return empty(address), 0, 0

    takeRate: uint256 = 0
    if _isTx:
        takeRate = data.txTakeRate
    else:
        takeRate = data.subTakeRate

    # get transaction fee
    feeUsdValue: uint256 = _agentUsdValue * takeRate // HUNDRED_PERCENT
    assetAmount: uint256 = 0 
    if feeUsdValue != 0:
        assetAmount = 0 # TODO: convert feeUsdValue to protocol asset amount

    return data.asset, assetAmount, feeUsdValue


# set protocol pricing


@external
def setProtocolPricing(
    _asset: address,
    _txTakeRate: uint256,
    _subTakeRate: uint256,
) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms

    # validation
    assert empty(address) != _asset # dev: invalid addr
    assert _txTakeRate <= MAX_PROTOCOL_TAKE_RATE # dev: invalid tx take rate
    assert _subTakeRate <= MAX_PROTOCOL_TAKE_RATE # dev: invalid sub take rate

    self.protocolPricing = ProtocolPricing(
        asset=_asset,
        txTakeRate=_txTakeRate,
        subTakeRate=_subTakeRate,
    )

    log ProtocolPricingSet(_asset, _txTakeRate, _subTakeRate)
    return True


# removing protocol pricing


@external
def removeProtocolPricing() -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms

    prevAsset: address = self.protocolPricing.asset
    self.protocolPricing = empty(ProtocolPricing)
    log ProtocolPricingRemoved(prevAsset)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AgentRegistryActivated(_shouldActivate)