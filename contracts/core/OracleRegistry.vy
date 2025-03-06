# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

initializes: gov
exports: gov.__interface__

from ethereum.ercs import IERC20Detailed
import interfaces.OraclePartnerInterface as OraclePartner
import contracts.modules.Governable as gov

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

# registry core
oraclePartnerInfo: public(HashMap[uint256, OraclePartnerInfo])
oraclePartnerAddrToId: public(HashMap[address, uint256])
numOraclePartners: public(uint256)

# custom config
priorityOraclePartnerIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
staleTime: public(uint256)

# config
ADDY_REGISTRY: public(immutable(address))

ETH: public(immutable(address))
MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))

MAX_PRIORITY_PARTNERS: constant(uint256) = 10


@deploy
def __init__(_ethAddr: address, _minStaleTime: uint256, _maxStaleTime: uint256, _addyRegistry: address):
    assert empty(address) not in [_ethAddr, _addyRegistry] # dev: invalid addy registry
    gov.__init__(_addyRegistry)

    ETH = _ethAddr
    MIN_STALE_TIME = _minStaleTime
    MAX_STALE_TIME = _maxStaleTime
    ADDY_REGISTRY = _addyRegistry

    # start at 1 index
    self.numOraclePartners = 1


#########
# Price #
#########


@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
    """
    @notice Get the USD price of an asset from registered oracle partners
    @dev Checks priority partners first, then others. Returns 0 if no valid price found.
    @param _asset The address of the asset to get price for
    @param _shouldRaise If True, raises an error when price feed exists but returns no price
    @return The asset price in USD with 18 decimals
    """
    if _asset == empty(address):
        return 0
    return self._getPrice(_asset, _shouldRaise)


@view
@internal
def _getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
    price: uint256 = 0
    hasFeedConfig: bool = False
    alreadyLooked: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []
    staleTime: uint256 = self.staleTime

    # go thru priority partners first
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self.priorityOraclePartnerIds
    for i: uint256 in range(len(priorityIds), bound=MAX_PRIORITY_PARTNERS):
        pid: uint256 = priorityIds[i]
        hasFeed: bool = False
        price, hasFeed = self._getPriceFromOraclePartner(pid, _asset, staleTime)
        if price != 0:
            break
        if hasFeed:
            hasFeedConfig = True
        alreadyLooked.append(pid)

    # go thru rest of oracle partners
    if price == 0:
        numSources: uint256 = self.numOraclePartners
        for id: uint256 in range(1, numSources, bound=max_value(uint256)):
            if id in alreadyLooked:
                continue
            hasFeed: bool = False
            price, hasFeed = self._getPriceFromOraclePartner(id, _asset, staleTime)
            if price != 0:
                break
            if hasFeed:
                hasFeedConfig = True

    # raise exception if feed exists but no price
    if price == 0 and hasFeedConfig and _shouldRaise:
        raise "has price config, no price"

    return price


@view
@internal
def _getPriceFromOraclePartner(_pid: uint256, _asset: address, _staleTime: uint256) -> (uint256, bool):
    oraclePartner: address = self.oraclePartnerInfo[_pid].addr
    if oraclePartner == empty(address):
        return 0, False
    return staticcall OraclePartner(oraclePartner).getPriceAndHasFeed(_asset, _staleTime, self)


# other utils


@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256:
    """
    @notice Calculate the USD value of a given amount of an asset
    @dev Accounts for asset decimals in calculation. Returns 0 if no valid price.
    @param _asset The address of the asset
    @param _amount The amount of the asset
    @param _shouldRaise If True, raises an error when price feed exists but returns no price
    @return The USD value with 18 decimals
    """
    if _amount == 0 or _asset == empty(address):
        return 0
    price: uint256 = self._getPrice(_asset, _shouldRaise)
    if price == 0:
        return 0
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    return price * _amount // (10 ** decimals)


@view
@external
def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256:
    """
    @notice Calculate the amount of an asset worth a given USD value
    @dev Accounts for asset decimals in calculation. Returns 0 if no valid price.
    @param _asset The address of the asset
    @param _usdValue The USD value to convert to asset amount (18 decimals)
    @param _shouldRaise If True, raises an error when price feed exists but returns no price
    @return The amount of the asset
    """
    if _usdValue == 0 or _asset == empty(address):
        return 0
    price: uint256 = self._getPrice(_asset, _shouldRaise)
    if price == 0:
        return 0
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    return _usdValue * (10 ** decimals) // price


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    """
    @notice Check if any oracle partner has a price feed for the asset
    @dev Iterates through all registered oracle partners
    @param _asset The address of the asset to check
    @return True if a price feed exists, False otherwise
    """
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
def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256:
    """
    @notice Calculate the USD value of a given amount of ETH
    @dev Uses ETH price feed. Returns 0 if no valid price.
    @param _amount The amount of ETH in wei
    @param _shouldRaise If True, raises an error when price feed exists but returns no price
    @return The USD value with 18 decimals
    """
    if _amount == 0:
        return 0
    return self._getPrice(ETH, _shouldRaise) * _amount // (10 ** 18)


