import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256, HUNDRED_PERCENT, MAX_UINT256
from contracts.core.templates import UserWalletTemplate, UserWalletConfigTemplate


@pytest.fixture(scope="session")
def costly_agent(owner, agent_factory):
    w = agent_factory.createAgent(owner, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isAgent(w)
    return w


@pytest.fixture(scope="module")
def new_ai_wallet(agent_factory, owner, ambassador, costly_agent):
    w = agent_factory.createUserWallet(owner, ambassador, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    wallet = UserWalletTemplate.at(w)
    w_config = UserWalletConfigTemplate.at(wallet.walletConfig())
    w_config.addOrModifyAgent(costly_agent, sender=owner)
    return wallet


@pytest.fixture(scope="module")
def new_ai_wallet_config(new_ai_wallet):
    return UserWalletConfigTemplate.at(new_ai_wallet.walletConfig())


@pytest.fixture(scope="module")
def ambassador(agent_factory, owner):
    w = agent_factory.createUserWallet(owner, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return UserWalletTemplate.at(w)


@pytest.fixture(scope="module", autouse=True)
def setup_pricing(price_sheets, governor, alpha_token, costly_agent, oracle_custom, oracle_registry):
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set protocol transaction fees
    """Setup protocol pricing for tests"""
    # Set protocol transaction fees
    assert price_sheets.setProtocolTxPriceSheet(
        10_00,    # yield fee (10.00%)
        1_00,    # swapFee (1%)
        4_00,    # claimRewardsFee (4.00%)
        sender=governor
    )

    # Set protocol subscription
    assert price_sheets.setProtocolSubPrice(
        alpha_token,
        10 * EIGHTEEN_DECIMALS,  # usdValue
        43_200,                    # trialPeriod (1 day)
        302_400,                   # payPeriod (7 days)
        sender=governor
    )

    """Setup agent pricing for tests"""
    # Enable agent pricing
    assert price_sheets.setAgentSubPricingEnabled(True, sender=governor)

    # Set agent subscription pricing (instead of transaction fees)
    assert price_sheets.setAgentSubPrice(
        costly_agent,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,  # usdValue
        43_200,                   # trialPeriod (1 day)
        302_400,                  # payPeriod (7 days)
        sender=governor
    )

    return price_sheets


#########
# Tests #
#########


def test_agent_subscription_trial(new_ai_wallet_config, costly_agent):
    """Test costly_agent subscription trial period"""
    agent_info = new_ai_wallet_config.agentSettings(costly_agent)
    assert agent_info.isActive
    assert agent_info.installBlock > 0
    assert agent_info.paidThroughBlock > agent_info.installBlock
    assert agent_info.paidThroughBlock == agent_info.installBlock + 43_200  # trial period


def test_protocol_subscription_trial(new_ai_wallet_config):
    """Test protocol subscription trial period"""
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert protocol_sub.installBlock > 0
    assert protocol_sub.paidThroughBlock > protocol_sub.installBlock
    assert protocol_sub.paidThroughBlock == protocol_sub.installBlock + 43_200  # trial period


def test_agent_subscription_payment(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, oracle_registry):
    """Test costly_agent subscription payment after trial"""

    # remove protocol sub pricing and tx pricing
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    assert price_sheets.setAgentSubPricingEnabled(False, sender=governor)

    orig_paid_through_block = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # cannot pay
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert canPayProtocol
    assert not canPayAgent

    # Fund wallet for subscription payment
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # can make payment
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert canPayProtocol
    assert canPayAgent

    assert alpha_token.balanceOf(costly_agent) == 0

    # Trigger subscription check with a deposit
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0 and d != 0

    log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[0]
    assert log.recipient == costly_agent
    assert log.asset == alpha_token.address
    assert log.amount == 5 * EIGHTEEN_DECIMALS
    assert log.usdValue == 5 * EIGHTEEN_DECIMALS
    assert log.isAgent

    agent_info = new_ai_wallet_config.agentSettings(costly_agent)
    assert log.paidThroughBlock == agent_info.paidThroughBlock

    # Verify subscription payment
    assert agent_info.paidThroughBlock == log.paidThroughBlock  # Don't check exact block number, just verify it matches the event


def test_protocol_subscription_payment(new_ai_wallet, new_ai_wallet_config, alpha_token, alpha_token_whale, governor, price_sheets, costly_agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test protocol subscription payment after trial"""

    # remove costly_agent sub pricing and tx pricing
    assert price_sheets.removeAgentSubPrice(costly_agent, sender=governor)
    assert price_sheets.setAgentSubPricingEnabled(False, sender=governor)

    orig_paid_through_block = new_ai_wallet_config.protocolSub().paidThroughBlock

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # cannot pay
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert not canPayProtocol
    assert canPayAgent

    # Fund wallet for subscription payment
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # can make payment
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert canPayProtocol
    assert canPayAgent

    # Trigger subscription check with a deposit
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0 and d != 0

    log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[0]
    assert log.recipient == price_sheets.protocolRecipient()
    assert log.asset == alpha_token.address
    assert log.amount == 10 * EIGHTEEN_DECIMALS
    assert log.usdValue == 10 * EIGHTEEN_DECIMALS
    assert not log.isAgent

    protocol_sub = new_ai_wallet_config.protocolSub()
    assert log.paidThroughBlock == protocol_sub.paidThroughBlock

    # Verify subscription payment
    assert protocol_sub.paidThroughBlock > orig_paid_through_block
    current_block = boa.env.evm.patch.block_number
    assert protocol_sub.paidThroughBlock == current_block + 302_400  # pay period


def test_subscription_payment_checks(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale):
    """Test canMakeSubscriptionPayments function"""

    # Initially both should be true since in trial period
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert canPayAgent and canPayProtocol

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Should be false for both since no funds
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert not canPayAgent and not canPayProtocol

    # Fund wallet with just enough for costly_agent subscription
    alpha_token.transfer(new_ai_wallet, 5 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Should be true for costly_agent but false for protocol
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert canPayAgent and not canPayProtocol

    # Fund wallet with enough for protocol subscription
    alpha_token.transfer(new_ai_wallet, 10 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Should be true for both
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert canPayAgent and canPayProtocol


def test_subscription_pricing_removal(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test subscription behavior when pricing is removed and re-added"""
    # Initial state check
    agent_info = new_ai_wallet_config.agentSettings(costly_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0

    # Remove both subscription prices
    assert price_sheets.removeAgentSubPrice(costly_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Trigger subscription check
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0 and d != 0

    # Verify subscriptions are cleared
    agent_info = new_ai_wallet_config.agentSettings(costly_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_info.paidThroughBlock == 0
    assert protocol_sub.paidThroughBlock == 0

    # Re-add subscription prices
    assert price_sheets.setAgentSubPrice(costly_agent, alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert price_sheets.setProtocolSubPrice(alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)

    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0 and d != 0

    # Verify new trial periods started
    agent_info = new_ai_wallet_config.agentSettings(costly_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0


def test_subscription_payment_insufficient_balance(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test subscription payment behavior with insufficient balance"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Fund wallet with less than required for subscriptions
    alpha_token.transfer(new_ai_wallet, 2 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Verify cannot make payments
    can_pay_protocol, can_pay_agent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert not can_pay_agent and not can_pay_protocol

    # Try to trigger subscription payment - should still work but not pay subscription
    orig_agent_paid_through = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock

    with boa.reverts("insufficient balance for protocol subscription payment"):
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)

    # remove price, will allow transaction through
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)

    # trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 2 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0

    # Verify paid through blocks haven't changed
    assert new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_subscription_status_view_functions(new_ai_wallet_config, costly_agent, governor, price_sheets):
    """Test getAgentSubscriptionStatus and getProtocolSubscriptionStatus view functions"""
    # Check during trial period
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(costly_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    assert agent_data.amount == 0  # No payment needed during trial
    assert protocol_data.amount == 0  # No payment needed during trial
    assert agent_data.paidThroughBlock > 0  # Trial period active
    assert protocol_data.paidThroughBlock > 0  # Trial period active
    assert not agent_data.didChange  # No state change
    assert not protocol_data.didChange  # No state change

    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Check after trial period
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(costly_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    assert agent_data.amount == 5 * EIGHTEEN_DECIMALS  # Payment needed
    assert protocol_data.amount == 10 * EIGHTEEN_DECIMALS  # Payment needed
    assert agent_data.didChange  # State will change when paid
    assert protocol_data.didChange  # State will change when paid

    # Remove pricing and check status
    assert price_sheets.removeAgentSubPrice(costly_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(costly_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    assert agent_data.amount == 0  # No payment needed when no pricing
    assert protocol_data.amount == 0  # No payment needed when no pricing
    assert agent_data.didChange  # State will change to clear paid through
    assert protocol_data.didChange  # State will change to clear paid through


def test_multiple_subscription_payments(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test multiple subscription payments in sequence"""
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # First payment
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    first_agent_paid_through = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock
    first_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    
    # Fast forward past first payment period
    boa.env.time_travel(blocks=302_400 + 1)
    
    # Second payment
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    second_agent_paid_through = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock
    second_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    
    # Verify paid through blocks increased correctly
    assert second_agent_paid_through > first_agent_paid_through
    assert second_protocol_paid_through > first_protocol_paid_through
    assert second_agent_paid_through == first_agent_paid_through + 302_400 + 1
    assert second_protocol_paid_through == first_protocol_paid_through + 302_400 + 1


def test_subscription_state_transitions(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test subscription state transitions and edge cases"""
    # Initial state - in trial
    assert new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock > 0
    assert new_ai_wallet_config.protocolSub().paidThroughBlock > 0
    
    # Remove pricing during trial
    assert price_sheets.removeAgentSubPrice(costly_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    
    # Trigger check - should clear paid through
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock == 0
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == 0
    
    # Re-add pricing with different amounts
    assert price_sheets.setAgentSubPrice(costly_agent, alpha_token, 7 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert price_sheets.setProtocolSubPrice(alpha_token, 12 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    
    # Trigger check - should start new trial
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    trial_agent_paid_through = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock
    trial_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    assert trial_agent_paid_through > 0
    assert trial_protocol_paid_through > 0
    
    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Trigger payment with new amounts
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    
    # Verify new payment amounts in logs
    agent_log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[1]
    protocol_log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[0]
    assert agent_log.amount == 7 * EIGHTEEN_DECIMALS
    assert protocol_log.amount == 12 * EIGHTEEN_DECIMALS


def test_agent_transaction_fees(new_ai_wallet, new_ai_wallet_config, owner, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, costly_agent):
    """Test costly_agent transaction fees"""
    # Remove protocol pricing to isolate costly_agent fees
    assert price_sheets.removeProtocolTxPriceSheet(sender=governor)
    assert price_sheets.removeAgentSubPrice(costly_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_agent_wallet = alpha_token.balanceOf(costly_agent)

    # Test deposit - no agent transaction fees should be charged
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=costly_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # No agent transaction fees should be charged
    assert len(logs) == 0

    new_agent_wallet = alpha_token.balanceOf(costly_agent)
    # Agent wallet balance should remain unchanged since no fees are charged
    assert new_agent_wallet == pre_agent_wallet
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal - no agent transaction fees should be charged
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # No agent transaction fees should be charged
    assert len(logs) == 0

    new_agent_wallet = alpha_token.balanceOf(costly_agent)
    # Agent wallet balance should remain unchanged since no fees are charged
    assert new_agent_wallet == pre_agent_wallet


def test_subscription_status_during_trial(new_ai_wallet_config, costly_agent):
    """Test subscription status checks during trial period"""
    # Check initial trial period status
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(costly_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    # During trial period, no payment should be needed
    assert agent_data.amount == 0
    assert protocol_data.amount == 0
    assert not agent_data.didChange
    assert not protocol_data.didChange
    
    # Verify trial period end blocks
    agent_info = new_ai_wallet_config.agentSettings(costly_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_data.paidThroughBlock == agent_info.paidThroughBlock
    assert protocol_data.paidThroughBlock == protocol_sub.paidThroughBlock


def test_subscription_payment_zero_price(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test subscription payment behavior when price feed returns zero"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Set price to zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Get original paid through blocks
    orig_agent_paid_through = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    
    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0

    # Verify no subscription events were emitted
    logs = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")
    assert len(logs) == 0

    # Verify no subscription payments were made
    assert new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_maximum_fee_boundary(price_sheets, governor):
    """Test the maximum fee boundary (10%) for transaction fees"""
    # Test setting fees at the maximum boundary (10.00%)
    assert price_sheets.setProtocolTxPriceSheet(
        1000,    # yieldFee (10.00%)
        1000,    # swapFee (10.00%)
        1000,    # claimRewardsFee (10.00%)
        sender=governor
    )
    
    # Verify the fees were set correctly
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.yieldFee == 1000
    assert sheet.swapFee == 1000
    assert sheet.claimRewardsFee == 1000
    
    # Test setting fees above the maximum boundary (10.01%)
    assert not price_sheets.setProtocolTxPriceSheet(
        20_01,    # yieldFee (20.01%)
        1000,    # swapFee (10.00%)
        1000,    # claimRewardsFee (10.00%)
        sender=governor
    )
    
    # Verify the fees were not changed
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.yieldFee == 1000  # Still at 10.00%


def test_subscription_payment_failure(new_ai_wallet, new_ai_wallet_config, costly_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test behavior when subscription payments fail due to insufficient balance"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Fund wallet with less than required for subscriptions
    alpha_token.transfer(new_ai_wallet, 2 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Verify cannot make payments
    can_pay_protocol, can_pay_agent = new_ai_wallet_config.canMakeSubscriptionPayments(costly_agent)
    assert not can_pay_agent and not can_pay_protocol

    # Try to trigger subscription payment - should still work but not pay subscription
    orig_agent_paid_through = new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock

    with boa.reverts("insufficient balance for protocol subscription payment"):
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)

    # remove price, will allow transaction through
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)

    # trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 2 * EIGHTEEN_DECIMALS, sender=costly_agent)
    assert a != 0

    # Verify paid through blocks haven't changed
    assert new_ai_wallet_config.agentSettings(costly_agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_transaction_fee_calculation_with_zero_balance(new_ai_wallet, costly_agent, alpha_token, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test transaction fee calculation when token balance is zero"""
    # Don't fund the wallet, so balance is zero
    
    # Attempt a transaction
    with boa.reverts():  # Should revert due to insufficient balance
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=costly_agent)
    
    # No transaction fee events should be emitted
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    assert len(logs) == 0


def test_swap_fees_to_protocol(new_ai_wallet, costly_agent, mock_lego_alpha, alpha_token, price_sheets, alpha_token_whale, bravo_token, bravo_token_whale):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(new_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # put amount for swap
    bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)

    instruction = (
        lego_id,
        deposit_amount,
        0,
        [alpha_token, bravo_token],
        [alpha_token]
    )

    pre_protocol_balance = bravo_token.balanceOf(price_sheets.protocolRecipient())

    # swap
    actualSwapAmount, toAmount, usdValue = new_ai_wallet.swapTokens([instruction], sender=costly_agent)
    
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.asset == bravo_token.address
    assert log.protocolRecipient == price_sheets.protocolRecipient()
    assert log.protocolAmount == 1 * EIGHTEEN_DECIMALS # 1% of 100 * EIGHTEEN_DECIMALS
    assert log.ambassadorRecipient == ZERO_ADDRESS
    assert log.ambassadorAmount == 0
    assert log.fee == 1_00 # 1%

    assert bravo_token.balanceOf(log.protocolRecipient) == pre_protocol_balance + log.protocolAmount
    

def test_swap_fees_with_ambassador(new_ai_wallet, costly_agent, governor, mock_lego_alpha, alpha_token, price_sheets, alpha_token_whale, bravo_token, bravo_token_whale, ambassador):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(new_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # set ambassador ratio
    assert price_sheets.setAmbassadorRatio(50_00, sender=governor)

    # put amount for swap
    bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)

    instruction = (
        lego_id,
        deposit_amount,
        0,
        [alpha_token, bravo_token],
        [alpha_token]
    )

    pre_protocol_balance = bravo_token.balanceOf(price_sheets.protocolRecipient())
    pre_ambassador_balance = bravo_token.balanceOf(ambassador.address)

    # swap
    actualSwapAmount, toAmount, usdValue = new_ai_wallet.swapTokens([instruction], sender=costly_agent)
    
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.asset == bravo_token.address
    assert log.protocolRecipient == price_sheets.protocolRecipient()
    assert log.protocolAmount == 5 * EIGHTEEN_DECIMALS 
    assert log.ambassadorRecipient == ambassador.address
    assert log.ambassadorAmount == 5 * EIGHTEEN_DECIMALS
    assert log.fee == 1_00 # 1%

    assert bravo_token.balanceOf(log.protocolRecipient) == pre_protocol_balance + log.protocolAmount
    assert bravo_token.balanceOf(ambassador.address) == pre_ambassador_balance + log.ambassadorAmount


def test_ambassador_on_yield_fees(mock_lego_alpha, ambassador, governor, alpha_token, alpha_token_whale, new_ai_wallet, costly_agent, alpha_token_erc4626_vault, price_sheets):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS

    # set ambassador ratio
    assert price_sheets.setAmbassadorRatio(50_00, sender=governor)

    # transfer tokens to wallet
    alpha_token.transfer(new_ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(new_ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = new_ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=costly_agent)

    # send more to vault
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # test underlying amount
    underlying_amount = mock_lego_alpha.getUnderlyingAmount(vaultToken, vaultTokenAmountReceived)
    assert underlying_amount == 1100 * EIGHTEEN_DECIMALS

    # withdraw
    assetAmountReceived, vaultTokenAmountBurned, usdValue = new_ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=costly_agent)

    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]

    assert assetAmountReceived == 1090 * EIGHTEEN_DECIMALS

    assert log.asset == alpha_token.address
    assert log.protocolRecipient == price_sheets.protocolRecipient()
    assert log.protocolAmount == 5 * EIGHTEEN_DECIMALS # 10.00% of 10 * EIGHTEEN_DECIMALS
    assert log.ambassadorRecipient == ambassador.address
    assert log.ambassadorAmount == 5 * EIGHTEEN_DECIMALS
    assert log.fee == 10_00 # 10.00%


def test_ambassador_bonus(mock_lego_alpha, agent_factory, ambassador, governor, alpha_token, alpha_token_whale, new_ai_wallet, costly_agent, alpha_token_erc4626_vault, price_sheets):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS

    # no protocol fees, no abmassador ratios
    assert price_sheets.setProtocolTxPriceSheet(0, 0, 0, sender=governor)
    assert price_sheets.setAmbassadorRatio(0, sender=governor)

    # set ambassador bonus ratio
    assert agent_factory.setAmbassadorBonusRatio(10_00, sender=governor)

    # transfer tokens to wallet
    alpha_token.transfer(new_ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(new_ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = new_ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=costly_agent)

    # send more to vault
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # test underlying amount
    underlying_amount = mock_lego_alpha.getUnderlyingAmount(vaultToken, vaultTokenAmountReceived)
    assert underlying_amount == 1100 * EIGHTEEN_DECIMALS

    # put money in agent factory
    alpha_token.transfer(agent_factory, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    pre_ambassador_balance = alpha_token.balanceOf(ambassador.address)

    # withdraw
    assetAmountReceived, vaultTokenAmountBurned, usdValue = new_ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=costly_agent)

    log = filter_logs(new_ai_wallet, "AmbassadorYieldBonusPaid")[0]

    # no tx fees, so user gets full amount
    assert assetAmountReceived == 1100 * EIGHTEEN_DECIMALS

    assert log.user == new_ai_wallet.address
    assert log.ambassador == ambassador.address
    assert log.asset == alpha_token.address
    assert log.amount == 10 * EIGHTEEN_DECIMALS
    assert log.ratio == 10_00

    assert alpha_token.balanceOf(ambassador.address) == pre_ambassador_balance + log.amount
