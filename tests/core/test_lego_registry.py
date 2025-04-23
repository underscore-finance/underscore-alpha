import pytest
import boa

from constants import ZERO_ADDRESS, YIELD_OPP_UINT256, DEX_UINT256
from conf_utils import filter_logs
from utils.BluePrint import PARAMS


@pytest.fixture(scope="module")
def new_lego(alpha_token, alpha_token_erc4626_vault, addy_registry, governor):
    addr = boa.load("contracts/mock/MockLego.vy", addy_registry, name="new_lego")
    assert addr.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    return addr


@pytest.fixture(scope="module")
def new_lego_b(alpha_token, alpha_token_erc4626_vault, addy_registry, governor):
    addr = boa.load("contracts/mock/MockLego.vy", addy_registry, name="new_lego_b")
    assert addr.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    return addr


#########
# Tests #
#########


def test_register_new_lego(lego_registry, new_lego, governor):
    description = "Test Lego"

    assert lego_registry.isValidNewLegoAddr(new_lego)
    
    numLegos = lego_registry.numLegosRaw()
    current_block = boa.env.evm.patch.block_number

    # Test successful registration initiation
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)

    # Verify pending event
    log = filter_logs(lego_registry, "NewAddyPending")[0]
    assert log.addr == new_lego.address
    assert log.description == description
    assert log.confirmBlock == current_block + lego_registry.legoChangeDelay()

    # Confirm registration after delay
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    assert lego_id == numLegos

    # Verify registration event
    log = filter_logs(lego_registry, "NewAddyConfirmed")[0]
    assert log.addr == new_lego.address
    assert log.addyId == lego_id
    assert log.description == description

    assert lego_registry.isValidLegoAddr(new_lego.address)
    assert lego_registry.getLegoId(new_lego.address) == lego_id
    assert lego_registry.getLegoAddr(lego_id) == new_lego.address
    assert lego_registry.getLegoDescription(lego_id) == description
    assert lego_registry.getNumLegos() == lego_id
    assert lego_registry.getLastLegoAddr() == new_lego.address
    assert lego_registry.getLastLegoId() == lego_id
    
    info = lego_registry.getLegoInfo(lego_id)
    assert info.addr == new_lego.address
    assert info.version == 1
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_register_new_lego_invalid_cases(lego_registry, new_lego, governor, bob):
    description = "Test Lego"
    
    # Test non-governor cannot register
    with boa.reverts():  # Empty revert as the assertion combines both checks
        lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=bob)
    
    # Test cannot register zero address
    assert not lego_registry.isValidNewLegoAddr(ZERO_ADDRESS)
    assert not lego_registry.registerNewLego(ZERO_ADDRESS, description, YIELD_OPP_UINT256, sender=governor)
    
    # Register lego first time
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    
    # Wait for delay and confirm first registration
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    assert lego_id != 0

    # Test cannot register an already registered address
    assert not lego_registry.isValidNewLegoAddr(new_lego)
    assert not lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)


def test_cancel_pending_registration(lego_registry, new_lego, governor, bob):
    description = "Test Lego"
    current_block = boa.env.evm.patch.block_number
    
    # Initiate registration
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    
    # Test non-governor cannot cancel
    with boa.reverts("no perms"):
        lego_registry.cancelPendingNewLego(new_lego, sender=bob)
    
    # Test successful cancellation
    assert lego_registry.cancelPendingNewLego(new_lego, sender=governor)
    
    # Verify cancellation event
    log = filter_logs(lego_registry, "NewPendingAddyCancelled")[0]
    assert log.addr == new_lego.address
    assert log.description == description
    assert log.initiatedBlock == current_block
    assert log.confirmBlock == current_block + lego_registry.legoChangeDelay()
    
    # Test cannot confirm cancelled registration
    with boa.reverts():  # Empty revert as the assertion combines both checks
        lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)


