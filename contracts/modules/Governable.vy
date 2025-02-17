# @version 0.4.0

interface AddyRegistry:
    def governor() -> address: view

event LocalGovernorSet:
    addr: indexed(address)

localGovernor: public(address)
ADDY_REGISTRY: immutable(address)


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry


#############
# Utilities #
#############


@view
@external
def isGovernor(_address: address) -> bool:
    return self._isGovernor(_address)


@view
@internal
def _isGovernor(_address: address) -> bool:
    return _address in [self.localGovernor, staticcall AddyRegistry(ADDY_REGISTRY).governor()]


################
# Set Governor #
################


@view
@external 
def isValidLocalGovernor(_newGovernor: address) -> bool:
    mainGovernor: address = staticcall AddyRegistry(ADDY_REGISTRY).governor()
    return self._isValidLocalGovernor(_newGovernor, mainGovernor)


@view
@internal 
def _isValidLocalGovernor(_newGovernor: address, _mainGovernor: address) -> bool:
    if _newGovernor == _mainGovernor:
        return False
    if _newGovernor != empty(address) and not _newGovernor.is_contract:
        return False
    return _newGovernor != self.localGovernor


@external
def setLocalGovernor(_newGovernor: address) -> bool:
    mainGovernor: address = staticcall AddyRegistry(ADDY_REGISTRY).governor()
    assert msg.sender == mainGovernor # dev: no perms
    if not self._isValidLocalGovernor(_newGovernor, mainGovernor):
        return False
    self.localGovernor = _newGovernor
    log LocalGovernorSet(_newGovernor)
    return True