import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def new_oracle(addy_registry):
    return boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="new_oracle_partner")


@pytest.fixture(scope="module")
def new_oracle_b(addy_registry):
    return boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="new_oracle_partner_b")


#########
# Tests #
#########


def test_initial_state(oracle_registry):
    assert oracle_registry.numAddys() == 1


def test_register_new_oracle_partner(oracle_registry, new_oracle, governor):
    description = "Test Oracle Partner"

    assert oracle_registry.isValidNewOraclePartnerAddr(new_oracle)
    
    numOraclePartners = oracle_registry.numAddys()
    current_block = boa.env.evm.patch.block_number

    # Test successful registration initiation
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)

    # Verify pending event
    log = filter_logs(oracle_registry, "NewAddyPending")[0]
    assert log.addr == new_oracle.address
    assert log.description == description
    assert log.confirmBlock == current_block + oracle_registry.addyChangeDelay()

    # Confirm registration after delay
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id == numOraclePartners

    # Verify registration event
    log = filter_logs(oracle_registry, "NewAddyConfirmed")[0]
    assert log.addr == new_oracle.address
    assert log.addyId == oracle_id
    assert log.description == description

    assert oracle_registry.isValidOraclePartnerAddr(new_oracle.address)
    assert oracle_registry.getOraclePartnerId(new_oracle.address) == oracle_id
    assert oracle_registry.getOraclePartnerAddr(oracle_id) == new_oracle.address
    assert oracle_registry.getOraclePartnerDescription(oracle_id) == description
    assert oracle_registry.numAddys() == oracle_id + 1  # Account for initial oracle partner
    assert oracle_registry.getLastOraclePartnerAddr() == new_oracle.address
    assert oracle_registry.getLastOraclePartnerId() == oracle_id
    
    info = oracle_registry.getOraclePartnerInfo(oracle_id)
    assert info.addr == new_oracle.address
    assert info.version == 1
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_register_new_oracle_invalid_cases(oracle_registry, new_oracle, governor, bob):
    description = "Test Oracle Partner"
    
    # Test non-governor cannot register
    with boa.reverts("no perms"):
        oracle_registry.registerNewOraclePartner(new_oracle, description, sender=bob)
    
    # Test cannot register zero address
    assert not oracle_registry.isValidNewOraclePartnerAddr(ZERO_ADDRESS)
    assert not oracle_registry.registerNewOraclePartner(ZERO_ADDRESS, description, sender=governor)
    
    # Register oracle first time
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    
    # Wait for delay and confirm first registration
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    # Test cannot register an already registered address
    assert not oracle_registry.isValidNewOraclePartnerAddr(new_oracle)
    assert not oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)


def test_cancel_pending_registration(oracle_registry, new_oracle, governor, bob):
    description = "Test Oracle Partner"
    current_block = boa.env.evm.patch.block_number
    
    # Initiate registration
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    
    # Test non-governor cannot cancel
    with boa.reverts("no perms"):
        oracle_registry.cancelPendingNewOraclePartner(new_oracle, sender=bob)
    
    # Test successful cancellation
    assert oracle_registry.cancelPendingNewOraclePartner(new_oracle, sender=governor)
    
    # Verify cancellation event
    log = filter_logs(oracle_registry, "NewPendingAddyCancelled")[0]
    assert log.addr == new_oracle.address
    assert log.description == description
    assert log.initiatedBlock == current_block
    assert log.confirmBlock == current_block + oracle_registry.addyChangeDelay()
    
    # Test cannot confirm cancelled registration
    with boa.reverts():  # Empty revert as the assertion combines both checks
        oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)


