import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def new_addy(addy_registry):
    return boa.load("contracts/mock/MockErc20.vy", addy_registry, "Test Addy", "TEST", 18, 10_000_000, name="new_addy")


@pytest.fixture(scope="module")
def new_addy_b(addy_registry):
    return boa.load("contracts/mock/MockErc20.vy", addy_registry, "Test Addy B", "TESTB", 18, 10_000_000, name="new_addy_b")


@pytest.fixture(scope="module")
def new_governor(addy_registry):
    return boa.load("contracts/mock/MockErc20.vy", addy_registry, "Mock Governor", "GOV", 18, 10_000_000, name="new_governor")


#########
# Tests #
#########


def test_register_new_addy(addy_registry, new_addy, governor):
    description = "Test Addy"

    assert addy_registry.isValidNewAddy(new_addy)
    
    numAddys = addy_registry.getNumAddys()

    # Test successful registration
    addy_id = addy_registry.registerNewAddy(new_addy, description, sender=governor)
    assert addy_id != 0

    # Verify event
    log = filter_logs(addy_registry, "NewAddyRegistered")[0]
    assert log.addr == new_addy.address
    assert log.addyId == addy_id
    assert log.description == description

    assert addy_registry.isValidAddy(new_addy.address)
    assert addy_registry.getAddyId(new_addy.address) == addy_id
    assert addy_registry.getAddy(addy_id) == new_addy.address
    assert addy_registry.getAddyDescription(addy_id) == description
    assert addy_registry.getNumAddys() == numAddys + 1
    assert addy_registry.getLastAddy() == new_addy.address
    assert addy_registry.getLastAddyId() == addy_id
    
    info = addy_registry.getAddyInfo(addy_id)
    assert info.addr == new_addy.address
    assert info.version == 1
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_register_new_addy_invalid_cases(addy_registry, new_addy, governor, bob):
    description = "Test Addy"
    
    # Test non-governor cannot register
    with boa.reverts("no perms"):
        addy_registry.registerNewAddy(new_addy, description, sender=bob)
    
    # Test cannot register zero address
    assert not addy_registry.isValidNewAddy(ZERO_ADDRESS)
    assert addy_registry.registerNewAddy(ZERO_ADDRESS, description, sender=governor) == 0
    
    # Test cannot register same addy twice
    assert addy_registry.registerNewAddy(new_addy, description, sender=governor) != 0
    assert addy_registry.registerNewAddy(new_addy, description, sender=governor) == 0


def test_update_addy(addy_registry, new_addy, new_addy_b, governor, bob):
    description = "Test Addy"
    addy_id = addy_registry.registerNewAddy(new_addy, description, sender=governor)
    assert addy_id != 0

    # Test non-governor cannot update
    with boa.reverts("no perms"):
        addy_registry.updateAddy(addy_id, new_addy_b, sender=bob)

    # invalid id
    assert not addy_registry.isValidAddyUpdate(999, new_addy_b)
    assert not addy_registry.updateAddy(999, new_addy_b, sender=governor)

    # same address
    assert not addy_registry.updateAddy(addy_id, new_addy, sender=governor)

    # Test successful update
    assert addy_registry.updateAddy(addy_id, new_addy_b, sender=governor)

    log = filter_logs(addy_registry, "AddyIdUpdated")[0]
    assert log.newAddr == new_addy_b.address
    assert log.prevAddy == new_addy.address
    assert log.addyId == addy_id
    assert log.version == 2
    assert log.description == description

    assert addy_registry.getAddy(addy_id) == new_addy_b.address
    assert addy_registry.getAddyId(new_addy_b.address) == addy_id
    assert addy_registry.getAddyId(new_addy.address) == 0  # Old address mapping cleared
    
    info = addy_registry.getAddyInfo(addy_id)
    assert info.addr == new_addy_b.address
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_disable_addy(addy_registry, new_addy, governor, bob):
    description = "Test Addy"
    addy_id = addy_registry.registerNewAddy(new_addy, description, sender=governor)
    assert addy_id != 0

    # Test non-governor cannot disable
    with boa.reverts("no perms"):
        addy_registry.disableAddy(addy_id, sender=bob)

    # invalid id
    assert not addy_registry.isValidAddyDisable(999)
    assert not addy_registry.disableAddy(999, sender=governor)

    # Test successful disable
    assert addy_registry.disableAddy(addy_id, sender=governor)

    log = filter_logs(addy_registry, "AddyIdDisabled")[0]
    assert log.prevAddy == new_addy.address
    assert log.addyId == addy_id
    assert log.version == 2
    assert log.description == description

    assert addy_registry.getAddy(addy_id) == ZERO_ADDRESS
    assert addy_registry.getAddyId(new_addy.address) == 0
    
    info = addy_registry.getAddyInfo(addy_id)
    assert info.addr == ZERO_ADDRESS
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp
    
    # already disabled
    assert not addy_registry.disableAddy(addy_id, sender=governor)


