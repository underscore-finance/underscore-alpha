import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, WITHDRAWAL_UINT256, SWAP_UINT256, CLAIM_REWARDS_UINT256
from conf_utils import filter_logs


#########
# Tests #
#########


def test_init(price_sheets, governor, addy_registry):
    """Test contract initialization"""
    assert price_sheets.ADDY_REGISTRY() == addy_registry.address
    assert price_sheets.protocolRecipient() == governor
    assert price_sheets.isActivated()


def test_activation(price_sheets, governor, sally):
    """Test activation control"""
    # Only governor can deactivate
    with boa.reverts("no perms"):
        price_sheets.activate(False, sender=sally)
    
    # Governor can deactivate
    price_sheets.activate(False, sender=governor)
    log = filter_logs(price_sheets, "PriceSheetsActivated")[0]
    assert log.isActivated == False
    assert not price_sheets.isActivated()
    
    # Governor can reactivate
    price_sheets.activate(True, sender=governor)
    log = filter_logs(price_sheets, "PriceSheetsActivated")[0]
    assert log.isActivated == True
    assert price_sheets.isActivated()


def test_protocol_recipient(price_sheets, governor, sally, bob):
    """Test protocol recipient management"""
    # Only governor can set recipient
    with boa.reverts("no perms"):
        price_sheets.setProtocolRecipient(bob, sender=sally)
    
    # Cannot set zero address
    with boa.reverts("invalid recipient"):
        price_sheets.setProtocolRecipient(ZERO_ADDRESS, sender=governor)
    
    # Set new recipient
    assert price_sheets.setProtocolRecipient(bob, sender=governor)
    log = filter_logs(price_sheets, "ProtocolRecipientSet")[0]
    assert log.recipient == bob

    assert price_sheets.protocolRecipient() == bob


def test_subscription_price_validation(price_sheets, alpha_token):
    """Test subscription price validation"""
    # Valid case
    assert price_sheets.isValidSubPrice(
        alpha_token,  # asset
        1000,   # usdValue
        43_200, # trialPeriod (1 day)
        302_400 # payPeriod (7 days)
    )
    
    # Invalid cases
    assert not price_sheets.isValidSubPrice(
        ZERO_ADDRESS,  # invalid asset
        1000,
        43_200,
        302_400
    )
    
    assert not price_sheets.isValidSubPrice(
        alpha_token,
        0,      # invalid usdValue
        43_200,
        302_400
    )
    
    assert not price_sheets.isValidSubPrice(
        alpha_token,
        1000,
        43_199,  # trial period too short
        302_400
    )
    
    assert not price_sheets.isValidSubPrice(
        alpha_token,
        1000,
        1_296_001,  # trial period too long
        302_400
    )
    
    assert not price_sheets.isValidSubPrice(
        alpha_token,
        1000,
        43_200,
        302_399  # pay period too short
    )
    
    assert not price_sheets.isValidSubPrice(
        alpha_token,
        1000,
        43_200,
        3_900_001  # pay period too long
    )


def test_agent_subscription_price(price_sheets, governor, bob_agent, alpha_token, bob):
    """Test agent subscription price management"""
    # Only governor can set prices
    with boa.reverts("no perms"):
        price_sheets.setAgentSubPrice(
            bob_agent,  # agent
            alpha_token,    # asset
            1000,   # usdValue
            43_200, # trialPeriod
            302_400,# payPeriod
            sender=bob
        )
    
    # Cannot set for zero address agent
    with boa.reverts("agent not registered"):
        price_sheets.setAgentSubPrice(
            ZERO_ADDRESS,
            alpha_token,
            1000,
            43_200,
            302_400,
            sender=governor
        )
    
    # Set valid price
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        302_400,
        sender=governor
    )
    log = filter_logs(price_sheets, "AgentSubPriceSet")[0]
    assert log.agent == bob_agent
    assert log.asset == alpha_token.address
    assert log.usdValue == 1000
    assert log.trialPeriod == 43_200
    assert log.payPeriod == 302_400

    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    assert info.trialPeriod == 43_200
    assert info.payPeriod == 302_400
    
    # Remove price
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.asset == ZERO_ADDRESS
    assert info.usdValue == 0