def test_update_oracle_addr(oracle_registry, new_oracle, new_oracle_b, governor, bob):
    description = "Test Oracle Partner"
    # Register and confirm initial oracle
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    current_block = boa.env.evm.patch.block_number

    # Test non-governor cannot update
    with boa.reverts("no perms"):
        oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle_b, sender=bob)

    # invalid id
    assert not oracle_registry.isValidOraclePartnerUpdate(999, new_oracle_b)
    assert not oracle_registry.updateOraclePartnerAddr(999, new_oracle_b, sender=governor)

    # same address
    assert not oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle, sender=governor)

    # Test successful update initiation
    assert oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle_b, sender=governor)
    
    # Verify pending event
    log = filter_logs(oracle_registry, "AddyUpdatePending")[0]
    assert log.newAddr == new_oracle_b.address
    assert log.prevAddr == new_oracle.address
    assert log.addyId == oracle_id
    assert log.confirmBlock == current_block + oracle_registry.addyChangeDelay()

    # Confirm update after delay
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    assert oracle_registry.confirmOraclePartnerUpdate(oracle_id, sender=governor)

    # Verify update event
    log = filter_logs(oracle_registry, "AddyUpdateConfirmed")[0]
    assert log.newAddr == new_oracle_b.address
    assert log.prevAddr == new_oracle.address
    assert log.addyId == oracle_id
    assert log.version == 2
    assert log.description == description

    assert oracle_registry.getOraclePartnerAddr(oracle_id) == new_oracle_b.address
    assert oracle_registry.getOraclePartnerId(new_oracle_b.address) == oracle_id
    assert oracle_registry.getOraclePartnerId(new_oracle.address) == 0  # Old address mapping cleared
    
    info = oracle_registry.getOraclePartnerInfo(oracle_id)
    assert info.addr == new_oracle_b.address
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_cancel_pending_update(oracle_registry, new_oracle, new_oracle_b, governor, bob):
    description = "Test Oracle Partner"
    # Register and confirm initial oracle
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    current_block = boa.env.evm.patch.block_number
    
    # Initiate update
    assert oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle_b, sender=governor)
    
    # Test non-governor cannot cancel
    with boa.reverts("no perms"):
        oracle_registry.cancelPendingOraclePartnerUpdate(oracle_id, sender=bob)
    
    # Test successful cancellation
    assert oracle_registry.cancelPendingOraclePartnerUpdate(oracle_id, sender=governor)
    
    # Verify cancellation event
    log = filter_logs(oracle_registry, "AddyUpdateCancelled")[0]
    assert log.addyId == oracle_id
    assert log.newAddr == new_oracle_b.address
    assert log.prevAddr == new_oracle.address
    assert log.initiatedBlock == current_block
    assert log.confirmBlock == current_block + oracle_registry.addyChangeDelay()
    
    # Test cannot confirm cancelled update
    with boa.reverts():  # Empty revert as the assertion combines both checks
        oracle_registry.confirmOraclePartnerUpdate(oracle_id, sender=governor)


def test_disable_oracle_addr(oracle_registry, new_oracle, governor, bob):
    description = "Test Oracle Partner"
    # Register and confirm initial oracle
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    current_block = boa.env.evm.patch.block_number

    # Test non-governor cannot disable
    with boa.reverts("no perms"):
        oracle_registry.disableOraclePartnerAddr(oracle_id, sender=bob)

    # invalid id
    assert not oracle_registry.isValidOraclePartnerDisable(999)
    assert not oracle_registry.disableOraclePartnerAddr(999, sender=governor)

    # Test successful disable initiation
    assert oracle_registry.disableOraclePartnerAddr(oracle_id, sender=governor)
    
    # Verify pending event
    log = filter_logs(oracle_registry, "AddyDisablePending")[0]
    assert log.addyId == oracle_id
    assert log.addr == new_oracle.address
    assert log.confirmBlock == current_block + oracle_registry.addyChangeDelay()

    # Confirm disable after delay
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    assert oracle_registry.confirmOraclePartnerDisable(oracle_id, sender=governor)

    # Verify disable event
    log = filter_logs(oracle_registry, "AddyDisableConfirmed")[0]
    assert log.addr == new_oracle.address
    assert log.addyId == oracle_id
    assert log.version == 2
    assert log.description == description

    assert oracle_registry.getOraclePartnerAddr(oracle_id) == ZERO_ADDRESS
    assert oracle_registry.getOraclePartnerId(new_oracle.address) == 0
    
    info = oracle_registry.getOraclePartnerInfo(oracle_id)
    assert info.addr == ZERO_ADDRESS
    assert info.version == 2
    assert info.description == description
    assert info.lastModified == boa.env.evm.patch.timestamp
    
    # already disabled
    assert not oracle_registry.disableOraclePartnerAddr(oracle_id, sender=governor)


