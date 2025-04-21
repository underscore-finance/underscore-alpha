import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS

MIN_OWNER_CHANGE_DELAY = 21_600  # 12 hours on Base (2 seconds per block)
MAX_OWNER_CHANGE_DELAY = 302_400  # 7 days on Base (2 seconds per block)


@pytest.fixture(scope="module")
def new_owner():
    return boa.env.generate_address()


#########
# Tests #
#########


def test_initial_ownership(ai_wallet_config, owner):
    """Test initial ownership setup"""
    assert ai_wallet_config.owner() == owner
    assert ai_wallet_config.ownershipChangeDelay() == MIN_OWNER_CHANGE_DELAY


def test_ownership_change_delay(ai_wallet_config, owner, sally):
    """Test setting ownership change delay"""
    # Test setting valid delay
    new_delay = MIN_OWNER_CHANGE_DELAY + 1000
    ai_wallet_config.setOwnershipChangeDelay(new_delay, sender=owner)

    log = filter_logs(ai_wallet_config, "OwnershipChangeDelaySet")[0]
    assert log.delayBlocks == new_delay

    assert ai_wallet_config.ownershipChangeDelay() == new_delay

    # Test setting delay below minimum
    with boa.reverts("invalid delay"):
        ai_wallet_config.setOwnershipChangeDelay(MIN_OWNER_CHANGE_DELAY - 1, sender=owner)

    # Test setting delay above maximum
    with boa.reverts("invalid delay"):
        ai_wallet_config.setOwnershipChangeDelay(MAX_OWNER_CHANGE_DELAY + 1, sender=owner)

    # Test setting delay by non-owner
    with boa.reverts("no perms"):
        ai_wallet_config.setOwnershipChangeDelay(new_delay, sender=sally)


def test_ownership_change_process(ai_wallet_config, owner, new_owner):
    """Test complete ownership change process"""
    delay = ai_wallet_config.ownershipChangeDelay()
    current_block = boa.env.evm.patch.block_number

    # Initiate ownership change
    ai_wallet_config.changeOwnership(new_owner, sender=owner)
    log = filter_logs(ai_wallet_config, "OwnershipChangeInitiated")[0]
    assert log.prevOwner == owner
    assert log.newOwner == new_owner
    assert log.confirmBlock == current_block + delay

    # Check pending owner data
    pending_owner = ai_wallet_config.pendingOwner()
    assert pending_owner.newOwner == new_owner  # newOwner
    assert pending_owner.initiatedBlock == current_block  # initiatedBlock
    assert pending_owner.confirmBlock == current_block + delay  # confirmBlock

    # Try to confirm before delay
    with boa.reverts("time delay not reached"):
        ai_wallet_config.confirmOwnershipChange(sender=new_owner)

    # Advance blocks to pass delay
    boa.env.time_travel(blocks=delay)

    # Confirm ownership change
    ai_wallet_config.confirmOwnershipChange(sender=new_owner)
    log = filter_logs(ai_wallet_config, "OwnershipChangeConfirmed")[0]
    assert log.prevOwner == owner
    assert log.newOwner == new_owner
    assert log.initiatedBlock == pending_owner.initiatedBlock
    assert log.confirmBlock == pending_owner.confirmBlock

    # Verify ownership change
    assert ai_wallet_config.owner() == new_owner

    pending_owner = ai_wallet_config.pendingOwner()
    assert pending_owner.newOwner == ZERO_ADDRESS
    assert pending_owner.initiatedBlock == 0
    assert pending_owner.confirmBlock == 0


