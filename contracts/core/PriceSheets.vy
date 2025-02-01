# @version 0.4.0

interface LegoRegistry:
    def isValidLegoId(_legoId: uint256) -> bool: view
    def numLegos() -> uint256: view

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

struct TransactionCost:
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

event AgentTxPriceSheetSet:
    agent: indexed(address)
    asset: indexed(address)
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256

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

event ProtocolRecipientSet:
    recipient: indexed(address)

event AgentRegistryActivated:
    isActivated: bool

# protocol pricing
protocolRecipient: public(address) # protocol recipient
protocolTxPriceData: public(TxPriceSheet) # protocol transaction pricing
protocolSubPriceData: public(SubscriptionInfo) # protocol subscription pricing

# agent pricing
agentTxPriceData: public(HashMap[address, TxPriceSheet]) # agent -> transaction pricing
agentSubPriceData: public(HashMap[address, SubscriptionInfo]) # agent -> subscription pricing

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_TX_FEE: constant(uint256) = 10_00 # 10.00%
MIN_TRIAL_PERIOD: constant(uint256) = 43_200 # 1 day on Base (2 seconds per block)
MAX_TRIAL_PERIOD: constant(uint256) = 1_296_000 # 1 month on Base (2 seconds per block)
MIN_PAY_PERIOD: constant(uint256) = 302_400 # 7 days on Base (2 seconds per block)
MAX_PAY_PERIOD: constant(uint256) = 3_900_000 # 3 months on Base (2 seconds per block)


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.protocolRecipient = staticcall AddyRegistry(_addyRegistry).governor()
    self.isActivated = True


#####################
# Subscription Fees #
#####################


# set sub price


@view
@external
def isValidSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
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
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    # validation
    assert _agent != empty(address) # dev: invalid agent
    if not self._isValidSubPrice(_asset, _usdValue, _trialPeriod, _payPeriod):
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


@external
def setProtocolSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

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


# removing sub price


@external
def removeAgentSubPrice(_agent: address) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    prevInfo: SubscriptionInfo = self.agentSubPriceData[_agent]
    if empty(address) in [prevInfo.asset, _agent]:
        return False

    self.agentSubPriceData[_agent] = empty(SubscriptionInfo)
    log AgentSubPriceRemoved(_agent, prevInfo.asset, prevInfo.usdValue, prevInfo.trialPeriod, prevInfo.payPeriod)
    return True


@external
def removeProtocolSubPrice() -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    prevInfo: SubscriptionInfo = self.protocolSubPriceData
    if prevInfo.asset == empty(address):
        return False

    self.protocolSubPriceData = empty(SubscriptionInfo)
    log ProtocolSubPriceRemoved(prevInfo.asset, prevInfo.usdValue, prevInfo.trialPeriod, prevInfo.payPeriod)
    return True


####################
# Transaction Fees #
####################


@view
@external
def getTransactionCost(_agent: address, _action: ActionType, _usdValue: uint256) -> TransactionCost:
    cost: TransactionCost = empty(TransactionCost)
    cost.agentAsset, cost.agentAssetAmount, cost.agentUsdValue = self._getTransactionFeeData(_action, _usdValue, self.agentTxPriceData[_agent])
    cost.protocolAsset, cost.protocolAssetAmount, cost.protocolUsdValue = self._getTransactionFeeData(_action, _usdValue, self.protocolTxPriceData)
    if cost.protocolAsset != empty(address):
        cost.protocolRecipient = self.protocolRecipient
    return cost


@view
@external
def getAgentTransactionFeeData(_agent: address, _action: ActionType, _usdValue: uint256) -> (address, uint256, uint256):
    return self._getTransactionFeeData(_action, _usdValue, self.agentTxPriceData[_agent])


@view
@external
def getProtocolTransactionFeeData(_action: ActionType, _usdValue: uint256) -> (address, uint256, uint256):
    return self._getTransactionFeeData(_action, _usdValue, self.protocolTxPriceData)


@view
@internal
def _getTransactionFeeData(_action: ActionType, _usdValue: uint256, _priceSheet: TxPriceSheet) -> (address, uint256, uint256):
    if _usdValue == 0 or _priceSheet.asset == empty(address):
        return empty(address), 0, 0

    # get transaction fee
    fee: uint256 = self._getTxFeeForAction(_action, _priceSheet)
    feeUsdValue: uint256 = _usdValue * fee // HUNDRED_PERCENT
    assetAmount: uint256 = 0 
    if feeUsdValue != 0:
        oracleRegistry: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)
        assetAmount = staticcall OracleRegistry(oracleRegistry).getAssetAmount(_priceSheet.asset, feeUsdValue, False)

    return _priceSheet.asset, assetAmount, feeUsdValue


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


# set tx price sheet


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
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    # validation
    assert _agent != empty(address) # dev: invalid agent
    if not self._isValidTxPriceSheet(_asset, _depositFee, _withdrawalFee, _rebalanceFee, _transferFee, _swapFee):
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


@external
def setProtocolTxPriceSheet(
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


# removing tx price sheet


@external
def removeAgentTxPriceSheet(_agent: address) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    prevInfo: TxPriceSheet = self.agentTxPriceData[_agent]
    if empty(address) in [prevInfo.asset, _agent]:
        return False

    self.agentTxPriceData[_agent] = empty(TxPriceSheet)
    log AgentTxPriceSheetRemoved(_agent, prevInfo.asset, prevInfo.depositFee, prevInfo.withdrawalFee, prevInfo.rebalanceFee, prevInfo.transferFee, prevInfo.swapFee)
    return True


@external
def removeProtocolTxPriceSheet() -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

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
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    assert _recipient != empty(address) # dev: invalid recipient
    self.protocolRecipient = _recipient
    log ProtocolRecipientSet(_recipient)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AgentRegistryActivated(_shouldActivate)