@view
@external
def getEthAmount(_usdValue: uint256, _shouldRaise: bool = False) -> uint256:
    """
    @notice Calculate the amount of ETH worth a given USD value
    @dev Uses ETH price feed. Returns 0 if no valid price.
    @param _usdValue The USD value to convert to ETH amount (18 decimals)
    @param _shouldRaise If True, raises an error when price feed exists but returns no price
    @return The amount of ETH in wei
    """
    if _usdValue == 0:
        return 0
    price: uint256 = self._getPrice(ETH, _shouldRaise)
    if price == 0:
        return 0
    return _usdValue * (10 ** 18) // price


###########################
# Register Oracle Partner #
###########################


@view
@external
def isValidNewOraclePartnerAddr(_addr: address) -> bool:
    """
    @notice Check if an address can be registered as a new oracle partner
    @dev Validates address is non-zero, is a contract, and hasn't been registered before
    @param _addr The address to validate
    @return True if address can be registered as new oracle partner, False otherwise
    """
    return self._isValidNewOraclePartnerAddr(_addr)


@view
@internal
def _isValidNewOraclePartnerAddr(_addr: address) -> bool:
    if _addr == empty(address) or not _addr.is_contract:
        return False
    return self.oraclePartnerAddrToId[_addr] == 0


@external
def registerNewOraclePartner(_addr: address, _description: String[64]) -> uint256:
    """
    @notice Register a new oracle partner contract in the registry
    @dev Sets oracle partner ID on the contract.
    @param _addr The address of the oracle partner contract to register
    @param _description A brief description of the oracle partner's functionality
    @return The assigned oracle partner ID if registration successful, 0 if failed
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

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

    log NewOraclePartnerRegistered(addr=_addr, oraclePartnerId=oraclePartnerId, description=_description)
    return oraclePartnerId


#########################
# Update Oracle Partner #
#########################


@view
@external
def isValidOraclePartnerUpdate(_oracleId: uint256, _newAddr: address) -> bool:
    """
    @notice Check if an oracle partner update operation would be valid
    @dev Validates oracle ID exists and new address is valid
    @param _oracleId The ID of the oracle partner to update
    @param _newAddr The proposed new address for the oracle partner
    @return True if update would be valid, False otherwise
    """
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
    """
    @notice Update the address of an existing oracle partner
    @dev Updates version and timestamp.
    @param _oracleId The ID of the oracle partner to update
    @param _newAddr The new address for the oracle partner
    @return True if update successful, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

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

    log OraclePartnerAddrUpdated(newAddr=_newAddr, prevAddr=prevAddr, oraclePartnerId=_oracleId, version=data.version, description=data.description)
    return True


##########################
# Disable Oracle Partner #
##########################


@view
@external
def isValidOraclePartnerDisable(_oracleId: uint256) -> bool:
    """
    @notice Check if an oracle partner can be disabled
    @dev Validates oracle ID exists and has a non-empty address
    @param _oracleId The ID of the oracle partner to check
    @return True if oracle partner can be disabled, False otherwise
    """
    return self._isValidOraclePartnerDisable(_oracleId, self.oraclePartnerInfo[_oracleId].addr)


@view
@internal
def _isValidOraclePartnerDisable(_oracleId: uint256, _prevAddr: address) -> bool:
    if not self._isValidOraclePartnerId(_oracleId):
        return False
    return _prevAddr != empty(address)


@external
def disableOraclePartnerAddr(_oracleId: uint256) -> bool:
    """
    @notice Disable an oracle partner by setting its address to empty
    @dev Updates version and timestamp.
    @param _oracleId The ID of the oracle partner to disable
    @return True if disable successful, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

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

    log OraclePartnerAddrDisabled(prevAddr=prevAddr, oraclePartnerId=_oracleId, version=data.version, description=data.description)
    return True


############################
# Priority Oracle Partners #
############################


@view 
@external 
def getPriorityOraclePartnerIds() -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    """
    @notice Get the list of priority oracle partner IDs
    @dev Returns ordered list of IDs that are checked first for prices
    @return Array of oracle partner IDs in priority order
    """
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
    """
    @notice Check if a list of priority oracle partner IDs is valid
    @dev Validates IDs exist and are not duplicated
    @param _priorityIds Array of oracle partner IDs to validate
    @return True if all IDs are valid, False otherwise
    """
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePriorityOraclePartnerIds(_priorityIds)
    return self._areValidPriorityOraclePartnerIds(priorityIds)


@view
@internal
def _areValidPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    return len(_priorityIds) != 0


@external
def setPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    """
    @notice Set the list of priority oracle partner IDs
    @dev Only callable by governor when registry is activated
    @param _priorityIds Array of oracle partner IDs in desired priority order
    @return True if priority list was set successfully, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePriorityOraclePartnerIds(_priorityIds)
    if not self._areValidPriorityOraclePartnerIds(priorityIds):
        return False

    self.priorityOraclePartnerIds = priorityIds
    log PriorityOraclePartnerIdsModified(numIds=len(priorityIds))
    return True


