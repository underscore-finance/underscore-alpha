import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256
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
    with boa.reverts("invalid agent"):
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


def test_transaction_price_validation(price_sheets, alpha_token):
    """Test transaction price validation"""
    # Valid case
    assert price_sheets.isValidTxPriceSheet(
        alpha_token,  # asset
        1000,   # depositFee
        1000,   # withdrawalFee
        1000,   # rebalanceFee
        1000,   # transferFee
        1000    # swapFee
    )
    
    # Invalid cases
    assert not price_sheets.isValidTxPriceSheet(
        ZERO_ADDRESS,  # invalid asset
        1000,
        1000,
        1000,
        1000,
        1000
    )
    
    assert not price_sheets.isValidTxPriceSheet(
        alpha_token,
        1001,   # fee too high (>10.00%)
        1000,
        1000,
        1000,
        1000
    )


def test_agent_transaction_price(price_sheets, governor, bob_agent, oracle_custom, alpha_token, oracle_registry):
    """Test agent transaction price management"""

    price_sheets.setAgentTxPricingEnabled(True, sender=governor)

    # set price on alpha_token
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set valid price sheet
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,  # agent
        alpha_token,    # asset
        100,    # depositFee (1.00%)
        200,    # withdrawalFee (2.00%)
        300,    # rebalanceFee (3.00%)
        400,    # transferFee (4.00%)
        500,    # swapFee (5.00%)
        sender=governor
    )
    log = filter_logs(price_sheets, "AgentTxPriceSheetSet")[0]
    assert log.agent == bob_agent
    assert log.asset == alpha_token.address
    assert log.depositFee == 100
    assert log.withdrawalFee == 200
    assert log.rebalanceFee == 300
    assert log.transferFee == 400
    assert log.swapFee == 500
    
    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.asset == alpha_token.address
    assert sheet.depositFee == 100
    assert sheet.withdrawalFee == 200
    assert sheet.rebalanceFee == 300
    assert sheet.transferFee == 400
    assert sheet.swapFee == 500
    
    # Test fee calculations
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)  # DEPOSIT
    assert cost[0] == alpha_token.address  # asset
    assert cost[1] == 10 * EIGHTEEN_DECIMALS # assetAmount (0.1 alpha tokens)
    assert cost[2] == 10000000000000000000 # usdValue (10)
    
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, WITHDRAWAL_UINT256, 1000 * EIGHTEEN_DECIMALS)  # WITHDRAWAL
    assert cost[1] == 20 * EIGHTEEN_DECIMALS # assetAmount (0.2 alpha tokens)
    assert cost[2] == 20 * EIGHTEEN_DECIMALS # usdValue (20)
    
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, REBALANCE_UINT256, 1000 * EIGHTEEN_DECIMALS)  # REBALANCE
    assert cost[1] == 30 * EIGHTEEN_DECIMALS # assetAmount (0.3 alpha tokens)
    assert cost[2] == 30 * EIGHTEEN_DECIMALS # usdValue (30)
    
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, TRANSFER_UINT256, 1000 * EIGHTEEN_DECIMALS)  # TRANSFER
    assert cost[1] == 40 * EIGHTEEN_DECIMALS # assetAmount (0.4 alpha tokens)
    assert cost[2] == 40 * EIGHTEEN_DECIMALS # usdValue (40)
    
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, SWAP_UINT256, 1000 * EIGHTEEN_DECIMALS)  # SWAP
    assert cost[1] == 50 * EIGHTEEN_DECIMALS # assetAmount (0.5 alpha tokens)
    assert cost[2] == 50 * EIGHTEEN_DECIMALS # usdValue (50)
    
    # Remove price sheet
    assert price_sheets.removeAgentTxPriceSheet(bob_agent, sender=governor)
    log = filter_logs(price_sheets, "AgentTxPriceSheetRemoved")[0]
    assert log.agent == bob_agent
    assert log.asset == alpha_token.address
    assert log.depositFee == 100
    assert log.withdrawalFee == 200
    assert log.rebalanceFee == 300
    assert log.transferFee == 400
    assert log.swapFee == 500

    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.asset == ZERO_ADDRESS
    assert sheet.depositFee == 0


