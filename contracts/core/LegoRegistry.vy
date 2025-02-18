# @version 0.4.0

initializes: gov
exports: gov.__interface__

from ethereum.ercs import IERC20
import contracts.modules.Governable as gov
from interfaces import LegoYield

interface LegoPartner:
    def setLegoId(_legoId: uint256) -> bool: nonpayable

flag LegoType:
    YIELD_OPP
    DEX

struct LegoInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
    legoType: LegoType

event NewLegoRegistered:
    addr: indexed(address)
    legoId: uint256
    description: String[64]
    legoType: LegoType

event LegoAddrUpdated:
    newAddr: indexed(address)
    prevAddr: indexed(address)
    legoId: uint256
    version: uint256
    description: String[64]
    legoType: LegoType

event LegoAddrDisabled:
    prevAddr: indexed(address)
    legoId: uint256
    version: uint256
    description: String[64]
    legoType: LegoType

event LegoHelperSet:
    helperAddr: indexed(address)

# other
legoHelper: public(address)

# registry core
legoInfo: public(HashMap[uint256, LegoInfo])
legoAddrToId: public(HashMap[address, uint256])
numLegos: public(uint256)

# config
ADDY_REGISTRY: public(immutable(address))

MAX_VAULTS: constant(uint256) = 15


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    gov.__init__(_addyRegistry)
    ADDY_REGISTRY = _addyRegistry

    # start at 1 index
    self.numLegos = 1


#################
# Register Lego #
#################


@view
@external
def isValidNewLegoAddr(_addr: address) -> bool:
    """
    @notice Check if an address can be registered as a new Lego integration
    @dev Validates address is non-zero, is a contract, and hasn't been registered before
    @param _addr The address to validate
    @return True if address can be registered as new Lego, False otherwise
    """
    return self._isValidNewLegoAddr(_addr)


@view
@internal
def _isValidNewLegoAddr(_addr: address) -> bool:
    if _addr == empty(address) or not _addr.is_contract:
        return False
    return self.legoAddrToId[_addr] == 0


@external
def registerNewLego(_addr: address, _description: String[64], _legoType: LegoType) -> uint256:
    """
    @notice Register a new Lego integration contract in the registry
    @dev Only callable by governor. Sets Lego ID on the contract.
    @param _addr The address of the Lego contract to register
    @param _description A brief description of the Lego integration's functionality
    @param _legoType The type of Lego integration
    @return The assigned Lego ID if registration successful, 0 if failed
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidNewLegoAddr(_addr):
        return 0

    data: LegoInfo = LegoInfo(
        addr=_addr,
        version=1,
        lastModified=block.timestamp,
        description=_description,
        legoType=_legoType,
    )

    legoId: uint256 = self.numLegos
    self.legoAddrToId[_addr] = legoId
    self.numLegos = legoId + 1
    self.legoInfo[legoId] = data
    assert extcall LegoPartner(_addr).setLegoId(legoId) # dev: set id failed

    log NewLegoRegistered(_addr, legoId, _description, _legoType)
    return legoId


###############
# Update Lego #
###############


@view
@external
def isValidLegoUpdate(_legoId: uint256, _newAddr: address) -> bool:
    """
    @notice Check if a Lego integration update operation would be valid
    @dev Validates Lego ID exists and new address is valid
    @param _legoId The ID of the Lego integration to update
    @param _newAddr The proposed new address for the Lego integration
    @return True if update would be valid, False otherwise
    """
    return self._isValidLegoUpdate(_legoId, _newAddr, self.legoInfo[_legoId].addr)


@view
@internal
def _isValidLegoUpdate(_legoId: uint256, _newAddr: address, _prevAddr: address) -> bool:
    if not self._isValidLegoId(_legoId):
        return False
    if not self._isValidNewLegoAddr(_newAddr):
        return False
    return _newAddr != _prevAddr


@external
def updateLegoAddr(_legoId: uint256, _newAddr: address) -> bool:
    """
    @notice Update the address of an existing Lego
    @dev Only callable by governor. Updates version and timestamp.
    @param _legoId The ID of the Lego to update
    @param _newAddr The new address for the Lego
    @return True if update successful, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    data: LegoInfo = self.legoInfo[_legoId]
    prevAddr: address = data.addr # needed for later

    if not self._isValidLegoUpdate(_legoId, _newAddr, prevAddr):
        return False

    # save new data
    data.addr = _newAddr
    data.lastModified = block.timestamp
    data.version += 1
    self.legoInfo[_legoId] = data
    self.legoAddrToId[_newAddr] = _legoId
    assert extcall LegoPartner(_newAddr).setLegoId(_legoId) # dev: set id failed

    # handle previous addr
    if prevAddr != empty(address):
        self.legoAddrToId[prevAddr] = 0

    log LegoAddrUpdated(_newAddr, prevAddr, _legoId, data.version, data.description, data.legoType)
    return True