def test_view_functions(addy_registry, new_addy, governor):
    description = "Test Addy"
    addy_id = addy_registry.registerNewAddy(new_addy, description, sender=governor)
    
    # Test isValidNewAddy
    assert not addy_registry.isValidNewAddy(new_addy.address)  # Already registered
    assert not addy_registry.isValidNewAddy(ZERO_ADDRESS)  # Zero address
    
    # Test isValidAddyUpdate
    assert not addy_registry.isValidAddyUpdate(addy_id, new_addy.address)  # Same address
    assert not addy_registry.isValidAddyUpdate(0, new_addy.address)  # Invalid addy ID
    
    # Test isValidAddyDisable
    assert addy_registry.isValidAddyDisable(addy_id)
    assert not addy_registry.isValidAddyDisable(0)  # Invalid addy ID
    
    # Test isValidAddyId
    assert addy_registry.isValidAddyId(addy_id)
    assert not addy_registry.isValidAddyId(0)
    assert not addy_registry.isValidAddyId(999)  # Non-existent ID


def test_register_eoa_address_invalid(addy_registry, governor, bob):
    """Registering an EOA (non‑contract) address must fail and return 0."""
    description = "EOA Addy"

    # bob is an EOA, so this should be considered invalid
    assert not addy_registry.isValidNewAddy(bob)
    assert addy_registry.registerNewAddy(bob, description, sender=governor) == 0


def test_update_addy_with_eoa_invalid(addy_registry, governor, bob, alpha_token):
    """Updating an existing addy to point to an EOA address must be rejected."""
    original = alpha_token
    description = "Original"
    addy_id = addy_registry.registerNewAddy(original, description, sender=governor)
    assert addy_id != 0

    # Attempt to update to an EOA address (bob)
    assert not addy_registry.updateAddy(addy_id, bob, sender=governor)

    # Verify state has NOT changed
    assert addy_registry.getAddy(addy_id) == original.address
    assert addy_registry.getAddyId(original.address) == addy_id
    assert addy_registry.getAddyId(bob) == 0


def test_update_addy_after_disable(addy_registry, governor, bravo_token, charlie_token):
    """A disabled addy can be updated to a new contract address, re‑enabling it."""
    first = bravo_token
    second = charlie_token
    description = "Re‑enable flow"

    # Register and then disable
    addy_id = addy_registry.registerNewAddy(first, description, sender=governor)
    assert addy_registry.disableAddy(addy_id, sender=governor)
    assert addy_registry.getAddy(addy_id) == ZERO_ADDRESS

    # Now update to a fresh contract addr — should succeed
    assert addy_registry.updateAddy(addy_id, second, sender=governor)

    # Version should have incremented (1 initial + 1 disable + 1 update = 3)
    info = addy_registry.getAddyInfo(addy_id)
    assert info.addr == second.address
    assert info.version == 3
    assert addy_registry.getAddyId(first.address) == 0
    assert addy_registry.getAddyId(second.address) == addy_id


def test_disable_addy_zero_id(addy_registry, governor):
    """Disabling addyId == 0 should be a no‑op and return False (never reverts)."""
    assert not addy_registry.isValidAddyDisable(0)
    assert not addy_registry.disableAddy(0, sender=governor)


def test_last_addy_after_disable(addy_registry, governor, charlie_token_erc4626_vault):
    """When the last registered addy is disabled it should remain the last id but resolve to ZERO_ADDRESS."""
    latest = charlie_token_erc4626_vault
    description = "Latest Addy"
    last_id = addy_registry.registerNewAddy(latest, description, sender=governor)

    # Sanity check — it is indeed the last addy prior to disable
    assert addy_registry.getLastAddyId() == last_id
    assert addy_registry.getLastAddy() == latest.address

    # Disable and verify getters
    assert addy_registry.disableAddy(last_id, sender=governor)

    assert addy_registry.getLastAddyId() == last_id  # index unchanged
    assert addy_registry.getLastAddy() == ZERO_ADDRESS  # should now return zero addr


##############
# Governance #
##############


def test_initial_governance(addy_registry, governor):
    """Test initial governance setup"""
    assert addy_registry.governance() == governor
    assert addy_registry.govChangeDelay() == addy_registry.MIN_GOV_CHANGE_DELAY()


