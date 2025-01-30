# @version 0.4.0

from ethereum.ercs import IERC20Detailed
import interfaces.LegoInterface as LegoPartner
import interfaces.OraclePartnerInterface as OraclePartner

interface AddyRegistry:
    def governor() -> address: view

struct OraclePartnerInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]

event NewOraclePartnerRegistered:
    addr: indexed(address)
    oraclePartnerId: uint256
    description: String[64]

event OraclePartnerAddrUpdated:
    newAddr: indexed(address)
    prevAddr: indexed(address)
    oraclePartnerId: uint256
    version: uint256
    description: String[64]

event OraclePartnerAddrDisabled:
    prevAddr: indexed(address)
    oraclePartnerId: uint256
    version: uint256
    description: String[64]

event PriorityOraclePartnerIdsModified:
    numIds: uint256

event StaleTimeSet:
    staleTime: uint256

event OracleRegistryActivated:
    isActivated: bool

# registry core
oraclePartnerInfo: public(HashMap[uint256, OraclePartnerInfo])
oraclePartnerAddrToId: public(HashMap[address, uint256])
numOraclePartners: public(uint256)

# custom config
priorityOraclePartnerIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
staleTime: public(uint256)

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)

ETH: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE
MAX_PRIORITY_PARTNERS: constant(uint256) = 10
MIN_STALE_TIME: constant(uint256) = 60 * 5 # 5 minutes
MAX_STALE_TIME: constant(uint256) = 60 * 60 * 24 * 3 # 3 days


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True

    # start at 1 index
    self.numOraclePartners = 1


#########
# Price #
#########


@view
@external
def getPrice(_asset: address) -> uint256:
    if _asset == empty(address):
        return 0
    return self._getPrice(_asset)


@view
@internal
def _getPrice(_asset: address) -> uint256:
    price: uint256 = 0
    staleTime: uint256 = self.staleTime
    alreadyLooked: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []

    # go thru priority partners first
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self.priorityOraclePartnerIds
    for i: uint256 in range(len(priorityIds), bound=MAX_PRIORITY_PARTNERS):
        pid: uint256 = priorityIds[i]
        oraclePartner: address = self.oraclePartnerInfo[pid].addr
        if oraclePartner == empty(address):
            continue
        price = staticcall OraclePartner(oraclePartner).getPrice(_asset, staleTime, self)
        if price != 0:
            break
        alreadyLooked.append(pid)

    # go thru rest of oracle partners
    if price == 0:
        numSources: uint256 = self.numOraclePartners
        for id: uint256 in range(1, numSources, bound=max_value(uint256)):
            if id in alreadyLooked:
                continue
            oraclePartner: address = self.oraclePartnerInfo[id].addr
            if oraclePartner == empty(address):
                continue
            price = staticcall OraclePartner(oraclePartner).getPrice(_asset, staleTime, self)
            if price != 0:
                break

    return price


# other utils


@view
@external
def getUsdValue(_asset: address, _amount: uint256) -> uint256:
    return self._getUsdValue(_asset, _amount)


@view
@internal
def _getUsdValue(_asset: address, _amount: uint256) -> uint256:
    if _amount == 0 or _asset == empty(address):
        return 0
    price: uint256 = self._getPrice(_asset)
    if price == 0:
        return 0
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    return price * _amount // (10 ** decimals)


@view
@external
def getAssetAmount(_asset: address, _usdValue: uint256) -> uint256:
    return self._getAssetAmount(_asset, _usdValue)


@view
@internal
def _getAssetAmount(_asset: address, _usdValue: uint256) -> uint256:
    if _usdValue == 0 or _asset == empty(address):
        return 0
    price: uint256 = self._getPrice(_asset)
    if price == 0:
        return 0
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    return _usdValue * (10 ** decimals) // price


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    numSources: uint256 = self.numOraclePartners
    for id: uint256 in range(1, numSources, bound=max_value(uint256)):
        oraclePartner: address = self.oraclePartnerInfo[id].addr
        if oraclePartner == empty(address):
            continue
        if staticcall OraclePartner(oraclePartner).hasPriceFeed(_asset):
            return True
    return False


@view
@external
def getEthUsdValue(_amount: uint256) -> uint256:
    return self._getUsdValue(ETH, _amount)


@view
@external
def getEthAmount(_usdValue: uint256) -> uint256:
    return self._getAssetAmount(ETH, _usdValue)


###########################
# Register Oracle Partner #
###########################


@view
@external
def isValidNewOraclePartnerAddr(_addr: address) -> bool:
    return self._isValidNewOraclePartnerAddr(_addr)


@view
@internal
def _isValidNewOraclePartnerAddr(_addr: address) -> bool:
    if _addr == empty(address) or not _addr.is_contract:
        return False
    return self.oraclePartnerAddrToId[_addr] == 0


@external
def registerNewOraclePartner(_addr: address, _description: String[64]) -> uint256:
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    if not self._isValidNewOraclePartnerAddr(_addr):
        return 0

    data: OraclePartnerInfo = OraclePartnerInfo(
        addr=_addr,
        version=1,
        lastModified=block.timestamp,
        description=_description,
    )

    oraclePartnerId: uint256 = self.numOraclePartners
    self.oraclePartnerAddrToId[_addr] = oraclePartnerId
    self.numOraclePartners = oraclePartnerId + 1
    self.oraclePartnerInfo[oraclePartnerId] = data
    assert extcall OraclePartner(_addr).setOraclePartnerId(oraclePartnerId) # dev: set id failed

    log NewOraclePartnerRegistered(_addr, oraclePartnerId, _description)
    return oraclePartnerId


#########################
# Update Oracle Partner #
#########################


