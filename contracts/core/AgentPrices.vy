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

struct TransactionCost:
    protocolAsset: address
    protocolCost: uint256
    agentAsset: address
    agentCost: uint256

struct PricesData:
    asset: address
    defaultPrices: PriceSheet

struct PriceSheet:
    isSet: bool
    deposit: uint256
    withdrawal: uint256
    rebalance: uint256
    transfer: uint256
    swap: uint256

event AgentRegistryActivated:
    isActivated: bool

event AgentPricesRegistered:
    agent: indexed(address)
    asset: indexed(address)
    defaultPrices: PriceSheet

event AgentPricesDisabled:
    agent: indexed(address)

event GranularAgentPricesSet:
    agent: indexed(address)
    legoId: uint256
    priceSheet: PriceSheet

event GranularAgentPriceDisabled:
    agent: indexed(address)
    legoId: uint256

event ProtocolPricesSet:
    asset: indexed(address)
    defaultPrices: PriceSheet

event GranularProtocolPricesSet:
    legoId: uint256
    priceSheet: PriceSheet

event GranularProtocolPriceDisabled:
    legoId: uint256

# agent price sheets
agentData: public(HashMap[address, PricesData]) # agent -> data
granularAgentPrices: public(HashMap[address, HashMap[uint256, PriceSheet]]) # agent -> lego id -> price sheet

# platform price sheet
protocolData: public(PricesData)
granularProtocolPrices: public(HashMap[uint256, PriceSheet]) # lego id -> price sheet

# system
isActivated: public(bool)
LEGO_REGISTRY: public(immutable(address))
MAX_LEGO_IDS: public(constant(uint256)) = 25


@deploy
def __init__(_legoRegistry: address):
    assert empty(address) not in [_legoRegistry] # dev: invalid addrs
    LEGO_REGISTRY = _legoRegistry
    self.isActivated = True


#############
# Get Costs #
#############


@view
@external
def getTransactionCost(_agent: address, _legoId: uint256, _action: ActionType) -> TransactionCost:
    cost: TransactionCost = empty(TransactionCost)
    cost.agentAsset, cost.agentCost = self._getAgentDataAndCost(_agent, _legoId, _action)
    cost.protocolAsset, cost.protocolCost = self._getProtocolDataAndCost(_legoId, _action)
    return cost


@view
@internal
def _getAgentDataAndCost(_agent: address, _legoId: uint256, _action: ActionType) -> (address, uint256):
    agentData: PricesData = self.agentData[_agent]
    if agentData.asset == empty(address):
        return empty(address), 0

    cost: uint256 = self._getCostForAction(_action, self.granularAgentPrices[_agent][_legoId])
    if cost == 0:
        cost = self._getCostForAction(_action, agentData.defaultPrices)

    return agentData.asset, cost


@view
@internal
def _getProtocolDataAndCost(_legoId: uint256, _action: ActionType) -> (address, uint256):
    protocolData: PricesData = self.protocolData
    if protocolData.asset == empty(address):
        return empty(address), 0

    cost: uint256 = self._getCostForAction(_action, self.granularProtocolPrices[_legoId])
    if cost == 0:
        cost = self._getCostForAction(_action, protocolData.defaultPrices)

    return protocolData.asset, cost


@view
@internal
def _getCostForAction(_action: ActionType, _priceSheet: PriceSheet) -> uint256:
    if not _priceSheet.isSet:
        return 0
    if _action == ActionType.DEPOSIT:
        return _priceSheet.deposit
    elif _action == ActionType.WITHDRAWAL:
        return _priceSheet.withdrawal
    elif _action == ActionType.REBALANCE:
        return _priceSheet.rebalance
    elif _action == ActionType.TRANSFER:
        return _priceSheet.transfer
    elif _action == ActionType.SWAP:
        return _priceSheet.swap
    else:
        return 0


@view
@internal
def _hasPriceSheetSet(_priceSheet: PriceSheet) -> bool:
    return _priceSheet.deposit != 0 or _priceSheet.withdrawal != 0 or _priceSheet.rebalance != 0 or _priceSheet.transfer != 0 or _priceSheet.swap != 0


########################
# Agent Price Settings #
########################


@external
def registerAgent(_agent: address, _asset: address, _defaultPrices: PriceSheet) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    assert empty(address) not in [_agent, _asset] # dev: invalid addrs

    defaultPrices: PriceSheet = _defaultPrices
    defaultPrices.isSet = self._hasPriceSheetSet(_defaultPrices)
    assert defaultPrices.isSet # dev: invalid default prices

    self.agentData[_agent] = PricesData(
        asset=_asset,
        defaultPrices=defaultPrices,
    )
    log AgentPricesRegistered(_agent, _asset, defaultPrices)
    return True


# granular prices


@external
def setGranularAgentPrices(_agent: address, _legoId: uint256, _priceSheet: PriceSheet) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_legoId) # dev: invalid lego id

    self._setGranularAgentPrices(_agent, _legoId, _priceSheet)
    return True


@external
def setManyGranularAgentPrices(_agent: address, _legoIds: DynArray[uint256, MAX_LEGO_IDS], _priceSheets: DynArray[PriceSheet, MAX_LEGO_IDS]) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms
    assert len(_legoIds) == len(_priceSheets) # dev: invalid arrays

    for i: uint256 in range(len(_legoIds), bound=MAX_LEGO_IDS):
        legoId: uint256 = _legoIds[i]
        assert staticcall LegoRegistry(legoRegistry).isValidLegoId(legoId) # dev: invalid lego id
        self._setGranularAgentPrices(_agent, legoId, _priceSheets[i])

    return True


