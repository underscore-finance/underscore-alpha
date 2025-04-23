# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

interface AgentFactory:
    def canCancelCriticalAction(_addr: address) -> bool: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct PendingOwner:
    newOwner: address
    initiatedBlock: uint256
    confirmBlock: uint256

event OwnershipChangeInitiated:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    confirmBlock: uint256

event OwnershipChangeConfirmed:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event OwnershipChangeCancelled:
    cancelledOwner: indexed(address)
    cancelledBy: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event OwnershipChangeDelaySet:
    delayBlocks: uint256

# owner
owner: public(address) # owner of the wallet
pendingOwner: public(PendingOwner) # pending owner of the wallet
ownershipChangeDelay: public(uint256) # num blocks to wait before owner can be changed

MIN_OWNER_CHANGE_DELAY: public(immutable(uint256))
MAX_OWNER_CHANGE_DELAY: public(immutable(uint256))
_ADDY_REGISTRY: public(immutable(address))

AGENT_FACTORY_ID: constant(uint256) = 1


@deploy
def __init__(
    _owner: address,
    _addyRegistry: address,
    _minOwnerChangeDelay: uint256,
    _maxOwnerChangeDelay: uint256,
):
    assert empty(address) not in [_owner, _addyRegistry] # dev: invalid addrs
    self.owner = _owner
    _ADDY_REGISTRY = _addyRegistry

    assert _minOwnerChangeDelay < _maxOwnerChangeDelay # dev: invalid delay
    MIN_OWNER_CHANGE_DELAY = _minOwnerChangeDelay
    MAX_OWNER_CHANGE_DELAY = _maxOwnerChangeDelay
    self.ownershipChangeDelay = _minOwnerChangeDelay


####################
# Ownership Change #
####################


@view
@external
def hasPendingOwnerChange() -> bool:
    """
    @notice Checks if there is a pending ownership change
    @return bool True if there is a pending ownership change, false otherwise
    """
    return self._hasPendingOwnerChange()


@view
@internal
def _hasPendingOwnerChange() -> bool:
    return self.pendingOwner.confirmBlock != 0


@external
def changeOwnership(_newOwner: address):
    """
    @notice Initiates a new ownership change
    @dev Can only be called by the current owner
    @param _newOwner The address of the new owner
    """
    currentOwner: address = self.owner
    assert msg.sender == currentOwner # dev: no perms
    assert _newOwner not in [empty(address), currentOwner] # dev: invalid new owner

    confirmBlock: uint256 = block.number + self.ownershipChangeDelay
    self.pendingOwner = PendingOwner(
        newOwner= _newOwner,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log OwnershipChangeInitiated(prevOwner=currentOwner, newOwner=_newOwner, confirmBlock=confirmBlock)


@external
def confirmOwnershipChange():
    """
    @notice Confirms the ownership change
    @dev Can only be called by the new owner
    """
    data: PendingOwner = self.pendingOwner
    assert data.newOwner != empty(address) # dev: no pending owner
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached
    assert msg.sender == data.newOwner # dev: only new owner can confirm

    prevOwner: address = self.owner
    self.owner = data.newOwner
    self.pendingOwner = empty(PendingOwner)
    log OwnershipChangeConfirmed(prevOwner=prevOwner, newOwner=data.newOwner, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def cancelOwnershipChange():
    """
    @notice Cancels the ownership change
    @dev Can only be called by the current owner or governance
    """
    agentFactory: address = staticcall AddyRegistry(_ADDY_REGISTRY).getAddy(AGENT_FACTORY_ID)
    assert msg.sender == self.owner or staticcall AgentFactory(agentFactory).canCancelCriticalAction(msg.sender) # dev: no perms (only owner or governance)

    data: PendingOwner = self.pendingOwner
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingOwner = empty(PendingOwner)
    log OwnershipChangeCancelled(cancelledOwner=data.newOwner, cancelledBy=msg.sender, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def setOwnershipChangeDelay(_numBlocks: uint256):
    """
    @notice Sets the ownership change delay
    @dev Can only be called by the owner
    @param _numBlocks The number of blocks to wait before ownership can be changed
    """
    assert msg.sender == self.owner # dev: no perms
    assert _numBlocks >= MIN_OWNER_CHANGE_DELAY and _numBlocks <= MAX_OWNER_CHANGE_DELAY # dev: invalid delay
    self.ownershipChangeDelay = _numBlocks
    log OwnershipChangeDelaySet(delayBlocks=_numBlocks)