@view
@external
def isValidOraclePartnerUpdate(_oracleId: uint256, _newAddr: address) -> bool:
    return self._isValidOraclePartnerUpdate(_oracleId, _newAddr, self.oraclePartnerInfo[_oracleId].addr)


@view
@internal
def _isValidOraclePartnerUpdate(_oracleId: uint256, _newAddr: address, _prevAddr: address) -> bool:
    if not self._isValidOraclePartnerId(_oracleId):
        return False
    if not self._isValidNewOraclePartnerAddr(_newAddr):
        return False
    return _newAddr != _prevAddr


@external
def updateOraclePartnerAddr(_oracleId: uint256, _newAddr: address) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    data: OraclePartnerInfo = self.oraclePartnerInfo[_oracleId]
    prevAddr: address = data.addr # needed for later

    if not self._isValidOraclePartnerUpdate(_oracleId, _newAddr, prevAddr):
        return False

    # save new data
    data.addr = _newAddr
    data.lastModified = block.timestamp
    data.version += 1
    self.oraclePartnerInfo[_oracleId] = data
    self.oraclePartnerAddrToId[_newAddr] = _oracleId
    assert extcall OraclePartner(_newAddr).setOraclePartnerId(_oracleId) # dev: set id failed

    # handle previous addr
    if prevAddr != empty(address):
        self.oraclePartnerAddrToId[prevAddr] = 0

    log OraclePartnerAddrUpdated(_newAddr, prevAddr, _oracleId, data.version, data.description)
    return True


##########################
# Disable Oracle Partner #
##########################


@view
@external
def isValidOraclePartnerDisable(_oracleId: uint256) -> bool:
    return self._isValidOraclePartnerDisable(_oracleId, self.oraclePartnerInfo[_oracleId].addr)


@view
@internal
def _isValidOraclePartnerDisable(_oracleId: uint256, _prevAddr: address) -> bool:
    if not self._isValidOraclePartnerId(_oracleId):
        return False
    return _prevAddr != empty(address)


@external
def disableOraclePartnerAddr(_oracleId: uint256) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    data: OraclePartnerInfo = self.oraclePartnerInfo[_oracleId]
    prevAddr: address = data.addr # needed for later

    if not self._isValidOraclePartnerDisable(_oracleId, prevAddr):
        return False

    # save new data
    data.addr = empty(address)
    data.lastModified = block.timestamp
    data.version += 1
    self.oraclePartnerInfo[_oracleId] = data
    self.oraclePartnerAddrToId[prevAddr] = 0

    log OraclePartnerAddrDisabled(prevAddr, _oracleId, data.version, data.description)
    return True


############################
# Priority Oracle Partners #
############################


@view 
@external 
def getPriorityOraclePartnerIds() -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    return self.priorityOraclePartnerIds


@view
@internal
def _sanitizePriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    sanitizedIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []
    for i: uint256 in range(len(_priorityIds), bound=MAX_PRIORITY_PARTNERS):
        pid: uint256 = _priorityIds[i]
        if not self._isValidOraclePartnerId(pid):
            continue
        if pid in sanitizedIds:
            continue
        sanitizedIds.append(pid)
    return sanitizedIds


@view
@external
def areValidPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePriorityOraclePartnerIds(_priorityIds)
    return self._areValidPriorityOraclePartnerIds(priorityIds)


@view
@internal
def _areValidPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    return len(_priorityIds) != 0


@external
def setPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePriorityOraclePartnerIds(_priorityIds)
    if not self._areValidPriorityOraclePartnerIds(priorityIds):
        return False

    self.priorityOraclePartnerIds = priorityIds
    log PriorityOraclePartnerIdsModified(len(priorityIds))
    return True


##############
# Stale Time #
##############


@view
@external
def isValidStaleTime(_staleTime: uint256) -> bool:
    return self._isValidStaleTime(_staleTime)


@view
@internal
def _isValidStaleTime(_staleTime: uint256) -> bool:
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME


@external
def setStaleTime(_staleTime: uint256) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    if not self._isValidStaleTime(_staleTime):
        return False

    self.staleTime = _staleTime
    log StaleTimeSet(_staleTime)
    return True


#################
# Views / Utils #
#################


# is valid


@view
@external
def isValidOraclePartnerAddr(_addr: address) -> bool:
    return self.oraclePartnerAddrToId[_addr] != 0


@view
@external
def isValidOraclePartnerId(_oracleId: uint256) -> bool:
    return self._isValidOraclePartnerId(_oracleId)


@view
@internal
def _isValidOraclePartnerId(_oracleId: uint256) -> bool:
    return _oracleId != 0 and _oracleId < self.numOraclePartners


# oracle partner getters


@view
@external
def getOraclePartnerId(_addr: address) -> uint256:
    return self.oraclePartnerAddrToId[_addr]


@view
@external
def getOraclePartnerAddr(_oracleId: uint256) -> address:
    return self.oraclePartnerInfo[_oracleId].addr


@view
@external
def getOraclePartnerInfo(_oracleId: uint256) -> OraclePartnerInfo:
    return self.oraclePartnerInfo[_oracleId]


@view
@external
def getOraclePartnerDescription(_oracleId: uint256) -> String[64]:
    return self.oraclePartnerInfo[_oracleId].description


# high level


@view
@external
def getNumOraclePartners() -> uint256:
    return self.numOraclePartners - 1


@view
@external
def getLastOraclePartnerAddr() -> address:
    lastIndex: uint256 = self.numOraclePartners - 1
    return self.oraclePartnerInfo[lastIndex].addr


@view
@external
def getLastOraclePartnerId() -> uint256:
    return self.numOraclePartners - 1


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log OracleRegistryActivated(_shouldActivate)