def test_governance_change_delay(addy_registry, governor, bob):
    """Test setting governance change delay"""
    # Test setting valid delay
    new_delay = addy_registry.MIN_GOV_CHANGE_DELAY() + 1000
    addy_registry.setGovernanceChangeDelay(new_delay, sender=governor)

    log = filter_logs(addy_registry, "GovChangeDelaySet")[0]
    assert log.delayBlocks == new_delay

    assert addy_registry.govChangeDelay() == new_delay

    # Test setting delay below minimum
    with boa.reverts("invalid delay"):
        addy_registry.setGovernanceChangeDelay(addy_registry.MIN_GOV_CHANGE_DELAY() - 1, sender=governor)

    # Test setting delay above maximum
    with boa.reverts("invalid delay"):
        addy_registry.setGovernanceChangeDelay(addy_registry.MAX_GOV_CHANGE_DELAY() + 1, sender=governor)

    # Test setting delay by non-governor
    with boa.reverts("no perms"):
        addy_registry.setGovernanceChangeDelay(new_delay, sender=bob)


def test_governance_change_process(addy_registry, governor, new_governor):
    """Test complete governance change process"""
    delay = addy_registry.govChangeDelay()
    current_block = boa.env.evm.patch.block_number

    # Initiate governance change
    addy_registry.changeGovernance(new_governor.address, sender=governor)
    log = filter_logs(addy_registry, "GovChangeInitiated")[0]
    assert log.prevGov == governor
    assert log.newGov == new_governor.address
    assert log.confirmBlock == current_block + delay

    # Check pending governance data
    pending_gov = addy_registry.pendingGov()
    assert pending_gov.newGov == new_governor.address
    assert pending_gov.initiatedBlock == current_block
    assert pending_gov.confirmBlock == current_block + delay

    # Try to confirm before delay
    with boa.reverts("time delay not reached"):
        addy_registry.confirmGovernanceChange(sender=new_governor.address)

    # Advance blocks to pass delay
    boa.env.time_travel(blocks=delay)

    # Confirm governance change
    addy_registry.confirmGovernanceChange(sender=new_governor.address)
    log = filter_logs(addy_registry, "GovChangeConfirmed")[0]
    assert log.prevGov == governor
    assert log.newGov == new_governor.address
    assert log.initiatedBlock == pending_gov.initiatedBlock
    assert log.confirmBlock == pending_gov.confirmBlock

    # Verify governance change
    assert addy_registry.governance() == new_governor.address

    pending_gov = addy_registry.pendingGov()
    assert pending_gov.newGov == ZERO_ADDRESS
    assert pending_gov.initiatedBlock == 0
    assert pending_gov.confirmBlock == 0


def test_governance_change_restrictions(addy_registry, governor, new_governor, bob):
    """Test governance change restrictions"""
    # Test initiating change by non-governor
    with boa.reverts("no perms"):
        addy_registry.changeGovernance(new_governor.address, sender=bob)

    # Test invalid new governance addresses
    with boa.reverts("new governance must be a contract"):
        addy_registry.changeGovernance(ZERO_ADDRESS, sender=governor)
    with boa.reverts("invalid new governance"):
        addy_registry.changeGovernance(governor, sender=governor)

    # Test confirming without pending change
    with boa.reverts("no pending governance"):
        addy_registry.confirmGovernanceChange(sender=new_governor.address)

    # Initiate valid change
    addy_registry.changeGovernance(new_governor.address, sender=governor)

    boa.env.time_travel(blocks=addy_registry.govChangeDelay())

    # Test confirming by wrong address
    with boa.reverts("only new governance can confirm"):
        addy_registry.confirmGovernanceChange(sender=governor)
    with boa.reverts("only new governance can confirm"):
        addy_registry.confirmGovernanceChange(sender=bob)


def test_governance_change_cancellation(addy_registry, governor, new_governor, bob):
    """Test cancelling governance change"""
    delay = addy_registry.govChangeDelay()

    # Test cancelling without pending change
    with boa.reverts("no pending change"):
        addy_registry.cancelGovernanceChange(sender=governor)

    # Initiate governance change
    addy_registry.changeGovernance(new_governor.address, sender=governor)
    pending_gov = addy_registry.pendingGov()

    # Test cancelling by non-governor
    with boa.reverts("no perms"):
        addy_registry.cancelGovernanceChange(sender=bob)

    # Cancel governance change
    addy_registry.cancelGovernanceChange(sender=governor)
    log = filter_logs(addy_registry, "GovChangeCancelled")[0]
    assert log.cancelledGov == new_governor.address
    assert log.initiatedBlock == pending_gov.initiatedBlock
    assert log.confirmBlock == pending_gov.confirmBlock

    # Verify cancellation
    assert addy_registry.governance() == governor
    pending_gov = addy_registry.pendingGov()
    assert pending_gov.newGov == ZERO_ADDRESS
    assert pending_gov.initiatedBlock == 0
    assert pending_gov.confirmBlock == 0

    # Verify cannot confirm after cancellation
    boa.env.time_travel(blocks=delay)
    with boa.reverts("no pending governance"):
        addy_registry.confirmGovernanceChange(sender=new_governor.address)