def test_protocol_transaction_price(price_sheets, governor, oracle_custom, alpha_token, oracle_registry):
    """Test protocol transaction price management"""

    # set price on alpha_token
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set valid price sheet
    assert price_sheets.setProtocolTxPriceSheet(
        alpha_token,    # asset
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        sender=governor
    )
    log = filter_logs(price_sheets, "ProtocolTxPriceSheetSet")[0]
    assert log.asset == alpha_token.address
    assert log.depositFee == 50
    assert log.withdrawalFee == 100
    assert log.rebalanceFee == 150
    assert log.transferFee == 200
    assert log.swapFee == 250
    
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.asset == alpha_token.address
    assert sheet.depositFee == 50
    assert sheet.withdrawalFee == 100
    assert sheet.rebalanceFee == 150
    assert sheet.transferFee == 200
    assert sheet.swapFee == 250
    
    # Test fee calculations
    cost = price_sheets.getProtocolTransactionFeeData(DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)  # DEPOSIT
    assert cost[0] == alpha_token.address  # asset
    assert cost[1] == 5 * EIGHTEEN_DECIMALS  # assetAmount (0.05 alpha tokens)
    assert cost[2] == 5 * EIGHTEEN_DECIMALS  # usdValue (5)
    
    cost = price_sheets.getProtocolTransactionFeeData(WITHDRAWAL_UINT256, 1000 * EIGHTEEN_DECIMALS)  # WITHDRAWAL
    assert cost[1] == 10 * EIGHTEEN_DECIMALS  # assetAmount (0.1 alpha tokens)
    assert cost[2] == 10 * EIGHTEEN_DECIMALS  # usdValue (10)
    
    cost = price_sheets.getProtocolTransactionFeeData(REBALANCE_UINT256, 1000 * EIGHTEEN_DECIMALS)  # REBALANCE
    assert cost[1] == 15 * EIGHTEEN_DECIMALS  # assetAmount (0.15 alpha tokens)
    assert cost[2] == 15 * EIGHTEEN_DECIMALS  # usdValue (15)
    
    cost = price_sheets.getProtocolTransactionFeeData(TRANSFER_UINT256, 1000 * EIGHTEEN_DECIMALS)  # TRANSFER
    assert cost[1] == 20 * EIGHTEEN_DECIMALS  # assetAmount (0.2 alpha tokens)
    assert cost[2] == 20 * EIGHTEEN_DECIMALS  # usdValue (20)
    
    cost = price_sheets.getProtocolTransactionFeeData(SWAP_UINT256, 1000 * EIGHTEEN_DECIMALS)  # SWAP
    assert cost[1] == 25 * EIGHTEEN_DECIMALS  # assetAmount (0.25 alpha tokens)
    assert cost[2] == 25 * EIGHTEEN_DECIMALS  # usdValue (25)
    
    # Remove price sheet
    assert price_sheets.removeProtocolTxPriceSheet(sender=governor)
    log = filter_logs(price_sheets, "ProtocolTxPriceSheetRemoved")[0]
    assert log.asset == alpha_token.address
    assert log.depositFee == 50
    assert log.withdrawalFee == 100
    assert log.rebalanceFee == 150
    assert log.transferFee == 200
    assert log.swapFee == 250

    sheet = price_sheets.protocolTxPriceData()
    assert sheet.asset == ZERO_ADDRESS
    assert sheet.depositFee == 0


