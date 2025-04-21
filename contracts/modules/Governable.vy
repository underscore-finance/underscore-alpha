# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

interface AddyRegistry:
    def governance() -> address: view

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
    return _address in [self.localGovernor, staticcall AddyRegistry(ADDY_REGISTRY).governance()]


################
# Set Governor #
################


@view
@external 
def isValidLocalGovernor(_newGovernor: address) -> bool:
    mainGovernor: address = staticcall AddyRegistry(ADDY_REGISTRY).governance()
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
    mainGovernor: address = staticcall AddyRegistry(ADDY_REGISTRY).governance()
    assert msg.sender == mainGovernor # dev: no perms
    if not self._isValidLocalGovernor(_newGovernor, mainGovernor):
        return False
    self.localGovernor = _newGovernor
    log LocalGovernorSet(addr=_newGovernor)
    return True