def test_multiple_governance_changes(addy_registry, governor, new_governor, new_addy):
    """Test multiple governance changes"""
    first_new_governor = new_governor
    second_new_governor = new_addy  # Use new_addy instead of bob since it's a contract
    delay = addy_registry.govChangeDelay()

    # Initiate first governance change
    addy_registry.changeGovernance(first_new_governor.address, sender=governor)
    init_log = filter_logs(addy_registry, "GovChangeInitiated")[0]
    assert init_log.prevGov == governor
    assert init_log.newGov == first_new_governor.address

    # Complete first change
    boa.env.time_travel(blocks=delay)
    addy_registry.confirmGovernanceChange(sender=first_new_governor.address)
    confirm_log = filter_logs(addy_registry, "GovChangeConfirmed")[0]
    assert confirm_log.prevGov == governor
    assert confirm_log.newGov == first_new_governor.address
    assert addy_registry.governance() == first_new_governor.address

    # Initiate second governance change
    addy_registry.changeGovernance(second_new_governor.address, sender=first_new_governor.address)
    init_log = filter_logs(addy_registry, "GovChangeInitiated")[0]
    assert init_log.prevGov == first_new_governor.address
    assert init_log.newGov == second_new_governor.address

    # Complete second change
    boa.env.time_travel(blocks=delay)
    addy_registry.confirmGovernanceChange(sender=second_new_governor.address)
    confirm_log = filter_logs(addy_registry, "GovChangeConfirmed")[0]
    assert confirm_log.prevGov == first_new_governor.address
    assert confirm_log.newGov == second_new_governor.address
    assert addy_registry.governance() == second_new_governor.address


def test_has_pending_governance_change(addy_registry, governor, new_governor, new_addy):
    """Test hasPendingGovChange view function"""
    # Initially no pending change
    assert not addy_registry.hasPendingGovChange()

    # After initiating change
    addy_registry.changeGovernance(new_governor.address, sender=governor)
    assert addy_registry.hasPendingGovChange()

    # After confirming change
    boa.env.time_travel(blocks=addy_registry.govChangeDelay())
    addy_registry.confirmGovernanceChange(sender=new_governor.address)
    assert not addy_registry.hasPendingGovChange()

    # After cancelling change
    addy_registry.changeGovernance(new_addy.address, sender=new_governor.address)  # Use new_addy instead of governor
    assert addy_registry.hasPendingGovChange()
    addy_registry.cancelGovernanceChange(sender=new_governor.address)
    assert not addy_registry.hasPendingGovChange()


def test_new_governance_must_be_contract(addy_registry, governor, bob):
    """Test that new governance must be a contract"""
    # bob is an EOA, not a contract
    with boa.reverts("new governance must be a contract"):
        addy_registry.changeGovernance(bob, sender=governor)


def test_governance_change_timing_edge_cases(addy_registry, governor, new_governor):
    """Test edge cases around governance change timing"""
    delay = addy_registry.govChangeDelay()
    
    # Initiate change
    addy_registry.changeGovernance(new_governor.address, sender=governor)
    
    # Try to confirm exactly at confirm block
    boa.env.time_travel(blocks=delay - 1)
    with boa.reverts("time delay not reached"):
        addy_registry.confirmGovernanceChange(sender=new_governor.address)
    
    boa.env.time_travel(blocks=1)  # Move to exactly confirm block
    addy_registry.confirmGovernanceChange(sender=new_governor.address)
    assert addy_registry.governance() == new_governor.address


def test_pending_governance_struct(addy_registry, governor, new_governor, new_addy):
    """Test pending governance struct fields"""
    current_block = boa.env.evm.patch.block_number
    delay = addy_registry.govChangeDelay()
    
    # Initiate change
    addy_registry.changeGovernance(new_governor.address, sender=governor)
    pending_gov = addy_registry.pendingGov()
    
    # Verify all struct fields
    assert pending_gov.newGov == new_governor.address
    assert pending_gov.initiatedBlock == current_block
    assert pending_gov.confirmBlock == current_block + delay
    
    # Verify struct is cleared after confirmation
    boa.env.time_travel(blocks=delay)
    addy_registry.confirmGovernanceChange(sender=new_governor.address)
    pending_gov = addy_registry.pendingGov()
    assert pending_gov.newGov == ZERO_ADDRESS
    assert pending_gov.initiatedBlock == 0
    assert pending_gov.confirmBlock == 0
    
    # Verify struct is cleared after cancellation
    addy_registry.changeGovernance(new_addy.address, sender=new_governor.address)  # Use new_addy instead of governor
    addy_registry.cancelGovernanceChange(sender=new_governor.address)
    pending_gov = addy_registry.pendingGov()
    assert pending_gov.newGov == ZERO_ADDRESS
    assert pending_gov.initiatedBlock == 0
    assert pending_gov.confirmBlock == 0