def test_combined_transaction_costs(price_sheets, governor, bob_agent, oracle_custom, alpha_token, oracle_registry):
    """Test combined transaction costs (protocol + agent fees)"""

    price_sheets.setAgentTxPricingEnabled(True, sender=governor)

    # Setup prices
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set protocol price sheet
    assert price_sheets.setProtocolTxPriceSheet(
        alpha_token,
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        sender=governor
    )

    # Set agent price sheet
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,    # depositFee (1.00%)
        200,    # withdrawalFee (2.00%)
        300,    # rebalanceFee (3.00%)
        400,    # transferFee (4.00%)
        500,    # swapFee (5.00%)
        sender=governor
    )

    # Test combined fees
    cost = price_sheets.getTransactionCost(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)
    assert cost.protocolRecipient == price_sheets.protocolRecipient()
    assert cost.protocolAsset == alpha_token.address
    assert cost.protocolAssetAmount == 5 * EIGHTEEN_DECIMALS  # 0.50% of 1000
    assert cost.protocolUsdValue == 5 * EIGHTEEN_DECIMALS
    assert cost.agentAsset == alpha_token.address
    assert cost.agentAssetAmount == 10 * EIGHTEEN_DECIMALS  # 1.00% of 1000
    assert cost.agentUsdValue == 10 * EIGHTEEN_DECIMALS

    # Test with zero protocol fee
    price_sheets.removeProtocolTxPriceSheet(sender=governor)
    cost = price_sheets.getTransactionCost(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)
    assert cost.protocolRecipient == ZERO_ADDRESS
    assert cost.protocolAsset == ZERO_ADDRESS
    assert cost.protocolAssetAmount == 0
    assert cost.protocolUsdValue == 0
    assert cost.agentAsset == alpha_token.address
    assert cost.agentAssetAmount == 10 * EIGHTEEN_DECIMALS
    assert cost.agentUsdValue == 10 * EIGHTEEN_DECIMALS

    # Test with zero agent fee
    price_sheets.removeAgentTxPriceSheet(bob_agent, sender=governor)
    cost = price_sheets.getTransactionCost(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)
    assert cost.protocolRecipient == ZERO_ADDRESS
    assert cost.protocolAsset == ZERO_ADDRESS
    assert cost.protocolAssetAmount == 0
    assert cost.protocolUsdValue == 0
    assert cost.agentAsset == ZERO_ADDRESS
    assert cost.agentAssetAmount == 0
    assert cost.agentUsdValue == 0


def test_deactivated_state(price_sheets, governor, bob_agent, alpha_token, sally):
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
            sender=bob_agent
        )
    
    with boa.reverts("not active"):
        price_sheets.setAgentTxPriceSheet(
            bob_agent,
            alpha_token,
            100,
            200,
            300,
            400,
            500,
            sender=bob_agent
        )

def test_edge_cases(price_sheets, governor, bob_agent, alpha_token, oracle_custom, oracle_registry, sally):
    """Test edge cases and boundary conditions"""
    
    # Setup price
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Test maximum fees
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        1000,   # 10.00% (maximum allowed)
        1000,
        1000,
        1000,
        1000,
        sender=governor
    )

    # Test with zero USD value
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 0)
    assert cost[1] == 0  # assetAmount
    assert cost[2] == 0  # usdValue

    # Test removing non-existent price sheets
    assert not price_sheets.removeAgentTxPriceSheet(sally, sender=governor)  # non-existent agent
    assert not price_sheets.removeProtocolTxPriceSheet(sender=governor)  # already removed

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


def test_transaction_fee_edge_cases(price_sheets, governor, bob_agent, alpha_token, oracle_custom, oracle_registry):
    """Test edge cases in transaction fee calculations"""
    
    price_sheets.setAgentTxPricingEnabled(True, sender=governor)

    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set price sheet with minimum possible fees
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        1,      # 0.01% (minimum non-zero fee)
        1,
        1,
        1,
        1,
        sender=governor
    )
      
    # Test with oracle returning zero price
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    cost = price_sheets.getAgentTransactionFeeData(
        bob_agent,
        DEPOSIT_UINT256,
        1000 * EIGHTEEN_DECIMALS
    )
    # Verify handles zero price gracefully
    assert cost[0] == alpha_token.address
    assert cost[1] == 0  # Asset amount should be zero
    assert cost[2] == 100000000000000000  # USD value should still be calculated


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


