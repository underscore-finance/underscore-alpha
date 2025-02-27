import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256
from contracts.core import WalletFunds, WalletConfig


@pytest.fixture(scope="module")
def new_ai_wallet(agent_factory, owner, bob_agent):
    w = agent_factory.createUserWallet(owner, bob_agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return WalletFunds.at(w)


@pytest.fixture(scope="module")
def new_ai_wallet_config(new_ai_wallet):
    return WalletConfig.at(new_ai_wallet.walletConfig())


@pytest.fixture(scope="module", autouse=True)
def setup_pricing(price_sheets, governor, alpha_token, bob_agent, oracle_custom, oracle_registry):
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set protocol transaction fees
    """Setup protocol pricing for tests"""
    # Set protocol transaction fees
    assert price_sheets.setProtocolTxPriceSheet(
        alpha_token,
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        300,    # addLiqFee (3.00%)
        350,    # removeLiqFee (3.50%)
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

    """Setup bob_agent pricing for tests"""
    # Enable bob_agent pricing
    assert price_sheets.setAgentTxPricingEnabled(True, sender=governor)
    assert price_sheets.setAgentSubPricingEnabled(True, sender=governor)

    # Set bob_agent transaction fees
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,    # depositFee (1.00%)
        200,    # withdrawalFee (2.00%)
        300,    # rebalanceFee (3.00%)
        400,    # transferFee (4.00%)
        500,    # swapFee (5.00%)
        600,    # addLiqFee (6.00%)
        700,    # removeLiqFee (7.00%)
        sender=governor
    )

    # Set bob_agent subscription
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,   # usdValue
        43_200,                    # trialPeriod (1 day)
        302_400,                   # payPeriod (7 days)
        sender=governor
    )


#########
# Tests #
#########


def test_agent_subscription_trial(new_ai_wallet_config, bob_agent):
    """Test bob_agent subscription trial period"""
    agent_info = new_ai_wallet_config.agentSettings(bob_agent)
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


def test_agent_subscription_payment(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, oracle_registry):
    """Test bob_agent subscription payment after trial"""

    # remove protocol sub pricing and tx pricing
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)

    orig_paid_through_block = new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # cannot pay
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert canPayProtocol
    assert not canPayAgent

    # Fund wallet for subscription payment
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # can make payment
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert canPayProtocol
    assert canPayAgent

    assert alpha_token.balanceOf(bob_agent) == 0

    # Trigger subscription check with a deposit
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0 and d != 0
   
    log = filter_logs(new_ai_wallet, "SubscriptionPaid")[0]
    assert log.recipient == bob_agent
    assert log.asset == alpha_token.address
    assert log.amount == 5 * EIGHTEEN_DECIMALS
    assert log.usdValue == 5 * EIGHTEEN_DECIMALS
    assert log.isAgent

    agent_info = new_ai_wallet_config.agentSettings(bob_agent)
    assert log.paidThroughBlock == agent_info.paidThroughBlock

    # Verify subscription payment
    assert agent_info.paidThroughBlock == orig_paid_through_block + 302_400 + 1  # pay period

    assert alpha_token.balanceOf(bob_agent) == log.amount