##############
# Stale Time #
##############


@view
@external
def isValidStaleTime(_staleTime: uint256) -> bool:
    """
    @notice Check if a stale time value is valid
    @dev Validates against minimum and maximum allowed stale times
    @param _staleTime The stale time in seconds to validate
    @return True if stale time is valid, False otherwise
    """
    return self._isValidStaleTime(_staleTime)


@view
@internal
def _isValidStaleTime(_staleTime: uint256) -> bool:
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME


@external
def setStaleTime(_staleTime: uint256) -> bool:
    """
    @notice Set the stale time for price feeds
    @dev Only callable by governor when registry is activated
    @param _staleTime The stale time in seconds
    @return True if stale time was set successfully, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidStaleTime(_staleTime):
        return False

    self.staleTime = _staleTime
    log StaleTimeSet(staleTime=_staleTime)
    return True


#################
# Views / Utils #
#################


# is valid


@view
@external
def isValidOraclePartnerAddr(_addr: address) -> bool:
    """
    @notice Check if an address is a registered oracle partner
    @dev Returns true if address has a non-zero oracle partner ID
    @param _addr The address to check
    @return True if address is a registered oracle partner, False otherwise
    """
    return self.oraclePartnerAddrToId[_addr] != 0


@view
@external
def isValidOraclePartnerId(_oracleId: uint256) -> bool:
    """
    @notice Check if an oracle partner ID is valid
    @dev ID must be non-zero and less than total number of oracle partners
    @param _oracleId The ID to check
    @return True if ID is valid, False otherwise
    """
    return self._isValidOraclePartnerId(_oracleId)


@view
@internal
def _isValidOraclePartnerId(_oracleId: uint256) -> bool:
    return _oracleId != 0 and _oracleId < self.numOraclePartners


# oracle partner getters


@view
@external
def getOraclePartnerId(_addr: address) -> uint256:
    """
    @notice Get the ID of an oracle partner from its address
    @dev Returns 0 if address is not registered
    @param _addr The address to query
    @return The oracle partner ID associated with the address
    """
    return self.oraclePartnerAddrToId[_addr]


@view
@external
def getOraclePartnerAddr(_oracleId: uint256) -> address:
    """
    @notice Get the address of an oracle partner from its ID
    @dev Returns empty address if ID is invalid or partner is disabled
    @param _oracleId The ID to query
    @return The address associated with the oracle partner ID
    """
    return self.oraclePartnerInfo[_oracleId].addr


@view
@external
def getOraclePartnerInfo(_oracleId: uint256) -> OraclePartnerInfo:
    """
    @notice Get all information about an oracle partner
    @dev Returns complete OraclePartnerInfo struct including address, version, timestamp and description
    @param _oracleId The ID to query
    @return OraclePartnerInfo struct containing all oracle partner information
    """
    return self.oraclePartnerInfo[_oracleId]


@view
@external
def getOraclePartnerDescription(_oracleId: uint256) -> String[64]:
    """
    @notice Get the description of an oracle partner
    @dev Returns empty string if ID is invalid
    @param _oracleId The ID to query
    @return The description associated with the oracle partner ID
    """
    return self.oraclePartnerInfo[_oracleId].description


# high level


@view
@external
def getNumOraclePartners() -> uint256:
    """
    @notice Get the total number of registered oracle partners
    @dev Returns number of partners minus 1 since indexing starts at 1
    @return The total number of registered oracle partners
    """
    return self.numOraclePartners - 1


@view
@external
def getLastOraclePartnerAddr() -> address:
    """
    @notice Get the address of the most recently registered oracle partner
    @dev Returns the address at index (numOraclePartners - 1)
    @return The address of the last registered oracle partner
    """
    lastIndex: uint256 = self.numOraclePartners - 1
    return self.oraclePartnerInfo[lastIndex].addr


@view
@external
def getLastOraclePartnerId() -> uint256:
    """
    @notice Get the ID of the most recently registered oracle partner
    @dev Returns numOraclePartners - 1 since indexing starts at 1
    @return The ID of the last registered oracle partner
    """
    return self.numOraclePartners - 1