def test_update_lego_addr(lego_registry, new_lego, new_lego_b, governor, bob):
    description = "Test Lego"
    # Register and confirm initial lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    assert lego_id != 0

    current_block = boa.env.evm.patch.block_number

    # Test non-governor cannot update
    with boa.reverts("no perms"):
        lego_registry.updateLegoAddr(lego_id, new_lego_b, sender=bob)

    # invalid id
    assert not lego_registry.isValidLegoUpdate(999, new_lego_b)
    assert not lego_registry.updateLegoAddr(999, new_lego_b, sender=governor)

    # same address
    assert not lego_registry.updateLegoAddr(lego_id, new_lego, sender=governor)

    # Test successful update initiation
    assert lego_registry.updateLegoAddr(lego_id, new_lego_b, sender=governor)
    
    # Verify pending event
    log = filter_logs(lego_registry, "AddyUpdatePending")[0]
    assert log.newAddr == new_lego_b.address
    assert log.prevAddr == new_lego.address
    assert log.addyId == lego_id
    assert log.confirmBlock == current_block + lego_registry.legoChangeDelay()

    # Confirm update after delay
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmLegoUpdate(lego_id, sender=governor)

    # Verify update event
    log = filter_logs(lego_registry, "AddyUpdateConfirmed")[0]
    assert log.newAddr == new_lego_b.address
    assert log.prevAddr == new_lego.address
    assert log.addyId == lego_id
    assert log.version == 2
    assert log.description == description

    assert lego_registry.getLegoAddr(lego_id) == new_lego_b.address
    assert lego_registry.getLegoId(new_lego_b.address) == lego_id
    assert lego_registry.getLegoId(new_lego.address) == 0  # Old address mapping cleared
    
    info = lego_registry.getLegoInfo(lego_id)
    assert info.addr == new_lego_b.address
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_cancel_pending_update(lego_registry, new_lego, new_lego_b, governor, bob):
    description = "Test Lego"
    # Register and confirm initial lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    current_block = boa.env.evm.patch.block_number
    
    # Initiate update
    assert lego_registry.updateLegoAddr(lego_id, new_lego_b, sender=governor)
    
    # Test non-governor cannot cancel
    with boa.reverts("no perms"):
        lego_registry.cancelPendingLegoUpdate(lego_id, sender=bob)
    
    # Test successful cancellation
    assert lego_registry.cancelPendingLegoUpdate(lego_id, sender=governor)
    
    # Verify cancellation event
    log = filter_logs(lego_registry, "AddyUpdateCancelled")[0]
    assert log.addyId == lego_id
    assert log.newAddr == new_lego_b.address
    assert log.prevAddr == new_lego.address
    assert log.initiatedBlock == current_block
    assert log.confirmBlock == current_block + lego_registry.legoChangeDelay()
    
    # Test cannot confirm cancelled update
    with boa.reverts():  # Empty revert as the assertion combines both checks
        lego_registry.confirmLegoUpdate(lego_id, sender=governor)


def test_disable_lego_addr(lego_registry, new_lego, governor, bob):
    description = "Test Lego"
    # Register and confirm initial lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    assert lego_id != 0

    current_block = boa.env.evm.patch.block_number

    # Test non-governor cannot disable
    with boa.reverts("no perms"):
        lego_registry.disableLegoAddr(lego_id, sender=bob)

    # invalid id
    assert not lego_registry.isValidLegoDisable(999)
    assert not lego_registry.disableLegoAddr(999, sender=governor)

    # Test successful disable initiation
    assert lego_registry.disableLegoAddr(lego_id, sender=governor)
    
    # Verify pending event
    log = filter_logs(lego_registry, "AddyDisablePending")[0]
    assert log.addyId == lego_id
    assert log.addr == new_lego.address
    assert log.confirmBlock == current_block + lego_registry.legoChangeDelay()

    # Confirm disable after delay
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmLegoDisable(lego_id, sender=governor)

    # Verify disable event
    log = filter_logs(lego_registry, "AddyDisableConfirmed")[0]
    assert log.addr == new_lego.address
    assert log.addyId == lego_id
    assert log.version == 2
    assert log.description == description

    assert lego_registry.getLegoAddr(lego_id) == ZERO_ADDRESS
    assert lego_registry.getLegoId(new_lego.address) == 0
    
    info = lego_registry.getLegoInfo(lego_id)
    assert info.addr == ZERO_ADDRESS
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp
    
    # already disabled
    assert not lego_registry.disableLegoAddr(lego_id, sender=governor)