def test_price_sheet_state_transitions(price_sheets, governor, bob_agent, alpha_token):
    """Test state transitions when updating price sheets"""
    
    # Set initial price sheet
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,
        200,
        300,
        400,
        500,
        sender=governor
    )
    
    # Verify initial state
    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.depositFee == 100
    assert sheet.withdrawalFee == 200
    assert sheet.rebalanceFee == 300
    assert sheet.transferFee == 400
    assert sheet.swapFee == 500
    
    # Update to new values
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        150,
        250,
        350,
        450,
        550,
        sender=governor
    )
    
    # Verify complete update
    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.depositFee == 150
    assert sheet.withdrawalFee == 250
    assert sheet.rebalanceFee == 350
    assert sheet.transferFee == 450
    assert sheet.swapFee == 550
    
    # Remove price sheet
    assert price_sheets.removeAgentTxPriceSheet(bob_agent, sender=governor)
    
    # Verify complete removal
    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.asset == ZERO_ADDRESS
    assert sheet.depositFee == 0
    assert sheet.withdrawalFee == 0
    assert sheet.rebalanceFee == 0
    assert sheet.transferFee == 0
    assert sheet.swapFee == 0


def test_agent_tx_pricing_enable_disable(price_sheets, governor, bob_agent, oracle_custom, alpha_token, sally):
    """Test enabling and disabling agent transaction pricing"""

    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)

    # Only governor can enable/disable
    with boa.reverts("no perms"):
        price_sheets.setAgentTxPricingEnabled(True, sender=sally)
    
    # No change if already in desired state
    with boa.reverts("no change"):
        price_sheets.setAgentTxPricingEnabled(False, sender=governor)
    
    # Enable agent tx pricing
    assert price_sheets.setAgentTxPricingEnabled(True, sender=governor)
    log = filter_logs(price_sheets, "AgentTxPricingEnabled")[0]
    assert log.isEnabled == True
    assert price_sheets.isAgentTxPricingEnabled()
    
    # Set agent price sheet
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,    # depositFee
        200,    # withdrawalFee
        300,    # rebalanceFee
        400,    # transferFee
        500,    # swapFee
        sender=governor
    )
    
    # Verify fees are returned when enabled
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 1000)
    assert cost[0] == alpha_token.address
    assert cost[1] > 0  # Should have non-zero fee
    
    # Disable agent tx pricing
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)
    log = filter_logs(price_sheets, "AgentTxPricingEnabled")[0]
    assert log.isEnabled == False
    assert not price_sheets.isAgentTxPricingEnabled()
    
    # Verify no fees are returned when disabled
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 1000)
    assert cost[0] == ZERO_ADDRESS
    assert cost[1] == 0  # Should have zero fee


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


def test_agent_pricing_combined_states(price_sheets, governor, bob_agent, alpha_token, oracle_custom, oracle_registry):
    """Test interaction between transaction and subscription pricing states"""
    
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS
    
    # Enable both pricing types
    price_sheets.setAgentTxPricingEnabled(True, sender=governor)
    price_sheets.setAgentSubPricingEnabled(True, sender=governor)
    
    # Set both price types
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,    # depositFee
        200,    # withdrawalFee
        300,    # rebalanceFee
        400,    # transferFee
        500,    # swapFee
        sender=governor
    )
    
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000,   # usdValue
        43_200, # trialPeriod
        302_400,# payPeriod
        sender=governor
    )
    
    # Verify both types of pricing are active
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)
    assert cost[0] == alpha_token.address
    assert cost[1] > 0
    
    info = price_sheets.getAgentSubPriceData(bob_agent)
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    
    # Disable transaction pricing only
    price_sheets.setAgentTxPricingEnabled(False, sender=governor)
    
    # Verify only subscription pricing remains active
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)
    assert cost[0] == ZERO_ADDRESS
    assert cost[1] == 0
    
    info = price_sheets.getAgentSubPriceData(bob_agent)
    assert info.asset == alpha_token.address
    assert info.usdValue == 1000
    
    # Disable subscription pricing only
    price_sheets.setAgentTxPricingEnabled(True, sender=governor)
    price_sheets.setAgentSubPricingEnabled(False, sender=governor)
    
    # Verify only transaction pricing remains active
    cost = price_sheets.getAgentTransactionFeeData(bob_agent, DEPOSIT_UINT256, 1000 * EIGHTEEN_DECIMALS)
    assert cost[0] == alpha_token.address
    assert cost[1] > 0
    
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