def test_cancel_pending_disable(oracle_registry, new_oracle, governor, bob):
    description = "Test Oracle Partner"
    # Register and confirm initial oracle
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    current_block = boa.env.evm.patch.block_number
    
    # Initiate disable
    assert oracle_registry.disableOraclePartnerAddr(oracle_id, sender=governor)
    
    # Test non-governor cannot cancel
    with boa.reverts("no perms"):
        oracle_registry.cancelPendingOraclePartnerDisable(oracle_id, sender=bob)
    
    # Test successful cancellation
    assert oracle_registry.cancelPendingOraclePartnerDisable(oracle_id, sender=governor)
    
    # Verify cancellation event
    log = filter_logs(oracle_registry, "AddyDisableCancelled")[0]
    assert log.addyId == oracle_id
    assert log.addr == new_oracle.address
    assert log.initiatedBlock == current_block
    assert log.confirmBlock == current_block + oracle_registry.addyChangeDelay()
    
    # Test cannot confirm cancelled disable
    with boa.reverts():  # Empty revert as the assertion combines both checks
        oracle_registry.confirmOraclePartnerDisable(oracle_id, sender=governor)


def test_set_oracle_change_delay(oracle_registry, governor, bob):
    min_delay = oracle_registry.MIN_ADDY_CHANGE_DELAY()
    max_delay = oracle_registry.MAX_ADDY_CHANGE_DELAY()
    
    # Test non-governor cannot set delay
    with boa.reverts("no perms"):
        oracle_registry.setOraclePartnerChangeDelay(min_delay + 1, sender=bob)
    
    # Test invalid delay values
    with boa.reverts():  # Empty revert as the assertion combines both checks
        oracle_registry.setOraclePartnerChangeDelay(min_delay - 1, sender=governor)
    with boa.reverts():  # Empty revert as the assertion combines both checks
        oracle_registry.setOraclePartnerChangeDelay(max_delay + 1, sender=governor)
    
    # Test successful delay update
    new_delay = min_delay + 1
    oracle_registry.setOraclePartnerChangeDelay(new_delay, sender=governor)
    assert oracle_registry.addyChangeDelay() == new_delay


def test_view_functions(oracle_registry, new_oracle, governor):
    description = "Test Oracle Partner"
    # Register and confirm initial oracle
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    # Test isValidNewOraclePartnerAddr
    assert not oracle_registry.isValidNewOraclePartnerAddr(new_oracle.address)  # Already registered
    assert not oracle_registry.isValidNewOraclePartnerAddr(ZERO_ADDRESS)  # Zero address
    
    # Test isValidOraclePartnerUpdate
    assert not oracle_registry.isValidOraclePartnerUpdate(oracle_id, new_oracle.address)  # Same address
    assert not oracle_registry.isValidOraclePartnerUpdate(0, new_oracle.address)  # Invalid oracle ID
    
    # Test isValidOraclePartnerDisable
    assert oracle_registry.isValidOraclePartnerDisable(oracle_id)
    assert not oracle_registry.isValidOraclePartnerDisable(0)  # Invalid oracle ID
    
    # Test isValidOraclePartnerId
    assert oracle_registry.isValidOraclePartnerId(oracle_id)
    assert not oracle_registry.isValidOraclePartnerId(0)
    assert not oracle_registry.isValidOraclePartnerId(999)  # Non-existent ID


