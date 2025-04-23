# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry

from ethereum.ercs import IERC20Detailed
import interfaces.OraclePartnerInterface as OraclePartner

event PriorityOraclePartnerIdsModified:
    numIds: uint256

event StaleTimeSet:
    staleTime: uint256

# custom config
priorityOraclePartnerIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
staleTime: public(uint256)

ETH: public(immutable(address))
MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))

MAX_PRIORITY_PARTNERS: constant(uint256) = 10


@deploy
def __init__(
    _addyRegistry: address,
    _ethAddr: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
    _minOracleChangeDelay: uint256,
    _maxOracleChangeDelay: uint256,
):
    assert empty(address) not in [_addyRegistry, _ethAddr] # dev: invalid addrs

    # initialize gov
    gov.__init__(empty(address), _addyRegistry, 0, 0)

    # initialize registry
    registry.__init__(_minOracleChangeDelay, _maxOracleChangeDelay, "OracleRegistry.vy")

    ETH = _ethAddr
    MIN_STALE_TIME = _minStaleTime
    MAX_STALE_TIME = _maxStaleTime


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
        numSources: uint256 = registry.numAddys
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
    oraclePartner: address = registry._getAddy(_pid)
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
    numSources: uint256 = registry.numAddys
    for id: uint256 in range(1, numSources, bound=max_value(uint256)):
        oraclePartner: address = registry._getAddy(id)
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
    @notice Checks if an address can be registered as a new Oracle Partner
    @dev Validates that the address is a contract and not already registered
    @param _addr The address to validate
    @return True if the address can be registered, False otherwise
    """
    return registry._isValidNewAddy(_addr)


@external
def registerNewOraclePartner(_addr: address, _description: String[64]) -> bool:
    """
    @notice Initiates the registration process for a new Oracle Partner
    @dev Only callable by governor. Sets up a pending registration that requires confirmation after a delay period
    @param _addr The address of the Oracle Partner to register
    @param _description A short description of the Oracle Partner (max 64 characters)
    @return True if the registration was successfully initiated, False if the Oracle Partner is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._registerNewAddy(_addr, _description)


@external
def confirmNewOraclePartnerRegistration(_addr: address) -> uint256:
    """
    @notice Confirms a pending Oracle Partner registration after the required delay period
    @dev Only callable by governor. Finalizes the registration by assigning an ID and setting the Oracle Partner ID
    @param _addr The address of the Oracle Partner to confirm registration for
    @return The assigned ID for the registered Oracle Partner, or 0 if confirmation fails
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    oraclePartnerId: uint256 = registry._confirmNewAddy(_addr)
    if oraclePartnerId != 0:
        assert extcall OraclePartner(_addr).setOraclePartnerId(oraclePartnerId) # dev: set id failed
    return oraclePartnerId


@external
def cancelPendingNewOraclePartner(_addr: address) -> bool:
    """
    @notice Cancels a pending Oracle Partner registration
    @dev Only callable by governor. Removes the pending registration and emits a cancellation event
    @param _addr The address of the Oracle Partner whose pending registration should be cancelled
    @return True if the cancellation was successful, reverts if no pending registration exists
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingNewAddy(_addr)


#########################
# Update Oracle Partner #
#########################


@view
@external
def isValidOraclePartnerUpdate(_oracleId: uint256, _newAddr: address) -> bool:
    """
    @notice Checks if an Oracle Partner address can be updated
    @dev Validates that the Oracle Partner ID exists and the new address is valid
    @param _oracleId The ID of the Oracle Partner to update
    @param _newAddr The new address to set
    @return True if the update is valid, False otherwise
    """
    return registry._isValidAddyUpdate(_oracleId, _newAddr, registry.addyInfo[_oracleId].addr)


@external
def updateOraclePartnerAddr(_oracleId: uint256, _newAddr: address) -> bool:
    """
    @notice Initiates an address update for an existing registered Oracle Partner
    @dev Only callable by governor. Sets up a pending update that requires confirmation after a delay period
    @param _oracleId The ID of the Oracle Partner to update
    @param _newAddr The new address to set for the Oracle Partner
    @return True if the update was successfully initiated, False if the update is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._updateAddyAddr(_oracleId, _newAddr)


@external
def confirmOraclePartnerUpdate(_oracleId: uint256) -> bool:
    """
    @notice Confirms a pending Oracle Partner address update after the required delay period
    @dev Only callable by governor. Finalizes the update by updating the address and setting the Oracle Partner ID
    @param _oracleId The ID of the Oracle Partner to confirm update for
    @return True if the update was successfully confirmed, False if confirmation fails
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    didUpdate: bool = registry._confirmAddyUpdate(_oracleId)
    if didUpdate:
        oraclePartnerAddr: address = registry.addyInfo[_oracleId].addr
        assert extcall OraclePartner(oraclePartnerAddr).setOraclePartnerId(_oracleId) # dev: set id failed
    return didUpdate