def test_protocol_subscription_price(price_sheets, governor, alpha_token):
    """Test protocol subscription price management"""
    # Set valid price
    assert price_sheets.setProtocolSubPrice(
        alpha_token,  # asset
        1000,   # usdValue
        43_200, # trialPeriod
        302_400,# payPeriod
        sender=governor
    )
    log = filter_logs(price_sheets, "ProtocolSubPriceSet")[0]
    assert log.asset == alpha_token.address
    assert log.usdValue == 1000
    assert log.trialPeriod == 43_200
    assert log.payPeriod == 302_400
    
    info = price_sheets.protocolSubPriceData()
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    assert info.trialPeriod == 43_200
    assert info.payPeriod == 302_400
    
    # Remove price
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    log = filter_logs(price_sheets, "ProtocolSubPriceRemoved")[0]
    assert log.asset == alpha_token.address
    assert log.usdValue == 1000
    assert log.trialPeriod == 43_200
    assert log.payPeriod == 302_400

    info = price_sheets.protocolSubPriceData()
    assert info.asset == ZERO_ADDRESS
    assert info.usdValue == 0


def test_transaction_price_validation(price_sheets):
    """Test transaction price validation"""
    # Valid case
    assert price_sheets.isValidTxPriceSheet(
        100,    # yieldFee
        200,    # swapFee
        300,    # claimRewardsFee
    )
    
    # Invalid cases - fees too high (>20.00%)
    assert not price_sheets.isValidTxPriceSheet(
        2001,   # yieldFee too high (>20.00%)
        200,
        300
    )
    
    assert not price_sheets.isValidTxPriceSheet(
        100,
        2001,   # swapFee too high (>20.00%)
        300
    )
    
    assert not price_sheets.isValidTxPriceSheet(
        100,
        200,
        2001    # claimRewardsFee too high (>20.00%)
    )


def test_protocol_transaction_price(price_sheets, governor, bob):
    """Test protocol transaction price management"""
    # Set valid price sheet
    assert price_sheets.setProtocolTxPriceSheet(
        100,    # yieldFee (1.00%)
        200,    # swapFee (2.00%)
        300,    # claimRewardsFee (3.00%)
        sender=governor
    )
    log = filter_logs(price_sheets, "ProtocolTxPriceSheetSet")[0]
    assert log.yieldFee == 100
    assert log.swapFee == 200
    assert log.claimRewardsFee == 300
    
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.yieldFee == 100
    assert sheet.swapFee == 200
    assert sheet.claimRewardsFee == 300
    
    # Test fee calculations
    fee, recipient = price_sheets.getTransactionFeeData(bob, WITHDRAWAL_UINT256)
    assert fee == 100  # 1.00%
    assert recipient == price_sheets.protocolRecipient()
    
    fee, recipient = price_sheets.getTransactionFeeData(bob, SWAP_UINT256)
    assert fee == 200  # 2.00%
    assert recipient == price_sheets.protocolRecipient()
    
    fee, recipient = price_sheets.getTransactionFeeData(bob, CLAIM_REWARDS_UINT256)
    assert fee == 300  # 3.00%
    assert recipient == price_sheets.protocolRecipient()
    
    # Remove price sheet
    assert price_sheets.removeProtocolTxPriceSheet(sender=governor)
    log = filter_logs(price_sheets, "ProtocolTxPriceSheetRemoved")[0]
    assert log.yieldFee == 100
    assert log.swapFee == 200
    assert log.claimRewardsFee == 300

    sheet = price_sheets.protocolTxPriceData()
    assert sheet.yieldFee == 0
    assert sheet.swapFee == 0
    assert sheet.claimRewardsFee == 0


