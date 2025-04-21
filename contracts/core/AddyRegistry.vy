# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

struct AddyInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]

struct PendingGovernance:
    newGov: address
    initiatedBlock: uint256
    confirmBlock: uint256

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

event GovChangeInitiated:
    prevGov: indexed(address)
    newGov: indexed(address)
    confirmBlock: uint256

event GovChangeConfirmed:
    prevGov: indexed(address)
    newGov: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event GovChangeCancelled:
    cancelledGov: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event GovChangeDelaySet:
    delayBlocks: uint256

# core
addyInfo: public(HashMap[uint256, AddyInfo])
addyToId: public(HashMap[address, uint256])
numAddys: public(uint256)

# governance
governance: public(address)
pendingGov: public(PendingGovernance) # pending governance change
govChangeDelay: public(uint256) # num blocks to wait before governance can be changed

MIN_GOV_CHANGE_DELAY: public(immutable(uint256))
MAX_GOV_CHANGE_DELAY: public(immutable(uint256))


@deploy
def __init__(_initialGov: address, _minGovChangeDelay: uint256, _maxGovChangeDelay: uint256):
    assert _initialGov != empty(address) # dev: invalid governance
    self.governance = _initialGov

    assert _minGovChangeDelay < _maxGovChangeDelay # dev: invalid delay
    MIN_GOV_CHANGE_DELAY = _minGovChangeDelay
    MAX_GOV_CHANGE_DELAY = _maxGovChangeDelay
    self.govChangeDelay = _minGovChangeDelay

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
    @dev Only callable by governor
    @param _addy The address of the contract to register
    @param _description A brief description of the contract's functionality
    @return The assigned ID if registration successful, 0 if failed
    """
    assert msg.sender == self.governance # dev: no perms

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

    log NewAddyRegistered(addr=_addy, addyId=addyId, description=_description)
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
    @dev Only callable by governor. Updates version and timestamp.
    @param _addyId The ID of the contract to update
    @param _newAddy The new address for the contract
    @return True if update successful, False otherwise
    """
    assert msg.sender == self.governance # dev: no perms

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

    log AddyIdUpdated(newAddr=_newAddy, prevAddy=prevAddy, addyId=_addyId, version=data.version, description=data.description)
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
    @dev Only callable by governor. Updates version and timestamp.
    @param _addyId The ID of the contract to disable
    @return True if disable successful, False otherwise
    """
    assert msg.sender == self.governance # dev: no perms

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

    log AddyIdDisabled(prevAddy=prevAddy, addyId=_addyId, version=data.version, description=data.description)
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


##############
# Governance #
##############


@view
@external
def hasPendingGovChange() -> bool:
    """
    @notice Checks if there is a pending governance change
    @return bool True if there is a pending governance change, false otherwise
    """
    return self.pendingGov.confirmBlock != 0


@external
def changeGovernance(_newGov: address):
    """
    @notice Initiates a new governance change
    @dev Can only be called by current governance
    @param _newGov The address of new governance
    """
    currentGov: address = self.governance
    assert msg.sender == currentGov # dev: no perms
    assert _newGov not in [empty(address), currentGov] # dev: invalid new governance
    assert _newGov.is_contract # dev: new governance must be a contract

    confirmBlock: uint256 = block.number + self.govChangeDelay
    self.pendingGov = PendingGovernance(
        newGov= _newGov,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log GovChangeInitiated(prevGov=currentGov, newGov=_newGov, confirmBlock=confirmBlock)


@external
def confirmGovernanceChange():
    """
    @notice Confirms the governance change
    @dev Can only be called by the new governance
    """
    data: PendingGovernance = self.pendingGov
    assert data.newGov != empty(address) # dev: no pending governance
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached
    assert msg.sender == data.newGov # dev: only new governance can confirm

    prevGov: address = self.governance
    self.governance = data.newGov
    self.pendingGov = empty(PendingGovernance)
    log GovChangeConfirmed(prevGov=prevGov, newGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def cancelGovernanceChange():
    """
    @notice Cancels the governance change
    @dev Can only be called by the current governance
    """
    assert msg.sender == self.governance # dev: no perms
    data: PendingGovernance = self.pendingGov
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingGov = empty(PendingGovernance)
    log GovChangeCancelled(cancelledGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def setGovernanceChangeDelay(_numBlocks: uint256):
    """
    @notice Sets the governance change delay
    @dev Can only be called by current governance
    @param _numBlocks The number of blocks to wait before governance can be changed
    """
    assert msg.sender == self.governance # dev: no perms
    assert _numBlocks >= MIN_GOV_CHANGE_DELAY and _numBlocks <= MAX_GOV_CHANGE_DELAY # dev: invalid delay
    self.govChangeDelay = _numBlocks
    log GovChangeDelaySet(delayBlocks=_numBlocks)