def test_priority_oracle_partners(oracle_registry, new_oracle, new_oracle_b, governor, bob):
    description = "Test Oracle Partner"
    # Register two oracle partners
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    assert oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_b = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_b, sender=governor)
    
    assert oracle_id_a != 0 and oracle_id_b != 0

    # Test non-governor cannot set priority
    priority_ids = [oracle_id_a, oracle_id_b]
    with boa.reverts("no perms"):
        oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=bob)

    # Test setting valid priority oracle partners
    assert oracle_registry.areValidPriorityOraclePartnerIds(priority_ids)
    assert oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=governor)

    # Verify event
    log = filter_logs(oracle_registry, "PriorityOraclePartnerIdsModified")[0]
    assert log.numIds == len(priority_ids)

    # Test getting priority oracle partners
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == len(priority_ids)
    assert stored_priority_ids[0] == oracle_id_a
    assert stored_priority_ids[1] == oracle_id_b

    # Test invalid cases
    # Empty list
    assert not oracle_registry.areValidPriorityOraclePartnerIds([])
    assert not oracle_registry.setPriorityOraclePartnerIds([], sender=governor)

    # Invalid oracle IDs
    invalid_ids = [0, 999]  # Non-existent IDs
    assert not oracle_registry.areValidPriorityOraclePartnerIds(invalid_ids)
    assert not oracle_registry.setPriorityOraclePartnerIds(invalid_ids, sender=governor)

    # Test sanitization (duplicate IDs)
    duplicate_ids = [oracle_id_a, oracle_id_a, oracle_id_b]
    assert oracle_registry.setPriorityOraclePartnerIds(duplicate_ids, sender=governor)
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == 2  # Duplicates should be removed
    assert stored_priority_ids[0] == oracle_id_a
    assert stored_priority_ids[1] == oracle_id_b


def test_priority_oracle_partners_price_order(oracle_registry, new_oracle, new_oracle_b, governor, alpha_token):
    description = "Test Oracle Partner"
    # Register two oracle partners
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    assert oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_b = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_b, sender=governor)
    
    assert oracle_id_a != 0 and oracle_id_b != 0

    # Set priority order [A, B]
    priority_ids = [oracle_id_a, oracle_id_b]
    assert oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=governor)

    # Test that the priority order is respected when getting prices
    new_oracle.setPrice(alpha_token, 100, sender=governor) # a 
    new_oracle_b.setPrice(alpha_token, 200, sender=governor) # b 

    # For now we just verify the priority list is set correctly
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == 2
    assert stored_priority_ids[0] == oracle_id_a  # A should be checked first
    assert stored_priority_ids[1] == oracle_id_b  # B should be checked second

    assert oracle_registry.getPrice(alpha_token) == 100

    # Change priority order to [B, A]
    priority_ids = [oracle_id_b, oracle_id_a]
    assert oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=governor)
    
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == 2
    assert stored_priority_ids[0] == oracle_id_b  # B should be checked first
    assert stored_priority_ids[1] == oracle_id_a  # A should be checked second

    assert oracle_registry.getPrice(alpha_token) == 200


def test_stale_time(oracle_registry, governor, bob):
    # Test non-governor cannot set stale time
    with boa.reverts("no perms"):
        oracle_registry.setStaleTime(300, sender=bob)  # 5 minutes

    # Test invalid stale times
    MIN_STALE_TIME = 60 * 5  # 5 minutes
    MAX_STALE_TIME = 60 * 60 * 24 * 3  # 3 days

    # Too low
    assert not oracle_registry.isValidStaleTime(MIN_STALE_TIME - 1)
    assert not oracle_registry.setStaleTime(MIN_STALE_TIME - 1, sender=governor)

    # Too high
    assert not oracle_registry.isValidStaleTime(MAX_STALE_TIME + 1)
    assert not oracle_registry.setStaleTime(MAX_STALE_TIME + 1, sender=governor)

    # Test valid stale time
    valid_stale_time = 3600  # 1 hour
    assert oracle_registry.isValidStaleTime(valid_stale_time)
    assert oracle_registry.setStaleTime(valid_stale_time, sender=governor)

    # Verify event
    log = filter_logs(oracle_registry, "StaleTimeSet")[0]
    assert log.staleTime == valid_stale_time

    # Verify state
    assert oracle_registry.staleTime() == valid_stale_time