def test_pending_agent_tx_price_sheet(price_sheets, governor, bob_agent, alpha_token):
    """Test setting and finalizing pending agent transaction price sheets"""
    
    delay = 43_200

    # Set initial delay
    price_sheets.setPriceChangeDelay(delay, sender=governor)
    assert price_sheets.priceChangeDelay() == delay
    
    # Set pending price sheet
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,    # depositFee
        200,    # withdrawalFee
        300,    # rebalanceFee
        400,    # transferFee
        500,    # swapFee
        sender=governor
    )
    
    # Verify pending price sheet is set
    pending = price_sheets.pendingAgentTxPrices(bob_agent)
    assert pending.priceSheet.asset == alpha_token.address
    assert pending.priceSheet.depositFee == 100
    assert pending.priceSheet.withdrawalFee == 200
    assert pending.priceSheet.rebalanceFee == 300
    assert pending.priceSheet.transferFee == 400
    assert pending.priceSheet.swapFee == 500
    assert pending.effectiveBlock == boa.env.evm.patch.block_number + delay
    
    # Cannot finalize before delay
    with boa.reverts("time delay not reached"):
        price_sheets.finalizePendingTxPriceSheet(bob_agent)
    
    # Advance blocks
    boa.env.time_travel(blocks=delay)
    
    # Now can finalize
    assert price_sheets.finalizePendingTxPriceSheet(bob_agent)
    
    # Verify price sheet is set and pending is cleared
    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.asset == alpha_token.address
    assert sheet.depositFee == 100
    assert sheet.withdrawalFee == 200
    assert sheet.rebalanceFee == 300
    assert sheet.transferFee == 400
    assert sheet.swapFee == 500
    
    pending = price_sheets.pendingAgentTxPrices(bob_agent)
    assert pending.effectiveBlock == 0


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
        price_sheets.finalizePendingTxPriceSheet(bob_agent)
    with boa.reverts("time delay not reached"):
        price_sheets.finalizePendingAgentSubPrice(bob_agent)
    
    # Set pending changes
    price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100, 200, 300, 400, 500,
        sender=governor
    )
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        1000, 43_200, 302_400,
        sender=governor
    )
    
    # Advance blocks
    boa.env.time_travel(blocks=delay)
    
    # anyone can finalize
    assert price_sheets.finalizePendingTxPriceSheet(bob_agent, sender=sally)
    assert price_sheets.finalizePendingAgentSubPrice(bob_agent, sender=sally)
    
    # Setting new pending changes overwrites old ones
    price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        150, 250, 350, 450, 550,
        sender=governor
    )
    price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        2000, 43_200, 302_400,
        sender=governor
    )
    
    pending_tx = price_sheets.pendingAgentTxPrices(bob_agent)
    assert pending_tx.priceSheet.depositFee == 150
    pending_sub = price_sheets.pendingAgentSubPrices(bob_agent)
    assert pending_sub.subInfo.usdValue == 2000


def test_zero_delay_price_changes(price_sheets, governor, bob_agent, alpha_token):
    """Test price changes when delay is set to zero"""
    
    # Set zero delay
    price_sheets.setPriceChangeDelay(0, sender=governor)
    assert price_sheets.priceChangeDelay() == 0
    
    # Price changes should take effect immediately
    price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100, 200, 300, 400, 500,
        sender=governor
    )
    
    # Verify changes are immediate
    sheet = price_sheets.agentTxPriceData(bob_agent)
    assert sheet.depositFee == 100
    
    # No pending changes should be set
    pending = price_sheets.pendingAgentTxPrices(bob_agent)
    assert pending.effectiveBlock == 0
    
    # Same for subscription prices
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