def test_cancel_pending_disable(lego_registry, new_lego, governor, bob):
    description = "Test Lego"
    # Register and confirm initial lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    current_block = boa.env.evm.patch.block_number
    
    # Initiate disable
    assert lego_registry.disableLegoAddr(lego_id, sender=governor)
    
    # Test non-governor cannot cancel
    with boa.reverts("no perms"):
        lego_registry.cancelPendingLegoDisable(lego_id, sender=bob)
    
    # Test successful cancellation
    assert lego_registry.cancelPendingLegoDisable(lego_id, sender=governor)
    
    # Verify cancellation event
    log = filter_logs(lego_registry, "AddyDisableCancelled")[0]
    assert log.addyId == lego_id
    assert log.addr == new_lego.address
    assert log.initiatedBlock == current_block
    assert log.confirmBlock == current_block + lego_registry.legoChangeDelay()
    
    # Test cannot confirm cancelled disable
    with boa.reverts():  # Empty revert as the assertion combines both checks
        lego_registry.confirmLegoDisable(lego_id, sender=governor)


def test_set_lego_change_delay(lego_registry, governor, bob, fork):
    min_delay = PARAMS[fork]["LEGO_REGISTRY_MIN_CHANGE_DELAY"]
    max_delay = PARAMS[fork]["LEGO_REGISTRY_MAX_CHANGE_DELAY"]
    
    # Test non-governor cannot set delay
    with boa.reverts("no perms"):
        lego_registry.setLegoChangeDelay(min_delay + 1, sender=bob)
    
    # Test invalid delay values
    with boa.reverts():  # Empty revert as the assertion combines both checks
        lego_registry.setLegoChangeDelay(min_delay - 1, sender=governor)
    with boa.reverts():  # Empty revert as the assertion combines both checks
        lego_registry.setLegoChangeDelay(max_delay + 1, sender=governor)
    
    # Test successful delay update
    new_delay = min_delay + 1
    lego_registry.setLegoChangeDelay(new_delay, sender=governor)
    assert lego_registry.legoChangeDelay() == new_delay


def test_set_lego_helper(lego_registry, alpha_token, governor, bob):
    lego_helper = alpha_token # using random contract

    # Test non-governor cannot set helper
    with boa.reverts("no perms"):
        lego_registry.setLegoHelper(lego_helper, sender=bob)
    
    # invalid helper
    assert not lego_registry.setLegoHelper(ZERO_ADDRESS, sender=governor)
    assert not lego_registry.setLegoHelper(bob, sender=governor)

    # Test successful helper set
    assert lego_registry.setLegoHelper(lego_helper, sender=governor)

    # Verify event
    log = filter_logs(lego_registry, "LegoHelperSet")[0]
    assert log.helperAddr == lego_helper.address

    assert lego_registry.legoHelper() == lego_helper.address 
    
    # Test cannot set same helper again
    assert not lego_registry.setLegoHelper(lego_helper, sender=governor)


def test_view_functions(lego_registry, new_lego, governor):
    description = "Test Lego"
    # Register and confirm initial lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    # Test isValidNewLegoAddr
    assert not lego_registry.isValidNewLegoAddr(new_lego.address)  # Already registered
    assert not lego_registry.isValidNewLegoAddr(ZERO_ADDRESS)  # Zero address
    
    # Test isValidLegoUpdate
    assert not lego_registry.isValidLegoUpdate(lego_id, new_lego.address)  # Same address
    assert not lego_registry.isValidLegoUpdate(0, new_lego.address)  # Invalid lego ID
    
    # Test isValidLegoDisable
    assert lego_registry.isValidLegoDisable(lego_id)
    assert not lego_registry.isValidLegoDisable(0)  # Invalid lego ID
    
    # Test isValidLegoId
    assert lego_registry.isValidLegoId(lego_id)
    assert not lego_registry.isValidLegoId(0)
    assert not lego_registry.isValidLegoId(999)  # Non-existent ID


def test_lego_type_handling(lego_registry, new_lego, governor):
    description = "Test Lego"
    # Register with YIELD_OPP type
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    
    # Verify pending type is set correctly
    assert lego_registry.pendingLegoType(new_lego.address) == YIELD_OPP_UINT256
    
    # Confirm registration
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    # Verify type is stored correctly in final mapping
    assert lego_registry.legoIdToType(lego_id) == YIELD_OPP_UINT256
    # Verify pending type is cleared
    assert lego_registry.pendingLegoType(new_lego.address) == 0  # Empty type after confirmation


