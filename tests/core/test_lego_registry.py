import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def new_lego_registry(governor, addy_registry, lego_registry):
    r = boa.load("contracts/core/LegoRegistry.vy", addy_registry, name="new_lego_registry")
    lego_registry_addy_id = addy_registry.getAddyId(lego_registry.address)
    assert addy_registry.updateAddy(lego_registry_addy_id, r.address, sender=governor)
    return r


@pytest.fixture(scope="module")
def new_lego(alpha_token, alpha_token_erc4626_vault, addy_registry_deploy):
    return boa.load("contracts/mock/MockLego.vy", alpha_token, alpha_token_erc4626_vault, addy_registry_deploy, name="new_lego")


@pytest.fixture(scope="module")
def new_lego_b(alpha_token, alpha_token_erc4626_vault, addy_registry_deploy):
    return boa.load("contracts/mock/MockLego.vy", alpha_token, alpha_token_erc4626_vault, addy_registry_deploy, name="new_lego_b")


#########
# Tests #
#########


def test_initial_state(new_lego_registry):
    assert new_lego_registry.isActivated()
    assert new_lego_registry.numLegos() == 1
    assert new_lego_registry.legoHelper() == ZERO_ADDRESS


def test_register_new_lego(new_lego_registry, new_lego, governor):
    description = "Test Lego"

    assert new_lego_registry.isValidNewLegoAddr(new_lego)
    
    # Test successful registration
    lego_id = new_lego_registry.registerNewLego(new_lego, description, sender=governor)
    assert lego_id  == 1

    # Verify event
    log = filter_logs(new_lego_registry, "NewLegoRegistered")[0]
    assert log.addr == new_lego.address
    assert log.legoId == lego_id
    assert log.description == description

    assert new_lego_registry.isValidLegoAddr(new_lego.address)
    assert new_lego_registry.getLegoId(new_lego.address) == lego_id
    assert new_lego_registry.getLegoAddr(lego_id) == new_lego.address
    assert new_lego_registry.getLegoDescription(lego_id) == description
    assert new_lego_registry.getNumLegos() == 1
    assert new_lego_registry.getLastLegoAddr() == new_lego.address
    assert new_lego_registry.getLastLegoId() == lego_id
    
    info = new_lego_registry.getLegoInfo(lego_id)
    assert info.addr == new_lego.address
    assert info.version == 1
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_register_new_lego_invalid_cases(new_lego_registry, new_lego, governor, bob):
    description = "Test Lego"
    
    # Test non-governor cannot register
    with boa.reverts("no perms"):
        new_lego_registry.registerNewLego(new_lego, description, sender=bob)
    
    # Test cannot register zero address
    assert not new_lego_registry.isValidNewLegoAddr(ZERO_ADDRESS)
    assert new_lego_registry.registerNewLego(ZERO_ADDRESS, description, sender=governor) == 0
    
    # Test cannot register same lego twice
    assert new_lego_registry.registerNewLego(new_lego, description, sender=governor) != 0
    assert new_lego_registry.registerNewLego(new_lego, description, sender=governor) == 0


def test_update_lego_addr(new_lego_registry, new_lego, new_lego_b, governor, bob):
    description = "Test Lego"
    lego_id = new_lego_registry.registerNewLego(new_lego, description, sender=governor)
    assert lego_id != 0

    # Test non-governor cannot update
    with boa.reverts("no perms"):
        new_lego_registry.updateLegoAddr(lego_id, new_lego_b, sender=bob)

    # invalid id
    assert not new_lego_registry.isValidLegoUpdate(999, new_lego_b)
    assert not new_lego_registry.updateLegoAddr(999, new_lego_b, sender=governor)

    # same address
    assert not new_lego_registry.updateLegoAddr(lego_id, new_lego, sender=governor)

    # Test successful update
    assert new_lego_registry.updateLegoAddr(lego_id, new_lego_b, sender=governor)

    log = filter_logs(new_lego_registry, "LegoAddrUpdated")[0]
    assert log.newAddr == new_lego_b.address
    assert log.prevAddr == new_lego.address
    assert log.legoId == lego_id
    assert log.version == 2
    assert log.description == description

    assert new_lego_registry.getLegoAddr(lego_id) == new_lego_b.address
    assert new_lego_registry.getLegoId(new_lego_b.address) == lego_id
    assert new_lego_registry.getLegoId(new_lego.address) == 0  # Old address mapping cleared
    
    info = new_lego_registry.getLegoInfo(lego_id)
    assert info.addr == new_lego_b.address
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp
    

