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
    return self._isValidNewAddy(_addy)


@view
@internal
def _isValidNewAddy(_addy: address) -> bool:
    if _addy == empty(address) or not _addy.is_contract:
        return False
    return self.addyToId[_addy] == 0


@external
def registerNewAddy(_addy: address, _description: String[64]) -> uint256:
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
    return self._isValidAddyDisable(_addyId, self.addyInfo[_addyId].addr)


@view
@internal
def _isValidAddyDisable(_addyId: uint256, _prevAddy: address) -> bool:
    if not self._isValidAddyId(_addyId):
        return False
    return _prevAddy != empty(address)


@external
def disableAddy(_addyId: uint256) -> bool:
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
    return self.addyToId[_addy] != 0


@view
@external
def isValidAddyId(_addyId: uint256) -> bool:
    return self._isValidAddyId(_addyId)


@view
@internal
def _isValidAddyId(_addyId: uint256) -> bool:
    return _addyId != 0 and _addyId < self.numAddys


# addy getters


@view
@external
def getAddyId(_addy: address) -> uint256:
    return self.addyToId[_addy]


@view
@external
def getAddy(_addyId: uint256) -> address:
    return self.addyInfo[_addyId].addr


@view
@external
def getAddyInfo(_addyId: uint256) -> AddyInfo:
    return self.addyInfo[_addyId]


@view
@external
def getAddyDescription(_addyId: uint256) -> String[64]:
    return self.addyInfo[_addyId].description


# high level


@view
@external
def getNumAddys() -> uint256:
    return self.numAddys - 1


@view
@external
def getLastAddy() -> address:
    lastIndex: uint256 = self.numAddys - 1
    return self.addyInfo[lastIndex].addr


@view
@external
def getLastAddyId() -> uint256:
    return self.numAddys - 1


################
# Set Governor #
################


@view
@external 
def isValidGovernor(_newGovernor: address) -> bool:
    return self._isValidGovernor(_newGovernor)


@view
@internal 
def _isValidGovernor(_newGovernor: address) -> bool:
    if not _newGovernor.is_contract or _newGovernor == empty(address):
        return False
    return _newGovernor != self.governor


@external
def setGovernor(_newGovernor: address) -> bool:
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
    assert msg.sender == self.governor # dev: no perms
    self.isActivated = _shouldActivate
    log AddyRegistryActivated(_shouldActivate)
