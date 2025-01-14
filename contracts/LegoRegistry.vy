# @version 0.3.10

interface LegoPartner:
    def setLegoId(_legoId: uint256) -> bool: nonpayable

struct LegoInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]

event NewLegoRegistered:
    addr: indexed(address)
    legoId: uint256
    description: String[64]

event LegoAddrUpdated:
    newAddr: indexed(address)
    prevAddr: indexed(address)
    legoId: uint256
    version: uint256
    description: String[64]

event LegoAddrDisabled:
    prevAddr: indexed(address)
    legoId: uint256
    version: uint256
    description: String[64]

event LegoRegistryGovernorSet:
    governor: indexed(address)

event LegoRegistryActivated:
    isActivated: bool

# core
legoInfo: public(HashMap[uint256, LegoInfo])
legoAddrToId: public(HashMap[address, uint256])
numLegos: public(uint256)

# config
governor: public(address)
isActivated: public(bool)


@external
def __init__(_governor: address):
    assert _governor != empty(address) # dev: invalid governor
    self.governor = _governor
    self.isActivated = True

    # start at 1 index
    self.numLegos = 1


#################
# Register Lego #
#################


@view
@external
def isValidNewLegoAddr(_addr: address) -> bool:
    return self._isValidNewLegoAddr(_addr)


@view
@internal
def _isValidNewLegoAddr(_addr: address) -> bool:
    if _addr == empty(address) or not _addr.is_contract:
        return False
    return self.legoAddrToId[_addr] == 0


@external
def registerNewLego(_addr: address, _description: String[64]) -> uint256:
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms

    if not self._isValidNewLegoAddr(_addr):
        return 0

    data: LegoInfo = LegoInfo({
        addr: _addr,
        version: 1,
        lastModified: block.timestamp,
        description: _description,
    })

    legoId: uint256 = self.numLegos
    self.legoAddrToId[_addr] = legoId
    self.numLegos = legoId + 1
    self.legoInfo[legoId] = data
    assert LegoPartner(_addr).setLegoId(legoId) # dev: set id failed

    log NewLegoRegistered(_addr, legoId, _description)
    return legoId


###############
# Update Lego #
###############


@view
@external
def isValidLegoUpdate(_legoId: uint256, _newAddr: address) -> bool:
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
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms

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
    assert LegoPartner(_newAddr).setLegoId(_legoId) # dev: set id failed

    # handle previous addr
    if prevAddr != empty(address):
        self.legoAddrToId[prevAddr] = 0

    log LegoAddrUpdated(_newAddr, prevAddr, _legoId, data.version, data.description)
    return True


################
# Disable Lego #
################


@view
@external
def isValidLegoDisable(_legoId: uint256) -> bool:
    return self._isValidLegoDisable(_legoId, self.legoInfo[_legoId].addr)


@view
@internal
def _isValidLegoDisable(_legoId: uint256, _prevAddr: address) -> bool:
    if not self._isValidLegoId(_legoId):
        return False
    return _prevAddr != empty(address)


@external
def disableLegoAddr(_legoId: uint256) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms

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

    log LegoAddrDisabled(prevAddr, _legoId, data.version, data.description)
    return True


#################
# Views / Utils #
#################


# is valid


@view
@external
def isValidLegoAddr(_addr: address) -> bool:
    return self.legoAddrToId[_addr] != 0


@view
@external
def isValidLegoId(_legoId: uint256) -> bool:
    return self._isValidLegoId(_legoId)


@view
@internal
def _isValidLegoId(_legoId: uint256) -> bool:
    return _legoId != 0 and _legoId < self.numLegos


# lego getters


@view
@external
def getLegoId(_addr: address) -> uint256:
    return self.legoAddrToId[_addr]


@view
@external
def getLegoAddr(_legoId: uint256) -> address:
    return self.legoInfo[_legoId].addr


@view
@external
def getLegoInfo(_legoId: uint256) -> LegoInfo:
    return self.legoInfo[_legoId]


@view
@external
def getLegoDescription(_legoId: uint256) -> String[64]:
    return self.legoInfo[_legoId].description


# high level


@view
@external
def getNumLegos() -> uint256:
    return self.numLegos - 1


@view
@external
def getLastLegoAddr() -> address:
    lastIndex: uint256 = self.numLegos - 1
    return self.legoInfo[lastIndex].addr


@view
@external
def getLastLegoId() -> uint256:
    return self.numLegos - 1


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
    log LegoRegistryGovernorSet(_newGovernor)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == self.governor # dev: no perms
    self.isActivated = _shouldActivate
    log LegoRegistryActivated(_shouldActivate)
