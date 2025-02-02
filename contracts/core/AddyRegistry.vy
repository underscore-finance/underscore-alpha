# @version 0.4.0

struct AddyInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]

event NewAddyRegistered:
    addr: indexed(address)
    addyId: uint256
    description: String[64]

event AddyIdUpdated:
    newAddr: indexed(address)
    prevAddy: indexed(address)
    addyId: uint256
    version: uint256
    description: String[64]

event AddyIdDisabled:
    prevAddy: indexed(address)
    addyId: uint256
    version: uint256
    description: String[64]

event AddyRegistryGovernorSet:
    governor: indexed(address)

event AddyRegistryActivated:
    isActivated: bool

# core
addyInfo: public(HashMap[uint256, AddyInfo])
addyToId: public(HashMap[address, uint256])
numAddys: public(uint256)

# config
governor: public(address)
isActivated: public(bool)


@deploy
def __init__(_governor: address):
    assert _governor != empty(address) # dev: invalid governor
    self.governor = _governor
    self.isActivated = True

    # start at 1 index
    self.numAddys = 1


#################
# Register Addy #
#################


@view
@external
def isValidNewAddy(_addy: address) -> bool:
    """
    @notice Check if an address can be registered as a new core contract
    @dev Validates address is non-zero, is a contract, and hasn't been registered before
    @param _addy The address to validate
    @return True if address can be registered as new core contract, False otherwise
    """
    return self._isValidNewAddy(_addy)


@view
@internal
def _isValidNewAddy(_addy: address) -> bool:
    if _addy == empty(address) or not _addy.is_contract:
        return False
    return self.addyToId[_addy] == 0


@external
def registerNewAddy(_addy: address, _description: String[64]) -> uint256:
    """
    @notice Register a new core contract address in the registry
    @dev Only callable by governor when registry is activated
    @param _addy The address of the contract to register
    @param _description A brief description of the contract's functionality
    @return The assigned ID if registration successful, 0 if failed
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms

    if not self._isValidNewAddy(_addy):
        return 0

    data: AddyInfo = AddyInfo(
        addr=_addy,
        version=1,
        lastModified=block.timestamp,
        description=_description,
    )

    addyId: uint256 = self.numAddys
    self.addyToId[_addy] = addyId
    self.numAddys = addyId + 1
    self.addyInfo[addyId] = data

    log NewAddyRegistered(_addy, addyId, _description)
    return addyId


###############
# Update Addy #
###############


@view
@external
def isValidAddyUpdate(_addyId: uint256, _newAddy: address) -> bool:
    """
    @notice Check if a core contract update operation would be valid
    @dev Validates ID exists and new address is valid
    @param _addyId The ID of the contract to update
    @param _newAddy The proposed new address for the contract
    @return True if update would be valid, False otherwise
    """
    return self._isValidAddyUpdate(_addyId, _newAddy, self.addyInfo[_addyId].addr)


@view
@internal
def _isValidAddyUpdate(_addyId: uint256, _newAddy: address, _prevAddy: address) -> bool:
    if not self._isValidAddyId(_addyId):
        return False
    if not self._isValidNewAddy(_newAddy):
        return False
    return _newAddy != _prevAddy


@external
def updateAddy(_addyId: uint256, _newAddy: address) -> bool:
    """
    @notice Update the address of an existing core contract
    @dev Only callable by governor when registry is activated. Updates version and timestamp.
    @param _addyId The ID of the contract to update
    @param _newAddy The new address for the contract
    @return True if update successful, False otherwise
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms

    data: AddyInfo = self.addyInfo[_addyId]
    prevAddy: address = data.addr # needed for later

    if not self._isValidAddyUpdate(_addyId, _newAddy, prevAddy):
        return False

    # save new data
    data.addr = _newAddy
    data.lastModified = block.timestamp
    data.version += 1
    self.addyInfo[_addyId] = data
    self.addyToId[_newAddy] = _addyId

    # handle previous addr
    if prevAddy != empty(address):
        self.addyToId[prevAddy] = 0

    log AddyIdUpdated(_newAddy, prevAddy, _addyId, data.version, data.description)
    return True


################
# Disable Addy #
################


@view
@external
def isValidAddyDisable(_addyId: uint256) -> bool:
    """
    @notice Check if a core contract can be disabled
    @dev Validates ID exists and has a non-empty address
    @param _addyId The ID of the contract to check
    @return True if contract can be disabled, False otherwise
    """
    return self._isValidAddyDisable(_addyId, self.addyInfo[_addyId].addr)


@view
@internal
def _isValidAddyDisable(_addyId: uint256, _prevAddy: address) -> bool:
    if not self._isValidAddyId(_addyId):
        return False
    return _prevAddy != empty(address)