def test_ownership_change_restrictions(ai_wallet_config, owner, new_owner, sally):
    """Test ownership change restrictions"""
    # Test initiating change by non-owner
    with boa.reverts("no perms"):
        ai_wallet_config.changeOwnership(new_owner, sender=sally)

    # Test invalid new owner addresses
    with boa.reverts("invalid new owner"):
        ai_wallet_config.changeOwnership(ZERO_ADDRESS, sender=owner)
    with boa.reverts("invalid new owner"):
        ai_wallet_config.changeOwnership(owner, sender=owner)

    # Test confirming without pending change
    with boa.reverts("no pending owner"):
        ai_wallet_config.confirmOwnershipChange(sender=new_owner)

    # Initiate valid change
    ai_wallet_config.changeOwnership(new_owner, sender=owner)

    boa.env.time_travel(blocks=ai_wallet_config.ownershipChangeDelay())

    # Test confirming by wrong address
    with boa.reverts("only new owner can confirm"):
        ai_wallet_config.confirmOwnershipChange(sender=owner)
    with boa.reverts("only new owner can confirm"):
        ai_wallet_config.confirmOwnershipChange(sender=sally)


def test_ownership_change_cancellation(ai_wallet_config, owner, new_owner, sally):
    """Test cancelling ownership change"""
    delay = ai_wallet_config.ownershipChangeDelay()

    # Test cancelling without pending change
    with boa.reverts("no pending change"):
        ai_wallet_config.cancelOwnershipChange(sender=owner)

    # Initiate ownership change
    ai_wallet_config.changeOwnership(new_owner, sender=owner)
    pending_owner = ai_wallet_config.pendingOwner()

    # Test cancelling by non-owner
    with boa.reverts("no perms (only owner or governor)"):
        ai_wallet_config.cancelOwnershipChange(sender=sally)

    # Cancel ownership change
    ai_wallet_config.cancelOwnershipChange(sender=owner)
    log = filter_logs(ai_wallet_config, "OwnershipChangeCancelled")[0]
    assert log.cancelledOwner == new_owner
    assert log.initiatedBlock == pending_owner.initiatedBlock
    assert log.confirmBlock == pending_owner.confirmBlock

    # Verify cancellation
    assert ai_wallet_config.owner() == owner
    pending_owner = ai_wallet_config.pendingOwner()
    assert pending_owner.newOwner == ZERO_ADDRESS
    assert pending_owner.initiatedBlock == 0
    assert pending_owner.confirmBlock == 0

    # Verify cannot confirm after cancellation
    boa.env.time_travel(blocks=delay)
    with boa.reverts("no pending owner"):
        ai_wallet_config.confirmOwnershipChange(sender=new_owner)


def test_multiple_ownership_changes(ai_wallet_config, owner, new_owner, sally):
    """Test multiple ownership changes"""
    first_new_owner = new_owner
    second_new_owner = sally
    delay = ai_wallet_config.ownershipChangeDelay()

    # Initiate first ownership change
    ai_wallet_config.changeOwnership(first_new_owner, sender=owner)
    init_log = filter_logs(ai_wallet_config, "OwnershipChangeInitiated")[0]
    assert init_log.prevOwner == owner
    assert init_log.newOwner == first_new_owner

    # Complete first change
    boa.env.time_travel(blocks=delay)
    ai_wallet_config.confirmOwnershipChange(sender=first_new_owner)
    confirm_log = filter_logs(ai_wallet_config, "OwnershipChangeConfirmed")[0]
    assert confirm_log.prevOwner == owner
    assert confirm_log.newOwner == first_new_owner
    assert ai_wallet_config.owner() == first_new_owner

    # Initiate second ownership change
    ai_wallet_config.changeOwnership(second_new_owner, sender=first_new_owner)
    init_log = filter_logs(ai_wallet_config, "OwnershipChangeInitiated")[0]
    assert init_log.prevOwner == first_new_owner
    assert init_log.newOwner == second_new_owner

    # Complete second change
    boa.env.time_travel(blocks=delay)
    ai_wallet_config.confirmOwnershipChange(sender=second_new_owner)
    confirm_log = filter_logs(ai_wallet_config, "OwnershipChangeConfirmed")[0]
    assert confirm_log.prevOwner == first_new_owner
    assert confirm_log.newOwner == second_new_owner
    assert ai_wallet_config.owner() == second_new_owner