def test_stale_time_price_impact(oracle_registry, new_oracle, governor, alpha_token):
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    # Set initial price
    new_oracle.setPrice(alpha_token, 100, sender=governor)
    assert oracle_registry.getPrice(alpha_token) == 100

    # Set stale time to 1 hour
    stale_time = 3600  # 1 hour
    assert oracle_registry.setStaleTime(stale_time, sender=governor)

    # Move time forward by 30 minutes (within stale time)
    boa.env.time_travel(seconds=1800)
    assert oracle_registry.getPrice(alpha_token) == 100

    # Move time forward by another 31 minutes (beyond stale time)
    boa.env.time_travel(seconds=1860)
    # Price should now be stale and return 0
    assert oracle_registry.getPrice(alpha_token) == 0

    # should raise
    with boa.reverts("has price config, no price"):
        oracle_registry.getPrice(alpha_token, True)

    # Update price
    new_oracle.setPrice(alpha_token, 200, sender=governor)
    assert oracle_registry.getPrice(alpha_token) == 200


def test_usd_value_and_asset_amount(oracle_registry, new_oracle, governor, alpha_token):
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    # Set price to $2000
    new_oracle.setPrice(alpha_token, 2_000 * EIGHTEEN_DECIMALS, sender=governor)  # $2000 with 18 decimals
    
    # Test getUsdValue
    amount = 5 * EIGHTEEN_DECIMALS  # 5 tokens with 18 decimals
    expected_usd = 10_000 * EIGHTEEN_DECIMALS  # $10,000 with 18 decimals
    assert oracle_registry.getUsdValue(alpha_token, amount) == expected_usd

    # Test getAssetAmount
    usd_value = 4_000 * EIGHTEEN_DECIMALS  # $4000 with 18 decimals
    expected_amount = 2 * EIGHTEEN_DECIMALS  # 2 tokens with 18 decimals
    assert oracle_registry.getAssetAmount(alpha_token, usd_value) == expected_amount

    # Test edge cases
    assert oracle_registry.getUsdValue(alpha_token, 0) == 0
    assert oracle_registry.getUsdValue(ZERO_ADDRESS, amount) == 0
    assert oracle_registry.getAssetAmount(alpha_token, 0) == 0
    assert oracle_registry.getAssetAmount(ZERO_ADDRESS, usd_value) == 0

    # Test when no price available
    new_oracle.setPrice(alpha_token, 0, sender=governor)
    assert oracle_registry.getUsdValue(alpha_token, amount) == 0
    assert oracle_registry.getAssetAmount(alpha_token, usd_value) == 0


def test_usd_value_and_asset_amount_diff_decimals(oracle_registry, new_oracle, governor, charlie_token):
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    # Set price to $2000
    new_oracle.setPrice(charlie_token, 2_000 * EIGHTEEN_DECIMALS, sender=governor)  # $2000 with 18 decimals
    
    # Test getUsdValue
    amount = 5 * (10 ** charlie_token.decimals())  # 5 tokens
    expected_usd = 10_000 * EIGHTEEN_DECIMALS  # $10,000 with 18 decimals
    assert oracle_registry.getUsdValue(charlie_token, amount) == expected_usd

    # Test getAssetAmount
    usd_value = 4_000 * EIGHTEEN_DECIMALS  # $4000 with 18 decimals
    expected_amount = 2 * (10 ** charlie_token.decimals())  # 2 tokens
    assert oracle_registry.getAssetAmount(charlie_token, usd_value) == expected_amount


def test_eth_specific_functions(oracle_registry, new_oracle, governor):
    ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    # Set ETH price to $2000
    new_oracle.setPrice(ETH, 2_000 * EIGHTEEN_DECIMALS, sender=governor)  # $2000 with 18 decimals
    
    # Test getEthUsdValue
    amount = 5 * EIGHTEEN_DECIMALS  # 5 ETH
    expected_usd = 10_000 * EIGHTEEN_DECIMALS  # $10,000 with 18 decimals
    assert oracle_registry.getEthUsdValue(amount) == expected_usd

    # Test getEthAmount
    usd_value = 4_000 * EIGHTEEN_DECIMALS  # $4000 with 18 decimals
    expected_amount = 2 * EIGHTEEN_DECIMALS  # 2 ETH
    assert oracle_registry.getEthAmount(usd_value) == expected_amount