@external
def disableAddy(_addyId: uint256) -> bool:
    """
    @notice Disable a core contract by setting its address to empty
    @dev Only callable by governor when registry is activated. Updates version and timestamp.
    @param _addyId The ID of the contract to disable
    @return True if disable successful, False otherwise
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms

    data: AddyInfo = self.addyInfo[_addyId]
    prevAddy: address = data.addr # needed for later

    if not self._isValidAddyDisable(_addyId, prevAddy):
        return False

    # save new data
    data.addr = empty(address)
    data.lastModified = block.timestamp
    data.version += 1
    self.addyInfo[_addyId] = data
    self.addyToId[prevAddy] = 0

    log AddyIdDisabled(prevAddy, _addyId, data.version, data.description)
    return True


#################
# Views / Utils #
#################


# is valid


@view
@external
def isValidAddy(_addy: address) -> bool:
    """
    @notice Check if an address is a registered core contract
    @dev Returns true if address has a non-zero ID
    @param _addy The address to check
    @return True if address is a registered core contract, False otherwise
    """
    return self.addyToId[_addy] != 0


@view
@external
def isValidAddyId(_addyId: uint256) -> bool:
    """
    @notice Check if a core contract ID is valid
    @dev ID must be non-zero and less than total number of contracts
    @param _addyId The ID to check
    @return True if ID is valid, False otherwise
    """
    return self._isValidAddyId(_addyId)


@view
@internal
def _isValidAddyId(_addyId: uint256) -> bool:
    return _addyId != 0 and _addyId < self.numAddys


# addy getters


@view
@external
def getAddyId(_addy: address) -> uint256:
    """
    @notice Get the ID of a core contract from its address
    @dev Returns 0 if address is not registered
    @param _addy The address to query
    @return The ID associated with the address
    """
    return self.addyToId[_addy]


@view
@external
def getAddy(_addyId: uint256) -> address:
    """
    @notice Get the address of a core contract from its ID
    @dev Returns empty address if ID is invalid or contract is disabled
    @param _addyId The ID to query
    @return The address associated with the ID
    """
    return self.addyInfo[_addyId].addr


@view
@external
def getAddyInfo(_addyId: uint256) -> AddyInfo:
    """
    @notice Get all information about a core contract
    @dev Returns complete AddyInfo struct including address, version, timestamp and description
    @param _addyId The ID to query
    @return AddyInfo struct containing all contract information
    """
    return self.addyInfo[_addyId]


@view
@external
def getAddyDescription(_addyId: uint256) -> String[64]:
    """
    @notice Get the description of a core contract
    @dev Returns empty string if ID is invalid
    @param _addyId The ID to query
    @return The description associated with the ID
    """
    return self.addyInfo[_addyId].description


# high level


@view
@external
def getNumAddys() -> uint256:
    """
    @notice Get the total number of registered core contracts
    @dev Returns number of contracts minus 1 since indexing starts at 1
    @return The total number of registered core contracts
    """
    return self.numAddys - 1


@view
@external
def getLastAddy() -> address:
    """
    @notice Get the address of the most recently registered core contract
    @dev Returns the address at index (numAddys - 1)
    @return The address of the last registered contract
    """
    lastIndex: uint256 = self.numAddys - 1
    return self.addyInfo[lastIndex].addr


@view
@external
def getLastAddyId() -> uint256:
    """
    @notice Get the ID of the most recently registered core contract
    @dev Returns numAddys - 1 since indexing starts at 1
    @return The ID of the last registered contract
    """
    return self.numAddys - 1


################
# Set Governor #
################


@view
@external 
def isValidGovernor(_newGovernor: address) -> bool:
    """
    @notice Check if an address can be set as the new governor
    @dev Address must be a contract and different from current governor
    @param _newGovernor The address to validate
    @return True if address can be set as governor, False otherwise
    """
    return self._isValidGovernor(_newGovernor)


@view
@internal 
def _isValidGovernor(_newGovernor: address) -> bool:
    if not _newGovernor.is_contract or _newGovernor == empty(address):
        return False
    return _newGovernor != self.governor


@external
def setGovernor(_newGovernor: address) -> bool:
    """
    @notice Set a new governor address
    @dev Only callable by current governor when registry is activated
    @param _newGovernor The address to set as governor
    @return True if governor was set successfully, False otherwise
    """
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms
    if not self._isValidGovernor(_newGovernor):
        return False
    self.governor = _newGovernor
    log AddyRegistryGovernorSet(_newGovernor)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    """
    @notice Activate or deactivate the address registry
    @dev Only callable by governor. When deactivated, most functions cannot be called.
    @param _shouldActivate True to activate, False to deactivate
    """
    assert msg.sender == self.governor # dev: no perms
    self.isActivated = _shouldActivate
    log AddyRegistryActivated(_shouldActivate)