def test_lego_type_cancellation(lego_registry, new_lego, governor):
    description = "Test Lego"
    # Register with YIELD_OPP type
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    
    # Verify pending type is set
    assert lego_registry.pendingLegoType(new_lego.address) == YIELD_OPP_UINT256
    
    # Cancel registration
    assert lego_registry.cancelPendingNewLego(new_lego, sender=governor)
    
    # Verify pending type is NOT cleared after cancellation (contract behavior)
    assert lego_registry.pendingLegoType(new_lego.address) == YIELD_OPP_UINT256


def test_lego_type_update(lego_registry, new_lego, new_lego_b, governor):
    description = "Test Lego"
    # Register and confirm first lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    # Verify initial type
    assert lego_registry.legoIdToType(lego_id) == YIELD_OPP_UINT256
    
    # Update to new lego
    assert lego_registry.updateLegoAddr(lego_id, new_lego_b, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmLegoUpdate(lego_id, sender=governor)
    
    # Verify type persists after update
    assert lego_registry.legoIdToType(lego_id) == YIELD_OPP_UINT256


def test_lego_type_disable(lego_registry, new_lego, governor):
    description = "Test Lego"
    # Register and confirm lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    # Verify initial type
    assert lego_registry.legoIdToType(lego_id) == YIELD_OPP_UINT256
    
    # Disable lego
    assert lego_registry.disableLegoAddr(lego_id, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmLegoDisable(lego_id, sender=governor)
    
    # Verify type persists after disable
    assert lego_registry.legoIdToType(lego_id) == YIELD_OPP_UINT256


def test_lego_type_edge_cases(lego_registry):
    # Test invalid ID cases
    assert lego_registry.legoIdToType(0) == 0  # Empty type for invalid ID
    assert lego_registry.legoIdToType(999) == 0  # Empty type for non-existent ID
    
    # Test pending type for unregistered address
    assert lego_registry.pendingLegoType(ZERO_ADDRESS) == 0  # Empty type for zero address
    assert lego_registry.pendingLegoType("0x" + "1" * 40) == 0  # Empty type for unregistered address


def test_view_function_edge_cases(lego_registry):
    # Test invalid ID cases
    assert lego_registry.getLegoAddr(0) == ZERO_ADDRESS
    assert lego_registry.getLegoAddr(999) == ZERO_ADDRESS
    assert lego_registry.getLegoDescription(0) == ""
    assert lego_registry.getLegoDescription(999) == ""
    
    # Test empty registry cases
    assert lego_registry.getNumLegos() == 0
    assert lego_registry.getLastLegoAddr() == ZERO_ADDRESS
    assert lego_registry.getLastLegoId() == 0


def test_helper_contract_validation(lego_registry, alpha_token, governor, bob):
    # Test invalid helper addresses
    assert not lego_registry.setLegoHelper(ZERO_ADDRESS, sender=governor)
    assert not lego_registry.setLegoHelper(bob, sender=governor)  # Not a contract
    
    # Test setting same helper twice
    assert lego_registry.setLegoHelper(alpha_token, sender=governor)
    assert not lego_registry.setLegoHelper(alpha_token, sender=governor)


def test_multiple_lego_types(lego_registry, new_lego, new_lego_b, governor):
    description = "Test Lego"
    # Register and confirm YIELD_OPP lego
    assert lego_registry.registerNewLego(new_lego, description, YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    yield_lego_id = lego_registry.confirmNewLegoRegistration(new_lego, sender=governor)
    
    # Register and confirm DEX lego
    assert lego_registry.registerNewLego(new_lego_b, description, DEX_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    dex_lego_id = lego_registry.confirmNewLegoRegistration(new_lego_b, sender=governor)
    
    # Verify types are stored correctly
    assert lego_registry.legoIdToType(yield_lego_id) == YIELD_OPP_UINT256
    assert lego_registry.legoIdToType(dex_lego_id) == DEX_UINT256