def test_has_price_feed(oracle_registry, new_oracle, new_oracle_b, governor, alpha_token, bravo_token):
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    assert oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_b = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_b, sender=governor)
    
    assert oracle_id_a != 0 and oracle_id_b != 0

    # Set up oracle A to have alpha_token feed
    assert not oracle_registry.hasPriceFeed(alpha_token)
    new_oracle.setPrice(alpha_token, 100 * EIGHTEEN_DECIMALS, sender=governor)  # $100 with 18 decimals
    assert oracle_registry.hasPriceFeed(alpha_token)

    # Set up oracle B to have bravo_token feed
    assert not oracle_registry.hasPriceFeed(bravo_token)
    new_oracle_b.setPrice(bravo_token, 50 * EIGHTEEN_DECIMALS, sender=governor)  # $50 with 18 decimals
    assert oracle_registry.hasPriceFeed(bravo_token)

    # Test token with no feed
    assert not oracle_registry.hasPriceFeed(ZERO_ADDRESS)


def test_priority_oracle_fallback(oracle_registry, addy_registry, new_oracle, new_oracle_b, governor, alpha_token):
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    assert oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_b = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_b, sender=governor)
    
    assert oracle_id_a != 0 and oracle_id_b != 0

    # Set priority order [A, B]
    priority_ids = [oracle_id_a, oracle_id_b]
    assert oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=governor)

    # Set prices
    new_oracle.setPrice(alpha_token, 0, sender=governor)  # A returns 0
    new_oracle_b.setPrice(alpha_token, 200, sender=governor)  # B has valid price

    # Should fall back to B's price since A returns 0
    assert oracle_registry.getPrice(alpha_token) == 200

    # Test fallback to non-priority oracle
    # Register a third oracle C that's not in priority list
    new_oracle_c = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="new_oracle_partner_c")
    assert oracle_registry.registerNewOraclePartner(new_oracle_c, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_c = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_c, sender=governor)
    assert oracle_id_c != 0

    # Set all priority oracle prices to 0
    new_oracle.setPrice(alpha_token, 0, sender=governor)  # A returns 0
    new_oracle_b.setPrice(alpha_token, 0, sender=governor)  # B returns 0
    new_oracle_c.setPrice(alpha_token, 300, sender=governor)  # C has valid price

    # Should fall back to C's price since A and B return 0
    assert oracle_registry.getPrice(alpha_token) == 300