def test_deactivated_state(price_sheets, governor, bob_agent, bob_agent_dev, alpha_token, sally):
    """Test all operations in deactivated state"""
    
    # Deactivate contract
    price_sheets.activate(False, sender=governor)
    
    # many operations should fail when deactivated
    with boa.reverts("not active"):
        price_sheets.setAgentSubPrice(
            bob_agent,
            alpha_token,
            1000,
            43_200,
            302_400,
            sender=bob_agent_dev
        )


def test_edge_cases(price_sheets, governor, bob_agent, alpha_token, sally):
    """Test edge cases and boundary conditions"""
    
    # Test removing non-existent price sheets
    with boa.reverts("agent not registered"):
        price_sheets.removeAgentSubPrice(sally, sender=governor)  # non-existent agent
    
    # Set and then remove protocol tx price sheet
    price_sheets.setProtocolTxPriceSheet(
        100, 200, 300,
        sender=governor
    )
    
    # First removal should work
    price_sheets.removeProtocolTxPriceSheet(sender=governor)
    
    # Check that the price sheet is empty
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.yieldFee == 0
    assert sheet.swapFee == 0
    assert sheet.claimRewardsFee == 0
    
    # Second removal should also work (the function always returns True)
    price_sheets.removeProtocolTxPriceSheet(sender=governor)

    # Test setting invalid trial/pay periods
    assert not price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_199,     # too short trial period
        302_400,
        sender=governor
    )

    assert not price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        302_399,    # too short pay period
        sender=governor
    )


def test_subscription_period_boundaries(price_sheets, governor, bob_agent, alpha_token):
    """Test subscription period boundary conditions"""
    
    # Test exact minimum trial period (1 day)
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,  # MIN_TRIAL_PERIOD (1 day)
        302_400,
        sender=governor
    )
    
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.trialPeriod == 43_200
    
    # Test exact maximum trial period (1 month)
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        1_296_000,  # MAX_TRIAL_PERIOD (1 month)
        302_400,
        sender=governor
    )
    
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.trialPeriod == 1_296_000
    
    # Test slightly above maximum trial period
    assert not price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        1_296_001,  # MAX_TRIAL_PERIOD + 1
        302_400,
        sender=governor
    )
    
    # Test exact minimum pay period (7 days)
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        302_400,  # MIN_PAY_PERIOD (7 days)
        sender=governor
    )
    
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.payPeriod == 302_400
    
    # Test exact maximum pay period (3 months)
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        3_900_000,  # MAX_PAY_PERIOD (3 months)
        sender=governor
    )
    
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.payPeriod == 3_900_000
    
    # Test slightly above maximum pay period
    assert not price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        3_900_001,  # MAX_PAY_PERIOD + 1
        sender=governor
    )


def test_agent_sub_pricing_enable_disable(price_sheets, governor, bob_agent, alpha_token, sally):
    """Test enabling and disabling agent subscription pricing"""
    
    # Only governor can enable/disable
    with boa.reverts("no perms"):
        price_sheets.setAgentSubPricingEnabled(True, sender=sally)
    
    # No change if already in desired state
    with boa.reverts("no change"):
        price_sheets.setAgentSubPricingEnabled(False, sender=governor)
    
    # Enable agent subscription pricing
    assert price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    log = filter_logs(price_sheets, "AgentSubPricingEnabled")[0]
    assert log.isEnabled == True
    assert price_sheets.isAgentSubPricingEnabled()
    
    # Set agent subscription price
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,   # usdValue
        43_200, # trialPeriod
        302_400,# payPeriod
        sender=governor
    )
    
    # Verify subscription info is returned when enabled
    info = price_sheets.getAgentSubPriceData(bob_agent)
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    
    # Disable agent subscription pricing
    assert price_sheets.setAgentSubPricingEnabled(False, sender=governor)
    log = filter_logs(price_sheets, "AgentSubPricingEnabled")[0]
    assert log.isEnabled == False
    assert not price_sheets.isAgentSubPricingEnabled()
    
    # Verify no subscription info is returned when disabled
    info = price_sheets.getAgentSubPriceData(bob_agent)
    assert info.asset == ZERO_ADDRESS
    assert info.usdValue == 0