@internal
def _setGranularAgentPrices(_agent: address, _legoId: uint256, _priceSheet: PriceSheet):
    priceSheet: PriceSheet = _priceSheet
    priceSheet.isSet = self._hasPriceSheetSet(_priceSheet)
    assert priceSheet.isSet # dev: invalid price sheet
    self.granularAgentPrices[_agent][_legoId] = priceSheet
    log GranularAgentPricesSet(_agent, _legoId, priceSheet)


# disabling agent / granular prices


@external
def disableAgent(_agent: address) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms
    assert empty(address) != _agent # dev: invalid addr

    self.agentData[_agent] = empty(PricesData)
    log AgentPricesDisabled(_agent)

    numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
    for i: uint256 in range(numLegos, bound=max_value(uint256)):
        self._disableGranularAgentPrices(_agent, i)

    return True


@external
def disableGranularAgentPrices(_agent: address, _legoIds: DynArray[uint256, MAX_LEGO_IDS] = []) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms
    assert _agent != empty(address) # dev: invalid addr

    # disable all granular prices if no lego ids are provided
    if len(_legoIds) == 0:
        numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
        for i: uint256 in range(numLegos, bound=max_value(uint256)):
            self._disableGranularAgentPrices(_agent, i)
    
    # specific lego ids provided
    else:
        for i: uint256 in range(len(_legoIds), bound=MAX_LEGO_IDS):
            legoId: uint256 = _legoIds[i]
            assert staticcall LegoRegistry(legoRegistry).isValidLegoId(legoId) # dev: invalid lego id
            self._disableGranularAgentPrices(_agent, legoId)

    return True


@internal
def _disableGranularAgentPrices(_agent: address, _legoId: uint256):
    priceData: PriceSheet = self.granularAgentPrices[_agent][_legoId]
    if priceData.isSet:
        self.granularAgentPrices[_agent][_legoId] = empty(PriceSheet)
        log GranularAgentPriceDisabled(_agent, _legoId)


###########################
# Protocol Price Settings #
###########################


@external
def setProtocolPrices(_asset: address, _defaultPrices: PriceSheet) -> bool:
    assert self.isActivated # dev: not active
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    assert empty(address) != _asset # dev: invalid addr

    defaultPrices: PriceSheet = _defaultPrices
    defaultPrices.isSet = self._hasPriceSheetSet(_defaultPrices)
    assert defaultPrices.isSet # dev: invalid default prices

    self.protocolData = PricesData(
        asset=_asset,
        defaultPrices=defaultPrices,
    )
    log ProtocolPricesSet(_asset, defaultPrices)
    return True


# granular prices


@external
def setGranularProtocolPrices(_legoId: uint256, _priceSheet: PriceSheet) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms
    assert staticcall LegoRegistry(legoRegistry).isValidLegoId(_legoId) # dev: invalid lego id

    self._setGranularProtocolPrices(_legoId, _priceSheet)
    return True


@external
def setManyGranularProtocolPrices(_legoIds: DynArray[uint256, MAX_LEGO_IDS], _priceSheets: DynArray[PriceSheet, MAX_LEGO_IDS]) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms
    assert len(_legoIds) == len(_priceSheets) # dev: invalid arrays

    for i: uint256 in range(len(_legoIds), bound=MAX_LEGO_IDS):
        legoId: uint256 = _legoIds[i]
        assert staticcall LegoRegistry(legoRegistry).isValidLegoId(legoId) # dev: invalid lego id
        self._setGranularProtocolPrices(legoId, _priceSheets[i])

    return True


@internal
def _setGranularProtocolPrices(_legoId: uint256, _priceSheet: PriceSheet):
    priceSheet: PriceSheet = _priceSheet
    priceSheet.isSet = self._hasPriceSheetSet(_priceSheet)
    assert priceSheet.isSet # dev: invalid price sheet
    self.granularProtocolPrices[_legoId] = priceSheet
    log GranularProtocolPricesSet(_legoId, priceSheet)


# disable granular protocol prices


@external
def disableGranularProtocolPrices(_legoIds: DynArray[uint256, MAX_LEGO_IDS] = []) -> bool:
    assert self.isActivated # dev: not active
    legoRegistry: address = LEGO_REGISTRY
    assert msg.sender == staticcall LegoRegistry(legoRegistry).governor() # dev: no perms

    # disable all granular prices if no lego ids are provided
    if len(_legoIds) == 0:
        numLegos: uint256 = staticcall LegoRegistry(legoRegistry).numLegos()
        for i: uint256 in range(numLegos, bound=max_value(uint256)):
            self._disableGranularProtocolPrices(i)
    
    # specific lego ids provided
    else:
        for i: uint256 in range(len(_legoIds), bound=MAX_LEGO_IDS):
            legoId: uint256 = _legoIds[i]
            assert staticcall LegoRegistry(legoRegistry).isValidLegoId(legoId) # dev: invalid lego id
            self._disableGranularProtocolPrices(legoId)

    return True


@internal
def _disableGranularProtocolPrices(_legoId: uint256):
    priceData: PriceSheet = self.granularProtocolPrices[_legoId]
    if priceData.isSet:
        self.granularProtocolPrices[_legoId] = empty(PriceSheet)
        log GranularProtocolPriceDisabled(_legoId)


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AgentRegistryActivated(_shouldActivate)