################
# Disable Lego #
################


@view
@external
def isValidLegoDisable(_legoId: uint256) -> bool:
    """
    @notice Check if a Lego can be disabled
    @dev Validates Lego ID exists and has a non-empty address
    @param _legoId The ID of the Lego to check
    @return True if Lego can be disabled, False otherwise
    """
    return self._isValidLegoDisable(_legoId, self.legoInfo[_legoId].addr)


@view
@internal
def _isValidLegoDisable(_legoId: uint256, _prevAddr: address) -> bool:
    if not self._isValidLegoId(_legoId):
        return False
    return _prevAddr != empty(address)


@external
def disableLegoAddr(_legoId: uint256) -> bool:
    """
    @notice Disable a Lego by setting its address to empty
    @dev Only callable by governor. Updates version and timestamp.
    @param _legoId The ID of the Lego to disable
    @return True if disable successful, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    data: LegoInfo = self.legoInfo[_legoId]
    prevAddr: address = data.addr # needed for later

    if not self._isValidLegoDisable(_legoId, prevAddr):
        return False

    # save new data
    data.addr = empty(address)
    data.lastModified = block.timestamp
    data.version += 1
    self.legoInfo[_legoId] = data
    self.legoAddrToId[prevAddr] = 0

    log LegoAddrDisabled(prevAddr, _legoId, data.version, data.description, data.legoType)
    return True


#################
# Views / Utils #
#################


# is valid


@view
@external
def isValidLegoAddr(_addr: address) -> bool:
    """
    @notice Check if an address is a registered Lego integration
    @dev Returns true if address has a non-zero Lego ID
    @param _addr The address to check
    @return True if address is a registered Lego integration, False otherwise
    """
    return self.legoAddrToId[_addr] != 0


@view
@external
def isValidLegoId(_legoId: uint256) -> bool:
    """
    @notice Check if a Lego ID is valid
    @dev ID must be non-zero and less than total number of Legos
    @param _legoId The ID to check
    @return True if ID is valid, False otherwise
    """
    return self._isValidLegoId(_legoId)


@view
@internal
def _isValidLegoId(_legoId: uint256) -> bool:
    return _legoId != 0 and _legoId < self.numLegos


# lego getters


@view
@external
def getLegoId(_addr: address) -> uint256:
    """
    @notice Get the ID of a Lego from its address
    @dev Returns 0 if address is not registered
    @param _addr The address to query
    @return The Lego ID associated with the address
    """
    return self.legoAddrToId[_addr]


@view
@external
def getLegoAddr(_legoId: uint256) -> address:
    """
    @notice Get the address of a Lego from its ID
    @dev Returns empty address if ID is invalid or Lego is disabled
    @param _legoId The ID to query
    @return The address associated with the Lego ID
    """
    return self.legoInfo[_legoId].addr


@view
@external
def getLegoInfo(_legoId: uint256) -> LegoInfo:
    """
    @notice Get all information about a Lego
    @dev Returns complete LegoInfo struct including address, version, timestamp and description
    @param _legoId The ID to query
    @return LegoInfo struct containing all Lego information
    """
    return self.legoInfo[_legoId]


@view
@external
def getLegoDescription(_legoId: uint256) -> String[64]:
    """
    @notice Get the description of a Lego
    @dev Returns empty string if ID is invalid
    @param _legoId The ID to query
    @return The description associated with the Lego ID
    """
    return self.legoInfo[_legoId].description


# high level


@view
@external
def getNumLegos() -> uint256:
    """
    @notice Get the total number of registered Legos
    @dev Returns number of Legos minus 1 since indexing starts at 1
    @return The total number of registered Legos
    """
    return self.numLegos - 1


@view
@external
def getLastLegoAddr() -> address:
    """
    @notice Get the address of the most recently registered Lego
    @dev Returns the address at index (numLegos - 1)
    @return The address of the last registered Lego
    """
    lastIndex: uint256 = self.numLegos - 1
    return self.legoInfo[lastIndex].addr


@view
@external
def getLastLegoId() -> uint256:
    """
    @notice Get the ID of the most recently registered Lego
    @dev Returns numLegos - 1 since indexing starts at 1
    @return The ID of the last registered Lego
    """
    return self.numLegos - 1


# underlying asset


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    """
    @notice Get the underlying asset for a vault token
    @dev Returns empty address if vault token is not registered
    @param _vaultToken The address of the vault token to query
    @return The underlying asset address
    """
    if _vaultToken == empty(address):
        return empty(address)

    numLegos: uint256 = self.numLegos
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = self.legoInfo[i]
        if legoInfo.legoType != LegoType.YIELD_OPP:
            continue

        asset: address = staticcall LegoYield(legoInfo.addr).getUnderlyingAsset(_vaultToken)
        if asset != empty(address):
            return asset

    return empty(address)


@view
@external
def getUnderlyingForUser(_user: address, _asset: address) -> uint256:
    """
    @notice Get the total underlying amount for a user in a given asset
    @dev Returns 0 if user or asset is empty
    @param _user The address of the user to query
    @param _asset The address of the asset to query
    """
    if empty(address) in [_user, _asset]:
        return 0

    totalDeposited: uint256 = 0
    numLegos: uint256 = self.numLegos
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoInfo: LegoInfo = self.legoInfo[i]
        if legoInfo.legoType != LegoType.YIELD_OPP:
            continue

        legoVaultTokens: DynArray[address, MAX_VAULTS] = staticcall LegoYield(legoInfo.addr).getAssetOpportunities(_asset)
        if len(legoVaultTokens) == 0:
            continue

        for vaultToken: address in legoVaultTokens:
            if vaultToken == empty(address):
                continue
            vaultTokenBal: uint256 = staticcall IERC20(vaultToken).balanceOf(_user)
            if vaultTokenBal != 0:
                totalDeposited += staticcall LegoYield(legoInfo.addr).getUnderlyingAmount(vaultToken, vaultTokenBal)

    return totalDeposited


###############
# Lego Helper #
###############


@view
@external 
def isValidLegoHelper(_helperAddr: address) -> bool:
    """
    @notice Check if an address can be set as the Lego helper
    @dev Address must be a contract and different from current helper
    @param _helperAddr The address to validate
    @return True if address can be set as helper, False otherwise
    """
    return self._isValidLegoHelper(_helperAddr)


@view
@internal 
def _isValidLegoHelper(_helperAddr: address) -> bool:
    if not _helperAddr.is_contract or _helperAddr == empty(address):
        return False
    return _helperAddr != self.legoHelper


@external
def setLegoHelper(_helperAddr: address) -> bool:
    """
    @notice Set a new Lego helper address
    @dev Only callable by governor
    @param _helperAddr The address to set as helper
    @return True if helper was set successfully, False otherwise
    """
    assert gov._isGovernor(msg.sender) # dev: no perms

    if not self._isValidLegoHelper(_helperAddr):
        return False
    self.legoHelper = _helperAddr
    log LegoHelperSet(_helperAddr)
    return True