def test_price_change_delay(price_sheets, governor, sally):
    """Test setting and managing price change delay"""
    
    # Only governor can set delay
    with boa.reverts("no perms"):
        price_sheets.setPriceChangeDelay(43_200, sender=sally)
    
    # Cannot set delay less than minimum buffer
    with boa.reverts("invalid delay"):
        price_sheets.setPriceChangeDelay(43_199, sender=governor)
    
    # Set valid delay
    assert price_sheets.setPriceChangeDelay(43_200, sender=governor)
    log = filter_logs(price_sheets, "PriceChangeDelaySet")[0]
    assert log.delayBlocks == 43_200
    assert price_sheets.priceChangeDelay() == 43_200
    
    # Can set to zero to disable delay
    assert price_sheets.setPriceChangeDelay(0, sender=governor)
    assert price_sheets.priceChangeDelay() == 0


def test_pending_agent_sub_price(price_sheets, governor, bob_agent, alpha_token):
    """Test setting and finalizing pending agent subscription prices"""

    delay = 43_200

    # Set initial delay
    price_sheets.setPriceChangeDelay(delay, sender=governor)
    assert price_sheets.priceChangeDelay() == delay
    
    # Set pending subscription price
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,   # usdValue
        43_200, # trialPeriod
        302_400,# payPeriod
        sender=governor
    )
    
    # Verify pending subscription price is set
    pending = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending.subInfo.asset == alpha_token.address
    assert pending.subInfo.usdValue == 1000
    assert pending.subInfo.trialPeriod == 43_200
    assert pending.subInfo.payPeriod == 302_400
    assert pending.effectiveBlock == boa.env.evm.patch.block_number + delay
    
    # Cannot finalize before delay
    with boa.reverts("time delay not reached"):
        price_sheets.finalizePendingAgentSubPrice(bob_agent)
    
    # Advance blocks
    boa.env.time_travel(blocks=delay)
    
    # Now can finalize
    assert price_sheets.finalizePendingAgentSubPrice(bob_agent)
    
    # Verify subscription price is set and pending is cleared
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    assert info.trialPeriod == 43_200
    assert info.payPeriod == 302_400
    
    pending = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending.effectiveBlock == 0


def test_pending_price_change_edge_cases(price_sheets, governor, bob_agent, alpha_token, sally):
    """Test edge cases for pending price changes"""
    
    delay = 43_200

    # Set initial delay
    price_sheets.setPriceChangeDelay(delay, sender=governor)
    
    # Cannot finalize non-existent pending changes
    with boa.reverts("time delay not reached"):
        price_sheets.finalizePendingAgentSubPrice(bob_agent)
    
    # Set pending changes
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000, 43_200, 302_400,
        sender=governor
    )
    
    # Advance blocks
    boa.env.time_travel(blocks=delay)
    
    # anyone can finalize
    assert price_sheets.finalizePendingAgentSubPrice(bob_agent, sender=sally)
    
    # Setting new pending changes overwrites old ones
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        2000, 43_200, 302_400,
        sender=governor
    )
    
    pending_sub = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending_sub.subInfo.usdValue == 2000


def test_zero_delay_price_changes(price_sheets, governor, bob_agent, alpha_token):
    """Test price changes when delay is set to zero"""
    
    # Set zero delay
    price_sheets.setPriceChangeDelay(0, sender=governor)
    assert price_sheets.priceChangeDelay() == 0
    
    # Subscription price changes should take effect immediately
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000, 43_200, 302_400,
        sender=governor
    )
    
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.usdValue == 1000
    
    pending = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending.effectiveBlock == 0