def test_disable_lego_addr(new_lego_registry, new_lego, governor, bob):
    description = "Test Lego"
    lego_id = new_lego_registry.registerNewLego(new_lego, description, sender=governor)
    assert lego_id != 0

    # Test non-governor cannot disable
    with boa.reverts("no perms"):
        new_lego_registry.disableLegoAddr(lego_id, sender=bob)

    # invalid id
    assert not new_lego_registry.isValidLegoDisable(999)
    assert not new_lego_registry.disableLegoAddr(999, sender=governor)

    # Test successful disable
    assert new_lego_registry.disableLegoAddr(lego_id, sender=governor)

    log = filter_logs(new_lego_registry, "LegoAddrDisabled")[0]
    assert log.prevAddr == new_lego.address
    assert log.legoId == lego_id
    assert log.version == 2
    assert log.description == description

    assert new_lego_registry.getLegoAddr(lego_id) == ZERO_ADDRESS
    assert new_lego_registry.getLegoId(new_lego.address) == 0
    
    info = new_lego_registry.getLegoInfo(lego_id)
    assert info.addr == ZERO_ADDRESS
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp
    
    # already disabled
    assert not new_lego_registry.disableLegoAddr(lego_id, sender=governor)


def test_set_lego_helper(new_lego_registry, alpha_token, governor, bob):
    lego_helper = alpha_token # using random contract

    # Test non-governor cannot set helper
    with boa.reverts("no perms"):
        new_lego_registry.setLegoHelper(lego_helper, sender=bob)
    
    # invalid helper
    assert not new_lego_registry.setLegoHelper(ZERO_ADDRESS, sender=governor)
    assert not new_lego_registry.setLegoHelper(bob, sender=governor)

    # Test successful helper set
    assert new_lego_registry.setLegoHelper(lego_helper, sender=governor)

    # Verify event
    log = filter_logs(new_lego_registry, "LegoHelperSet")[0]
    assert log.helperAddr == lego_helper.address

    assert new_lego_registry.legoHelper() == lego_helper.address 
    
    # Test cannot set same helper again
    assert not new_lego_registry.setLegoHelper(lego_helper, sender=governor)


def test_activation(new_lego_registry, new_lego, governor, bob):
    # Test non-governor cannot change activation
    with boa.reverts("no perms"):
        new_lego_registry.activate(False, sender=bob)
    
    # Test deactivation
    new_lego_registry.activate(False, sender=governor)

    log = filter_logs(new_lego_registry, "LegoRegistryActivated")[0]
    assert log.isActivated == False

    assert not new_lego_registry.isActivated()
    
    # Test operations fail when deactivated
    description = "Test Lego"
    with boa.reverts("not activated"):
        new_lego_registry.registerNewLego(new_lego, description, sender=governor)
    
    # Test reactivation
    new_lego_registry.activate(True, sender=governor)
    assert new_lego_registry.isActivated()


def test_view_functions(new_lego_registry, new_lego, governor):
    description = "Test Lego"
    lego_id = new_lego_registry.registerNewLego(new_lego, description, sender=governor)
    
    # Test isValidNewLegoAddr
    assert not new_lego_registry.isValidNewLegoAddr(new_lego.address)  # Already registered
    assert not new_lego_registry.isValidNewLegoAddr(ZERO_ADDRESS)  # Zero address
    
    # Test isValidLegoUpdate
    assert not new_lego_registry.isValidLegoUpdate(lego_id, new_lego.address)  # Same address
    assert not new_lego_registry.isValidLegoUpdate(0, new_lego.address)  # Invalid lego ID
    
    # Test isValidLegoDisable
    assert new_lego_registry.isValidLegoDisable(lego_id)
    assert not new_lego_registry.isValidLegoDisable(0)  # Invalid lego ID
    
    # Test isValidLegoId
    assert new_lego_registry.isValidLegoId(lego_id)
    assert not new_lego_registry.isValidLegoId(0)
    assert not new_lego_registry.isValidLegoId(999)  # Non-existent ID