def test_oracle_partner_registration_edge_cases(oracle_registry, new_oracle, governor):
    description_a = "Test Oracle Partner A"
    description_b = "Test Oracle Partner B"

    # First registration
    assert oracle_registry.registerNewOraclePartner(new_oracle, description_a, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id_a != 0
    
    # Try to register same oracle with different description
    assert not oracle_registry.registerNewOraclePartner(new_oracle, description_b, sender=governor)

    # Verify original registration unchanged
    info = oracle_registry.getOraclePartnerInfo(oracle_id_a)
    assert info.description == description_a  # Should keep original description

    # Test registration after disabling
    assert oracle_registry.disableOraclePartnerAddr(oracle_id_a, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    assert oracle_registry.confirmOraclePartnerDisable(oracle_id_a, sender=governor)
    
    # After disabling, we can update the same oracle ID
    assert oracle_registry.updateOraclePartnerAddr(oracle_id_a, new_oracle, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    assert oracle_registry.confirmOraclePartnerUpdate(oracle_id_a, sender=governor)

    assert oracle_registry.getOraclePartnerAddr(oracle_id_a) == new_oracle.address
    assert oracle_registry.getOraclePartnerId(new_oracle.address) == oracle_id_a


def test_get_price_edge_cases(oracle_registry, new_oracle, governor, alpha_token):
    description = "Test Oracle Partner"
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    assert oracle_id != 0

    # Test getPrice with _shouldRaise=True when no price feed exists
    # First set a price to ensure the oracle has a feed configured
    new_oracle.setPrice(alpha_token, 100, sender=governor)
    assert oracle_registry.hasPriceFeed(alpha_token)  # Verify feed exists
    
    # Set stale time and move time forward to make price stale
    stale_time = 3600  # 1 hour
    assert oracle_registry.setStaleTime(stale_time, sender=governor)
    boa.env.time_travel(seconds=stale_time + 1)
    
    # Now the price should be stale but feed exists
    with boa.reverts("has price config, no price"):
        oracle_registry.getPrice(alpha_token, True)

    # Test getPrice with ETH address directly
    ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    new_oracle.setPrice(ETH, 2000 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(ETH) == 2000 * EIGHTEEN_DECIMALS


def test_max_oracle_partners(oracle_registry, addy_registry, governor):
    description = "Test Oracle Partner"
    MAX_PARTNERS = 10  # Based on MAX_PRIORITY_PARTNERS constant
    
    # Register maximum number of oracle partners
    oracle_ids = []
    for i in range(MAX_PARTNERS):
        new_oracle = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name=f"oracle_{i}")
        assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
        boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
        oracle_id = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
        oracle_ids.append(oracle_id)
    
    # Test setting priority with all partners
    assert oracle_registry.setPriorityOraclePartnerIds(oracle_ids, sender=governor)
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == MAX_PARTNERS
    assert stored_priority_ids == oracle_ids


def test_priority_oracle_partners_edge_cases(oracle_registry, new_oracle, new_oracle_b, governor, addy_registry):
    description = "Test Oracle Partner"
    # Register two oracle partners
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    assert oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_b = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_b, sender=governor)
    
    # Set priority order [A, B]
    priority_ids = [oracle_id_a, oracle_id_b]
    assert oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=governor)

    # Disable oracle A
    assert oracle_registry.disableOraclePartnerAddr(oracle_id_a, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    assert oracle_registry.confirmOraclePartnerDisable(oracle_id_a, sender=governor)

    # Test priority list with disabled partner
    # The contract doesn't automatically remove disabled partners from priority list
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == 2  # Both partners remain in the list
    assert stored_priority_ids[0] == oracle_id_a
    assert stored_priority_ids[1] == oracle_id_b

    # Update oracle B
    new_oracle_c = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="new_oracle_c")
    assert oracle_registry.updateOraclePartnerAddr(oracle_id_b, new_oracle_c, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    assert oracle_registry.confirmOraclePartnerUpdate(oracle_id_b, sender=governor)

    # Test priority list with updated partner
    stored_priority_ids = oracle_registry.getPriorityOraclePartnerIds()
    assert len(stored_priority_ids) == 2
    assert stored_priority_ids[0] == oracle_id_a
    assert stored_priority_ids[1] == oracle_id_b  # ID should remain the same


def test_stale_time_edge_cases(oracle_registry, new_oracle, new_oracle_b, governor, alpha_token):
    description = "Test Oracle Partner"
    # Register two oracle partners
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_a = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle, sender=governor)
    
    assert oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
    boa.env.time_travel(blocks=oracle_registry.addyChangeDelay() + 1)
    oracle_id_b = oracle_registry.confirmNewOraclePartnerRegistration(new_oracle_b, sender=governor)
    
    # Set priority order [A, B]
    priority_ids = [oracle_id_a, oracle_id_b]
    assert oracle_registry.setPriorityOraclePartnerIds(priority_ids, sender=governor)

    # Set stale time to 1 hour
    stale_time = 3600  # 1 hour
    assert oracle_registry.setStaleTime(stale_time, sender=governor)

    # Set prices
    new_oracle.setPrice(alpha_token, 100, sender=governor)
    new_oracle_b.setPrice(alpha_token, 200, sender=governor)

    # Test exactly at stale time boundary
    boa.env.time_travel(seconds=stale_time)
    assert oracle_registry.getPrice(alpha_token) == 100  # Should still be valid

    # Test just beyond stale time boundary
    boa.env.time_travel(seconds=1)
    # When a price is stale, the contract returns 0 instead of falling back
    assert oracle_registry.getPrice(alpha_token) == 0  # Should be stale

    # Test with priority oracle partners
    # Move time back to valid range
    boa.env.time_travel(seconds=-1)
    assert oracle_registry.getPrice(alpha_token) == 100  # Should use priority oracle

    # Make priority oracle stale
    boa.env.time_travel(seconds=stale_time + 1)
    # When a price is stale, the contract returns 0 instead of falling back
    assert oracle_registry.getPrice(alpha_token) == 0  # Should be stale