def test_agent_owner_permissions(price_sheets, governor, bob_agent, bob_agent_dev, sally, alpha_token):
    """Test agent owner permissions for setting prices"""
    
    # Enable pricing features
    price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    
    # Test 1: Agent owner can set subscription price when activated
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,  # trial period
        302_400, # pay period
        sender=bob_agent_dev  # bob_agent_dev is the owner
    )
    
    # Verify subscription was set
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    
    # Test 3: Non-owner cannot set prices
    with boa.reverts("no perms"):
        price_sheets.setAgentSubPrice(
            bob_agent,
            alpha_token,
            2000,
            43_200,
            302_400,
            sender=sally
        )
    
    # Test 4: Governor can still set prices
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        2000,
        43_200,
        302_400,
        sender=governor
    )
    
    # Test 5: Agent owner cannot set prices when contract is deactivated
    price_sheets.activate(False, sender=governor)
    
    with boa.reverts("not active"):
        price_sheets.setAgentSubPrice(
            bob_agent,
            alpha_token,
            3000,
            43_200,
            302_400,
            sender=bob_agent_dev
        )
    
    # Governor can still set prices when deactivated
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        3000,
        43_200,
        302_400,
        sender=governor
    )


def test_agent_owner_pending_price_changes(price_sheets, governor, bob_agent, bob_agent_dev, sally, alpha_token):
    """Test agent owner permissions with pending price changes"""
    
    # Set price change delay
    delay = 43_200
    price_sheets.setPriceChangeDelay(delay, sender=governor)
    
    # Agent owner can set pending price changes
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        302_400,
        sender=bob_agent_dev
    )
    
    # Verify pending sub price is set
    pending_sub = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending_sub.subInfo.usdValue == 1000
    assert pending_sub.effectiveBlock == boa.env.evm.patch.block_number + delay
    
    # Anyone can finalize pending changes after delay
    boa.env.time_travel(blocks=delay)
    
    assert price_sheets.finalizePendingAgentSubPrice(bob_agent, sender=sally)
    
    # Verify changes are applied
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.usdValue == 1000


def test_agent_owner_zero_delay_changes(price_sheets, governor, bob_agent, bob_agent_dev, alpha_token):
    """Test agent owner permissions with zero delay price changes"""
    
    # Set zero delay
    price_sheets.setPriceChangeDelay(0, sender=governor)
    
    # Changes should take effect immediately for agent owner
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,
        43_200,
        302_400,
        sender=bob_agent_dev
    )
    
    # Verify immediate effect
    info = price_sheets.agentSubPriceData(bob_agent)
    assert info.usdValue == 1000
    
    # No pending changes
    pending = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending.effectiveBlock == 0


def test_combined_sub_data(price_sheets, governor, bob_agent, alpha_token, oracle_registry):
    """Test the getCombinedSubData function and subscription payment logic"""
    
    # Set protocol recipient
    price_sheets.setProtocolRecipient(governor, sender=governor)
    
    # Set up protocol subscription
    price_sheets.setProtocolSubPrice(
        alpha_token,  # asset
        10_00,   # usdValue ($10)
        43_200,  # trialPeriod (1 day)
        302_400, # payPeriod (7 days)
        sender=governor
    )
    
    # Set up agent subscription
    price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        5_00,    # usdValue ($5)
        43_200,  # trialPeriod (1 day)
        302_400, # payPeriod (7 days)
        sender=governor
    )
    
    # Test initial state (both in trial period)
    protocol_data, agent_data = price_sheets.getCombinedSubData(
        governor,  # user
        bob_agent, # agent
        0,         # agentPaidThru (0 means not paid yet, should start trial)
        0,         # protocolPaidThru (0 means not paid yet, should start trial)
        oracle_registry
    )
    
    # Verify trial period setup
    assert protocol_data.paidThroughBlock == boa.env.evm.patch.block_number + 43_200
    assert agent_data.paidThroughBlock == boa.env.evm.patch.block_number + 43_200
    assert protocol_data.didChange == True
    assert agent_data.didChange == True
    assert protocol_data.amount == 0  # No payment during trial
    assert agent_data.amount == 0     # No payment during trial
    # Note: protocol_data.recipient is only set when amount != 0
    assert agent_data.recipient == bob_agent
    
    # Test subscription removal
    price_sheets.removeProtocolSubPrice(sender=governor)
    price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    
    protocol_data, agent_data = price_sheets.getCombinedSubData(
        governor,
        bob_agent,
        boa.env.evm.patch.block_number + 302_400,  # Previously paid through
        boa.env.evm.patch.block_number + 302_400,  # Previously paid through
        oracle_registry
    )
    
    # Verify subscriptions were removed
    assert protocol_data.paidThroughBlock == 0
    assert agent_data.paidThroughBlock == 0
    assert protocol_data.didChange == True
    assert agent_data.didChange == True
    assert protocol_data.amount == 0
    assert agent_data.amount == 0


