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
    assert oracle_registry.numOraclePartners() == 1


def test_register_new_oracle_partner(oracle_registry, new_oracle, governor):
    description = "Test Oracle Partner"

    assert oracle_registry.isValidNewOraclePartnerAddr(new_oracle)
    
    # Test successful registration
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    assert oracle_id  == 1

    # Verify event
    log = filter_logs(oracle_registry, "NewOraclePartnerRegistered")[0]
    assert log.addr == new_oracle.address
    assert log.oraclePartnerId == oracle_id
    assert log.description == description

    assert oracle_registry.isValidOraclePartnerAddr(new_oracle.address)
    assert oracle_registry.getOraclePartnerId(new_oracle.address) == oracle_id
    assert oracle_registry.getOraclePartnerAddr(oracle_id) == new_oracle.address
    assert oracle_registry.getOraclePartnerDescription(oracle_id) == description
    assert oracle_registry.getNumOraclePartners() == 1
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
    assert oracle_registry.registerNewOraclePartner(ZERO_ADDRESS, description, sender=governor) == 0
    
    # Test cannot register same lego twice
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor) != 0
    assert oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor) == 0


def test_update_oracle_addr(oracle_registry, new_oracle, new_oracle_b, governor, bob):
    description = "Test Oracle Partner"
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    assert oracle_id != 0

    # Test non-governor cannot update
    with boa.reverts("no perms"):
        oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle_b, sender=bob)

    # invalid id
    assert not oracle_registry.isValidOraclePartnerUpdate(999, new_oracle_b)
    assert not oracle_registry.updateOraclePartnerAddr(999, new_oracle_b, sender=governor)

    # same address
    assert not oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle, sender=governor)

    # Test successful update
    assert oracle_registry.updateOraclePartnerAddr(oracle_id, new_oracle_b, sender=governor)

    log = filter_logs(oracle_registry, "OraclePartnerAddrUpdated")[0]
    assert log.newAddr == new_oracle_b.address
    assert log.prevAddr == new_oracle.address
    assert log.oraclePartnerId == oracle_id
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
    

def test_disable_oracle_addr(oracle_registry, new_oracle, governor, bob):
    description = "Test Oracle Partner"
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    assert oracle_id != 0

    # Test non-governor cannot disable
    with boa.reverts("no perms"):
        oracle_registry.disableOraclePartnerAddr(oracle_id, sender=bob)

    # invalid id
    assert not oracle_registry.isValidOraclePartnerDisable(999)
    assert not oracle_registry.disableOraclePartnerAddr(999, sender=governor)

    # Test successful disable
    assert oracle_registry.disableOraclePartnerAddr(oracle_id, sender=governor)

    log = filter_logs(oracle_registry, "OraclePartnerAddrDisabled")[0]
    assert log.prevAddr == new_oracle.address
    assert log.oraclePartnerId == oracle_id
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


def test_view_functions(oracle_registry, new_oracle, governor):
    description = "Test Oracle Partner"
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    
    # Test isValidNewOraclePartnerAddr
    assert not oracle_registry.isValidNewOraclePartnerAddr(new_oracle.address)  # Already registered
    assert not oracle_registry.isValidNewOraclePartnerAddr(ZERO_ADDRESS)  # Zero address
    
    # Test isValidOraclePartnerUpdate
    assert not oracle_registry.isValidOraclePartnerUpdate(oracle_id, new_oracle.address)  # Same address
    assert not oracle_registry.isValidOraclePartnerUpdate(0, new_oracle.address)  # Invalid lego ID
    
    # Test isValidOraclePartnerDisable
    assert oracle_registry.isValidOraclePartnerDisable(oracle_id)
    assert not oracle_registry.isValidOraclePartnerDisable(0)  # Invalid lego ID
    
    # Test isValidOraclePartnerId
    assert oracle_registry.isValidOraclePartnerId(oracle_id)
    assert not oracle_registry.isValidOraclePartnerId(0)
    assert not oracle_registry.isValidOraclePartnerId(999)  # Non-existent ID


def test_priority_oracle_partners(oracle_registry, new_oracle, new_oracle_b, governor, bob):
    description = "Test Oracle Partner"
    # Register two oracle partners
    oracle_id_a = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    oracle_id_b = oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
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
    oracle_id_a = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    oracle_id_b = oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
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
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
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
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
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
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
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
    oracle_id = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
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
    oracle_id_a = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    oracle_id_b = oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
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
    oracle_id_a = oracle_registry.registerNewOraclePartner(new_oracle, description, sender=governor)
    oracle_id_b = oracle_registry.registerNewOraclePartner(new_oracle_b, description, sender=governor)
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
    oracle_id_c = oracle_registry.registerNewOraclePartner(new_oracle_c, description, sender=governor)
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
    oracle_id_a = oracle_registry.registerNewOraclePartner(new_oracle, description_a, sender=governor)
    assert oracle_id_a != 0
    
    # Try to register same oracle with different description
    oracle_id_b = oracle_registry.registerNewOraclePartner(new_oracle, description_b, sender=governor)
    assert oracle_id_b == 0  # Should fail as address already registered

    # Verify original registration unchanged
    info = oracle_registry.getOraclePartnerInfo(oracle_id_a)
    assert info.description == description_a  # Should keep original description

    # Test registration after disabling
    assert oracle_registry.disableOraclePartnerAddr(oracle_id_a, sender=governor)
    
    # oracle id already been set on new_oracle, can only update same id
    with boa.reverts("set id failed"):
        oracle_registry.registerNewOraclePartner(new_oracle, description_b, sender=governor)

    assert oracle_registry.updateOraclePartnerAddr(oracle_id_a, new_oracle, sender=governor)

    assert oracle_registry.getOraclePartnerAddr(oracle_id_a) == new_oracle.address
    assert oracle_registry.getOraclePartnerId(new_oracle.address) == oracle_id_a