def test_protocol_subscription_payment(new_ai_wallet, new_ai_wallet_config, alpha_token, alpha_token_whale, governor, price_sheets, bob_agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test protocol subscription payment after trial"""

    # remove bob_agent sub pricing and tx pricing
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)

    orig_paid_through_block = new_ai_wallet_config.protocolSub().paidThroughBlock

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # cannot pay
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert not canPayProtocol
    assert canPayAgent

    # Fund wallet for subscription payment
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # can make payment
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert canPayProtocol
    assert canPayAgent

    # Trigger subscription check with a deposit
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0 and d != 0
   
    log = filter_logs(new_ai_wallet, "SubscriptionPaid")[0]
    assert log.recipient == price_sheets.protocolRecipient()
    assert log.asset == alpha_token.address
    assert log.amount == 10 * EIGHTEEN_DECIMALS
    assert log.usdValue == 10 * EIGHTEEN_DECIMALS
    assert not log.isAgent

    protocol_sub = new_ai_wallet_config.protocolSub()
    assert log.paidThroughBlock == protocol_sub.paidThroughBlock

    # Verify subscription payment
    assert protocol_sub.paidThroughBlock == orig_paid_through_block + 302_400 + 1  # pay period


def test_subscription_payment_checks(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale):
    """Test canMakeSubscriptionPayments function"""

    # Initially both should be true since in trial period
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert canPayAgent and canPayProtocol

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Should be false for both since no funds
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert not canPayAgent and not canPayProtocol

    # Fund wallet with just enough for bob_agent subscription
    alpha_token.transfer(new_ai_wallet, 5 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Should be true for bob_agent but false for protocol
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert canPayAgent and not canPayProtocol

    # Fund wallet with enough for protocol subscription
    alpha_token.transfer(new_ai_wallet, 10 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Should be true for both
    canPayProtocol, canPayAgent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert canPayAgent and canPayProtocol


def test_subscription_pricing_removal(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test subscription behavior when pricing is removed and re-added"""
    # Initial state check
    agent_info = new_ai_wallet_config.agentSettings(bob_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0

    # Remove both subscription prices
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Trigger subscription check
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0 and d != 0

    # Verify subscriptions are cleared
    agent_info = new_ai_wallet_config.agentSettings(bob_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_info.paidThroughBlock == 0
    assert protocol_sub.paidThroughBlock == 0

    # Re-add subscription prices
    assert price_sheets.setAgentSubPrice(bob_agent, alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert price_sheets.setProtocolSubPrice(alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)

    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0 and d != 0

    # Verify new trial periods started
    agent_info = new_ai_wallet_config.agentSettings(bob_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0


def test_subscription_payment_insufficient_balance(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test subscription payment behavior with insufficient balance"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Fund wallet with less than required for subscriptions
    alpha_token.transfer(new_ai_wallet, 2 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Verify cannot make payments
    can_pay_protocol, can_pay_agent = new_ai_wallet_config.canMakeSubscriptionPayments(bob_agent)
    assert not can_pay_agent and not can_pay_protocol

    # Try to trigger subscription payment - should still work but not pay subscription
    orig_agent_paid_through = new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock

    with boa.reverts("insufficient balance for protocol subscription payment"):
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)

    # remove price, will allow transaction through
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)

    # trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 2 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0

    # Verify paid through blocks haven't changed
    assert new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_subscription_status_view_functions(new_ai_wallet_config, bob_agent, governor, price_sheets):
    """Test getAgentSubscriptionStatus and getProtocolSubscriptionStatus view functions"""
    # Check during trial period
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(bob_agent)
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
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(bob_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    assert agent_data.amount == 5 * EIGHTEEN_DECIMALS  # Payment needed
    assert protocol_data.amount == 10 * EIGHTEEN_DECIMALS  # Payment needed
    assert agent_data.didChange  # State will change when paid
    assert protocol_data.didChange  # State will change when paid

    # Remove pricing and check status
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(bob_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    assert agent_data.amount == 0  # No payment needed when no pricing
    assert protocol_data.amount == 0  # No payment needed when no pricing
    assert agent_data.didChange  # State will change to clear paid through
    assert protocol_data.didChange  # State will change to clear paid through


def test_multiple_subscription_payments(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test multiple subscription payments in sequence"""
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # First payment
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    first_agent_paid_through = new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock
    first_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    
    # Fast forward past first payment period
    boa.env.time_travel(blocks=302_400 + 1)
    
    # Second payment
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    second_agent_paid_through = new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock
    second_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    
    # Verify paid through blocks increased correctly
    assert second_agent_paid_through > first_agent_paid_through
    assert second_protocol_paid_through > first_protocol_paid_through
    assert second_agent_paid_through == first_agent_paid_through + 302_400 + 1
    assert second_protocol_paid_through == first_protocol_paid_through + 302_400 + 1


def test_subscription_state_transitions(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test subscription state transitions and edge cases"""
    # Initial state - in trial
    assert new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock > 0
    assert new_ai_wallet_config.protocolSub().paidThroughBlock > 0
    
    # Remove pricing during trial
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    
    # Trigger check - should clear paid through
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock == 0
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == 0
    
    # Re-add pricing with different amounts
    assert price_sheets.setAgentSubPrice(bob_agent, alpha_token, 7 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert price_sheets.setProtocolSubPrice(alpha_token, 12 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    
    # Trigger check - should start new trial
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    trial_agent_paid_through = new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock
    trial_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    assert trial_agent_paid_through > 0
    assert trial_protocol_paid_through > 0
    
    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Trigger payment with new amounts
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    
    # Verify new payment amounts in logs
    agent_log = filter_logs(new_ai_wallet, "SubscriptionPaid")[1]
    protocol_log = filter_logs(new_ai_wallet, "SubscriptionPaid")[0]
    assert agent_log.amount == 7 * EIGHTEEN_DECIMALS
    assert protocol_log.amount == 12 * EIGHTEEN_DECIMALS


def test_protocol_transaction_fees(new_ai_wallet, new_ai_wallet_config, owner, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test protocol transaction fees"""
    # Remove bob_agent pricing to isolate protocol fees
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    assert not new_ai_wallet_config.canPayTransactionFees(bob_agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)[0]

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert new_ai_wallet_config.canPayTransactionFees(bob_agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)[0]

    pre_protocol_wallet = alpha_token.balanceOf(governor)

    # Test deposit fee (0.50%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256  # DEPOSIT
    assert log.recipient == governor
    assert log.asset == alpha_token.address
    assert log.amount == 1 * EIGHTEEN_DECIMALS  # 0.50% of 200
    assert log.usdValue == 1 * EIGHTEEN_DECIMALS

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.amount
    pre_protocol_wallet = new_protocol_wallet

    # Test withdrawal fee (1.00%)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log.asset == alpha_token.address
    assert log.amount == 1 * EIGHTEEN_DECIMALS  # 1.00% of 100
    assert log.usdValue == 1 * EIGHTEEN_DECIMALS
    assert log.recipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.amount
    pre_protocol_wallet = new_protocol_wallet

    # Test rebalance fee (1.50%)
    a, b, c, d = new_ai_wallet.rebalance(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, mock_lego_alpha.legoId(), alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == REBALANCE_UINT256  # REBALANCE
    assert log.asset == alpha_token.address
    assert log.amount == 1.5 * EIGHTEEN_DECIMALS  # 1.50% of 100
    assert log.usdValue == 1.5 * EIGHTEEN_DECIMALS
    assert log.recipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.amount
    pre_protocol_wallet = new_protocol_wallet

    # Test transfer fee (2.00%)
    a, b = new_ai_wallet.transferFunds(owner, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == TRANSFER_UINT256  # TRANSFER
    assert log.asset == alpha_token.address
    assert log.amount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log.usdValue == 2 * EIGHTEEN_DECIMALS
    assert log.recipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.amount
    pre_protocol_wallet = new_protocol_wallet
    
    # Test swap fee (2.50%)
    bravo_token.transfer(mock_lego_alpha.address, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    a, b, c = new_ai_wallet.swapTokens(mock_lego_alpha.legoId(), alpha_token, bravo_token, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == SWAP_UINT256  # SWAP
    assert log.asset == alpha_token.address
    assert log.amount == 2.5 * EIGHTEEN_DECIMALS  # 2.50% of 100
    assert log.usdValue == 2.5 * EIGHTEEN_DECIMALS
    assert log.recipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.amount


def test_agent_transaction_fees(new_ai_wallet, new_ai_wallet_config, owner, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test bob_agent transaction fees"""
    # Remove protocol pricing to isolate bob_agent fees
    assert price_sheets.removeProtocolTxPriceSheet(sender=governor)
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    assert not new_ai_wallet_config.canPayTransactionFees(bob_agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)[1]

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert new_ai_wallet_config.canPayTransactionFees(bob_agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)[1]

    pre_agent_wallet = alpha_token.balanceOf(bob_agent)

    # Test deposit fee (1.00%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256  # DEPOSIT
    assert log.isAgent
    assert log.asset == alpha_token.address
    assert log.amount == 2 * EIGHTEEN_DECIMALS  # 1.00% of 200
    assert log.usdValue == 2 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log.amount
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal fee (2.00%)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log.isAgent
    assert log.asset == alpha_token.address
    assert log.amount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log.usdValue == 2 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log.amount
    pre_agent_wallet = new_agent_wallet

    # Test rebalance fee (3.00%)
    a, b, c, d = new_ai_wallet.rebalance(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, mock_lego_alpha.legoId(), alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == REBALANCE_UINT256  # REBALANCE
    assert log.isAgent
    assert log.asset == alpha_token.address
    assert log.amount == 3 * EIGHTEEN_DECIMALS  # 3.00% of 100
    assert log.usdValue == 3 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log.amount
    pre_agent_wallet = new_agent_wallet

    # Test transfer fee (4.00%)
    a, b = new_ai_wallet.transferFunds(owner, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == TRANSFER_UINT256  # TRANSFER
    assert log.isAgent
    assert log.asset == alpha_token.address
    assert log.amount == 4 * EIGHTEEN_DECIMALS  # 4.00% of 100
    assert log.usdValue == 4 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log.amount
    pre_agent_wallet = new_agent_wallet

    # Test swap fee (5.00%)
    bravo_token.transfer(mock_lego_alpha.address, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    a, b, c = new_ai_wallet.swapTokens(mock_lego_alpha.legoId(), alpha_token, bravo_token, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == SWAP_UINT256  # SWAP
    assert log.isAgent
    assert log.asset == alpha_token.address
    assert log.amount == 5 * EIGHTEEN_DECIMALS  # 5.00% of 100
    assert log.usdValue == 5 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log.amount


def test_combined_transaction_fees(new_ai_wallet, new_ai_wallet_config, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test combined protocol and bob_agent transaction fees"""
    # Enable both protocol and bob_agent fees
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    can_pay_protocol, can_pay_agent = new_ai_wallet_config.canPayTransactionFees(bob_agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)
    assert not can_pay_protocol
    assert not can_pay_agent

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    can_pay_protocol, can_pay_agent = new_ai_wallet_config.canPayTransactionFees(bob_agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)
    assert can_pay_protocol
    assert can_pay_agent

    pre_protocol_wallet = alpha_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(bob_agent)

    # Test deposit fees (protocol: 0.50% + bob_agent: 1.00%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log0 = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    log1 = filter_logs(new_ai_wallet, "TransactionFeePaid")[1]

    assert log0.action == DEPOSIT_UINT256  # DEPOSIT
    assert log0.asset == alpha_token.address
    assert log0.amount == 1 * EIGHTEEN_DECIMALS  # 0.50% of 200
    assert log0.usdValue == 1 * EIGHTEEN_DECIMALS
    assert log0.recipient == governor
    assert not log0.isAgent

    assert log1.action == DEPOSIT_UINT256  # DEPOSIT
    assert log1.asset == alpha_token.address
    assert log1.amount == 2 * EIGHTEEN_DECIMALS  # 1.00% of 200
    assert log1.usdValue == 2 * EIGHTEEN_DECIMALS
    assert log1.recipient == bob_agent
    assert log1.isAgent

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log0.amount
    pre_protocol_wallet = new_protocol_wallet

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log1.amount
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal fees (protocol: 1.00% + bob_agent: 2.00%)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log0 = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    log1 = filter_logs(new_ai_wallet, "TransactionFeePaid")[1]

    assert log0.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log0.asset == alpha_token.address
    assert log0.amount == 1 * EIGHTEEN_DECIMALS  # 1.00% of 100
    assert log0.usdValue == 1 * EIGHTEEN_DECIMALS
    assert log0.recipient == governor
    assert not log0.isAgent

    assert log1.asset == alpha_token.address
    assert log1.amount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log1.usdValue == 2 * EIGHTEEN_DECIMALS
    assert log1.recipient == bob_agent
    assert log1.isAgent

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log0.amount

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    assert new_agent_wallet == pre_agent_wallet + log1.amount


def test_wallet_transaction_fee_edge_cases(new_ai_wallet, alpha_token, owner, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent, oracle_custom):
    """Test edge cases for transaction fees"""
    # Enable both protocol and bob_agent fees
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # not enough to pay bob_agent tx fee
    with boa.reverts("insufficient balance for protocol tx fee"):
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 1000 * EIGHTEEN_DECIMALS, sender=bob_agent)

    # Test with price feed returning zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert len(logs) == 0  # No fees when price feed returns zero

    # Test owner bypass of bob_agent fees
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=owner)
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert len(logs) == 0  # No bob_agent fees for owner


def test_subscription_status_during_trial(new_ai_wallet_config, bob_agent):
    """Test subscription status checks during trial period"""
    # Check initial trial period status
    agent_data = new_ai_wallet_config.getAgentSubscriptionStatus(bob_agent)
    protocol_data = new_ai_wallet_config.getProtocolSubscriptionStatus()
    
    # During trial period, no payment should be needed
    assert agent_data.amount == 0
    assert protocol_data.amount == 0
    assert not agent_data.didChange
    assert not protocol_data.didChange
    
    # Verify trial period end blocks
    agent_info = new_ai_wallet_config.agentSettings(bob_agent)
    protocol_sub = new_ai_wallet_config.protocolSub()
    assert agent_data.paidThroughBlock == agent_info.paidThroughBlock
    assert protocol_data.paidThroughBlock == protocol_sub.paidThroughBlock


def test_subscription_payment_zero_price(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test subscription payment behavior when price feed returns zero"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Set price to zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Get original paid through blocks
    orig_agent_paid_through = new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet_config.protocolSub().paidThroughBlock
    
    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0

    # Verify no subscription events were emitted
    logs = filter_logs(new_ai_wallet, "SubscriptionPaid")
    assert len(logs) == 0

    # Verify no subscription payments were made
    assert new_ai_wallet_config.agentSettings(bob_agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet_config.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_transaction_fees_zero_usd_value(new_ai_wallet, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test transaction fee behavior with zero USD value"""
    # Set price to zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Perform transaction
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    assert a != 0
    
    # Verify no transaction fees were charged
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert len(logs) == 0


def test_transaction_fees_different_assets(new_ai_wallet, bob_agent, oracle_custom, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test transaction fees with different assets for protocol vs bob_agent"""
    
    oracle_custom.setPrice(bravo_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)

    # Set different fee assets for protocol and bob_agent
    assert price_sheets.setProtocolTxPriceSheet(
        bravo_token,
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        300,    # addLiqFee (3.00%)
        350,    # removeLiqFee (3.50%)
        sender=governor
    )
    
    assert price_sheets.setAgentTxPriceSheet(
        bob_agent,
        alpha_token,
        100,    # depositFee (1.00%)
        200,    # withdrawalFee (2.00%)
        300,    # rebalanceFee (3.00%)
        400,    # transferFee (4.00%)
        500,    # swapFee (5.00%)
        600,    # addLiqFee (6.00%)
        700,    # removeLiqFee (7.00%)
        sender=governor
    )
    
    # Fund wallet with both tokens
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    bravo_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    
    pre_protocol_wallet = bravo_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(bob_agent)
    
    # Perform transaction
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    
    # Verify fees in different assets
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert logs[0].asset == bravo_token.address
    assert logs[0].amount == 1 * EIGHTEEN_DECIMALS  # 0.50% of 200
    assert logs[1].asset == alpha_token.address
    assert logs[1].amount == 2 * EIGHTEEN_DECIMALS  # 1.00% of 200
    
    # Verify balances
    assert bravo_token.balanceOf(governor) == pre_protocol_wallet + logs[0].amount
    assert alpha_token.balanceOf(bob_agent) == pre_agent_wallet + logs[1].amount


def test_batch_transaction_fees(new_ai_wallet, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test transaction fees in batch operations"""
    # Enable both protocol and bob_agent fees
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_protocol_wallet = alpha_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(bob_agent)

    # Create batch instructions
    instructions = [
        # Deposit instruction
        (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
        # Withdrawal instruction
        (WITHDRAWAL_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS)
    ]

    # Execute batch
    assert new_ai_wallet.performManyActions(instructions, sender=bob_agent)

    # Verify batch fees
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")

    # Protocol fees: (0.50% of 100) + (1.00% of 50) = 1 alpha
    assert logs[0].asset == alpha_token.address
    assert logs[0].amount == 1 * EIGHTEEN_DECIMALS
    assert logs[0].usdValue == 1 * EIGHTEEN_DECIMALS
    assert not logs[0].isAgent

    # Agent fees: (1.00% of 100) + (2.00% of 50) = 2 alpha
    assert logs[1].asset == alpha_token.address
    assert logs[1].amount == 2 * EIGHTEEN_DECIMALS
    assert logs[1].usdValue == 2 * EIGHTEEN_DECIMALS
    assert logs[1].isAgent

    assert alpha_token.balanceOf(governor) == pre_protocol_wallet + logs[0].amount
    assert alpha_token.balanceOf(bob_agent) == pre_agent_wallet + logs[1].amount