def test_unknown_action_type(price_sheets, governor, bob):
    """Test transaction fee calculation with unknown action type"""
    
    # Set up protocol transaction price sheet
    price_sheets.setProtocolTxPriceSheet(
        100,    # yieldFee (1.00%)
        200,    # swapFee (2.00%)
        300,    # claimRewardsFee (3.00%)
        sender=governor
    )
    
    # Test with a valid action type
    fee, recipient = price_sheets.getTransactionFeeData(bob, WITHDRAWAL_UINT256)
    assert fee == 100  # 1.00%
    assert recipient == price_sheets.protocolRecipient()
    
    # Test with an unknown action type (using a value outside the defined enum range)
    unknown_action_type = 99  # Some value not defined in ActionType enum
    fee, recipient = price_sheets.getTransactionFeeData(bob, unknown_action_type)
    assert fee == 0  # Should return 0 for unknown action types
    assert recipient == price_sheets.protocolRecipient()


def test_subscription_payment_calculation_with_different_assets(price_sheets, governor, bob_agent, alpha_token, bravo_token, oracle_registry, oracle_custom):
    """Test subscription payment calculation with different assets"""
    # Set up oracle prices
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)  # 1 USD
    oracle_custom.setPrice(bravo_token.address, 2 * EIGHTEEN_DECIMALS, sender=governor)  # 2 USD
    
    # Set protocol subscription in alpha_token
    price_sheets.setProtocolSubPrice(
        alpha_token,
        10 * EIGHTEEN_DECIMALS,  # 10 USD
        43_200,                  # trial period
        302_400,                 # pay period
        sender=governor
    )
    
    # Set agent subscription in bravo_token
    price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    price_sheets.setAgentSubPrice(
        bob_agent,
        bravo_token,
        5 * EIGHTEEN_DECIMALS,   # 5 USD
        43_200,                  # trial period
        302_400,                 # pay period
        sender=governor
    )
    
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Get subscription data
    protocol_data, agent_data = price_sheets.getCombinedSubData(
        governor,
        bob_agent,
        boa.env.evm.patch.block_number - 43_200,  # Trial period started
        boa.env.evm.patch.block_number - 43_200,  # Trial period started
        oracle_registry
    )
    
    # Verify protocol subscription payment amount (10 USD in alpha_token)
    assert protocol_data.asset == alpha_token.address
    assert protocol_data.amount == 10 * EIGHTEEN_DECIMALS  # 10 alpha_tokens (1 USD each)
    assert protocol_data.usdValue == 10 * EIGHTEEN_DECIMALS
    
    # Verify agent subscription payment amount (5 USD in bravo_token)
    assert agent_data.asset == bravo_token.address
    assert agent_data.amount == 2.5 * EIGHTEEN_DECIMALS  # 2.5 bravo_tokens (2 USD each)
    assert agent_data.usdValue == 5 * EIGHTEEN_DECIMALS