@external
def cancelPendingOraclePartnerUpdate(_oracleId: uint256) -> bool:
    """
    @notice Cancels a pending Oracle Partner address update
    @dev Only callable by governor. Removes the pending update and emits a cancellation event
    @param _oracleId The ID of the Oracle Partner whose pending update should be cancelled
    @return True if the cancellation was successful, reverts if no pending update exists
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyUpdate(_oracleId)


##########################
# Disable Oracle Partner #
##########################


@view
@external
def isValidOraclePartnerDisable(_oracleId: uint256) -> bool:
    """
    @notice Checks if an Oracle Partner can be disabled
    @dev Validates that the Oracle Partner ID exists and is not already disabled
    @param _oracleId The ID of the Oracle Partner to check
    @return True if the Oracle Partner can be disabled, False otherwise
    """
    return registry._isValidAddyDisable(_oracleId, registry.addyInfo[_oracleId].addr)


@external
def disableOraclePartnerAddr(_oracleId: uint256) -> bool:
    """
    @notice Initiates the disable process for an existing registered Oracle Partner
    @dev Only callable by governor. Sets up a pending disable that requires confirmation after a delay period
    @param _oracleId The ID of the Oracle Partner to disable
    @return True if the disable was successfully initiated, False if the disable is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._disableAddyAddr(_oracleId)


@external
def confirmOraclePartnerDisable(_oracleId: uint256) -> bool:
    """
    @notice Confirms a pending Oracle Partner disable after the required delay period
    @dev Only callable by governor. Finalizes the disable by clearing the Oracle Partner address
    @param _oracleId The ID of the Oracle Partner to confirm disable for
    @return True if the disable was successfully confirmed, False if confirmation fails
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._confirmAddyDisable(_oracleId)


@external
def cancelPendingOraclePartnerDisable(_oracleId: uint256) -> bool:
    """
    @notice Cancels a pending Oracle Partner disable
    @dev Only callable by governor. Removes the pending disable and emits a cancellation event
    @param _oracleId The ID of the Oracle Partner whose pending disable should be cancelled
    @return True if the cancellation was successful, reverts if no pending disable exists
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyDisable(_oracleId)


#########################
# Oracle Partner Change #
#########################


@external
def setOraclePartnerChangeDelay(_numBlocks: uint256) -> bool:
    """
    @notice Sets the delay period required for Oracle Partner changes
    @dev Only callable by governor. The delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY
    @param _numBlocks The number of blocks to set as the delay period
    @return True if the delay was successfully set, reverts if delay is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@view
@external
def oracleChangeDelay() -> uint256:
    return registry.addyChangeDelay


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
        if not registry._isValidAddyId(pid):
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
    assert gov._canGovern(msg.sender) # dev: no perms

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
    assert gov._canGovern(msg.sender) # dev: no perms

    if not self._isValidStaleTime(_staleTime):
        return False

    self.staleTime = _staleTime
    log StaleTimeSet(staleTime=_staleTime)
    return True


#################
# Views / Utils #
#################


@view
@external
def numOraclePartnersRaw() -> uint256:
    return registry.numAddys


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
    return registry._isValidAddyAddr(_addr)


@view
@external
def isValidOraclePartnerId(_oracleId: uint256) -> bool:
    """
    @notice Check if an oracle partner ID is valid
    @dev ID must be non-zero and less than total number of oracle partners
    @param _oracleId The ID to check
    @return True if ID is valid, False otherwise
    """
    return registry._isValidAddyId(_oracleId)


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
    return registry._getAddyId(_addr)


@view
@external
def getOraclePartnerAddr(_oracleId: uint256) -> address:
    """
    @notice Get the address of an oracle partner from its ID
    @dev Returns empty address if ID is invalid or partner is disabled
    @param _oracleId The ID to query
    @return The address associated with the oracle partner ID
    """
    return registry._getAddy(_oracleId)


@view
@external
def getOraclePartnerInfo(_oracleId: uint256) -> registry.AddyInfo:
    """
    @notice Get all information about an oracle partner
    @dev Returns complete OraclePartnerInfo struct including address, version, timestamp and description
    @param _oracleId The ID to query
    @return OraclePartnerInfo struct containing all oracle partner information
    """
    return registry.addyInfo[_oracleId]


@view
@external
def getOraclePartnerDescription(_oracleId: uint256) -> String[64]:
    """
    @notice Get the description of an oracle partner
    @dev Returns empty string if ID is invalid
    @param _oracleId The ID to query
    @return The description associated with the oracle partner ID
    """
    return registry.addyInfo[_oracleId].description


# high level


@view
@external
def getNumOraclePartners() -> uint256:
    """
    @notice Get the total number of registered oracle partners
    @dev Returns number of partners minus 1 since indexing starts at 1
    @return The total number of registered oracle partners
    """
    return registry._getNumAddys()


@view
@external
def getLastOraclePartnerAddr() -> address:
    """
    @notice Get the address of the most recently registered oracle partner
    @dev Returns the address at index (numOraclePartners - 1)
    @return The address of the last registered oracle partner
    """
    return registry._getLastAddyAddr()


@view
@external
def getLastOraclePartnerId() -> uint256:
    """
    @notice Get the ID of the most recently registered oracle partner
    @dev Returns numOraclePartners - 1 since indexing starts at 1
    @return The ID of the last registered oracle partner
    """
    return registry._getLastAddyId()