def test_subscription_payment_calculation_with_zero_oracle_price(price_sheets, governor, bob_agent, alpha_token, oracle_registry, oracle_custom):
    """Test subscription payment calculation when oracle returns zero price"""
    # Set up protocol subscription
    price_sheets.setProtocolSubPrice(
        alpha_token,
        10 * EIGHTEEN_DECIMALS,  # 10 USD
        43_200,                  # trial period
        302_400,                 # pay period
        sender=governor
    )
    
    # Set up agent subscription
    price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,   # 5 USD
        43_200,                  # trial period
        302_400,                 # pay period
        sender=governor
    )
    
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Set oracle price to zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    
    # Get subscription data
    protocol_data, agent_data = price_sheets.getCombinedSubData(
        governor,
        bob_agent,
        boa.env.evm.patch.block_number - 43_200,  # Trial period started
        boa.env.evm.patch.block_number - 43_200,  # Trial period started
        oracle_registry
    )
    
    # Verify no payment is required when price is zero
    assert protocol_data.amount == 0
    assert agent_data.amount == 0
    assert protocol_data.paidThroughBlock == boa.env.evm.patch.block_number - 43_200  # Unchanged
    assert agent_data.paidThroughBlock == boa.env.evm.patch.block_number - 43_200  # Unchanged


def test_transaction_fee_calculation_with_different_user_addresses(price_sheets, governor, bob, sally):
    """Test transaction fee calculation with different user addresses"""
    # Set protocol transaction fees
    price_sheets.setProtocolTxPriceSheet(
        100,    # yieldFee (1.00%)
        200,    # swapFee (2.00%)
        300,    # claimRewardsFee (3.00%)
        sender=governor
    )
    
    # Test fee calculation for different users
    fee_bob, recipient_bob = price_sheets.getTransactionFeeData(bob, WITHDRAWAL_UINT256)
    fee_sally, recipient_sally = price_sheets.getTransactionFeeData(sally, WITHDRAWAL_UINT256)
    
    # Verify fees are the same regardless of user
    assert fee_bob == 100  # 1.00%
    assert fee_sally == 100  # 1.00%
    assert recipient_bob == price_sheets.protocolRecipient()
    assert recipient_sally == price_sheets.protocolRecipient()
    
    # Test with different transaction types
    fee_bob_swap, _ = price_sheets.getTransactionFeeData(bob, SWAP_UINT256)
    fee_sally_swap, _ = price_sheets.getTransactionFeeData(sally, SWAP_UINT256)
    
    assert fee_bob_swap == 200  # 2.00%
    assert fee_sally_swap == 200  # 2.00%


def test_combined_subscription_data_with_multiple_agents(price_sheets, governor, bob_agent, sally, oracle_registry):
    """Test getCombinedSubData with multiple agents"""
    # Set up protocol subscription
    price_sheets.setProtocolSubPrice(
        sally,  # Using sally as a token address for this test
        10 * EIGHTEEN_DECIMALS,  # 10 USD
        43_200,                  # trial period
        302_400,                 # pay period
        sender=governor
    )
    
    # Set up agent subscription
    price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    price_sheets.setAgentSubPrice(
        bob_agent,
        sally,  # Using sally as a token address for this test
        5 * EIGHTEEN_DECIMALS,   # 5 USD
        43_200,                  # trial period
        302_400,                 # pay period
        sender=governor
    )
    
    # Get subscription data for bob_agent
    protocol_data_bob, agent_data_bob = price_sheets.getCombinedSubData(
        governor,
        bob_agent,
        0,  # Not paid yet
        0,  # Not paid yet
        oracle_registry
    )
    
    # Verify trial periods are set up correctly
    assert protocol_data_bob.paidThroughBlock == boa.env.evm.patch.block_number + 43_200
    assert agent_data_bob.paidThroughBlock == boa.env.evm.patch.block_number + 43_200
    
    # Get subscription data for a different agent (that doesn't have pricing set up)
    protocol_data_other, agent_data_other = price_sheets.getCombinedSubData(
        governor,
        sally,  # Using sally as an agent address for this test
        0,  # Not paid yet
        0,  # Not paid yet
        oracle_registry
    )
    
    # Verify protocol trial period is set up, but no agent subscription
    assert protocol_data_other.paidThroughBlock == boa.env.evm.patch.block_number + 43_200
    assert agent_data_other.paidThroughBlock == 0  # No agent subscription for sally
    assert agent_data_other.amount == 0
    assert agent_data_other.asset == ZERO_ADDRESS 