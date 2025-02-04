import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256
from contracts.core import WalletTemplate


@pytest.fixture(scope="module")
def new_ai_wallet(agent_factory, owner, agent):
    w = agent_factory.createAgenticWallet(owner, agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isAgenticWallet(w)
    return WalletTemplate.at(w)


@pytest.fixture(scope="module", autouse=True)
def setup_pricing(price_sheets, governor, alpha_token, agent, oracle_custom, oracle_registry):
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
    assert price_sheets.setAgentTxPricingEnabled(True, sender=governor)
    assert price_sheets.setAgentSubPricingEnabled(True, sender=governor)

    # Set agent transaction fees
    assert price_sheets.setAgentTxPriceSheet(
        agent,
        alpha_token,
        100,    # depositFee (1.00%)
        200,    # withdrawalFee (2.00%)
        300,    # rebalanceFee (3.00%)
        400,    # transferFee (4.00%)
        500,    # swapFee (5.00%)
        sender=governor
    )

    # Set agent subscription
    assert price_sheets.setAgentSubPrice(
        agent,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,   # usdValue
        43_200,                    # trialPeriod (1 day)
        302_400,                   # payPeriod (7 days)
        sender=governor
    )


#########
# Tests #
#########


def test_agent_subscription_trial(new_ai_wallet, agent):
    """Test agent subscription trial period"""
    agent_info = new_ai_wallet.agentSettings(agent)
    assert agent_info.isActive
    assert agent_info.installBlock > 0
    assert agent_info.paidThroughBlock > agent_info.installBlock
    assert agent_info.paidThroughBlock == agent_info.installBlock + 43_200  # trial period


def test_protocol_subscription_trial(new_ai_wallet):
    """Test protocol subscription trial period"""
    protocol_sub = new_ai_wallet.protocolSub()
    assert protocol_sub.installBlock > 0
    assert protocol_sub.paidThroughBlock > protocol_sub.installBlock
    assert protocol_sub.paidThroughBlock == protocol_sub.installBlock + 43_200  # trial period


def test_agent_subscription_payment(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test agent subscription payment after trial"""

    # remove protocol sub pricing and tx pricing
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)

    orig_paid_through_block = new_ai_wallet.agentSettings(agent).paidThroughBlock

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # cannot pay
    assert not new_ai_wallet.canMakeSubscriptionPayments(agent)[0]

    # Fund wallet for subscription payment
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # can make payment
    assert new_ai_wallet.canMakeSubscriptionPayments(agent)[0]

    assert alpha_token.balanceOf(agent) == 0

    # Trigger subscription check with a deposit
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0 and d != 0
   
    log = filter_logs(new_ai_wallet, "AgentSubscriptionPaid")[0]
    assert log.agent == agent
    assert log.asset == alpha_token.address
    assert log.amount == 5 * EIGHTEEN_DECIMALS
    assert log.usdValue == 5 * EIGHTEEN_DECIMALS

    agent_info = new_ai_wallet.agentSettings(agent)
    assert log.paidThroughBlock == agent_info.paidThroughBlock

    # Verify subscription payment
    assert agent_info.paidThroughBlock == orig_paid_through_block + 302_400 + 1  # pay period

    assert alpha_token.balanceOf(agent) == log.amount


def test_protocol_subscription_payment(new_ai_wallet, alpha_token, alpha_token_whale, governor, price_sheets, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test protocol subscription payment after trial"""
    # remove agent sub pricing and tx pricing
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)

    orig_paid_through_block = new_ai_wallet.protocolSub().paidThroughBlock

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # cannot pay
    assert not new_ai_wallet.canMakeSubscriptionPayments(agent)[1]

    # Fund wallet for subscription payment
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # can make payment
    assert new_ai_wallet.canMakeSubscriptionPayments(agent)[1]

    # Trigger subscription check with a deposit
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0 and d != 0
   
    log = filter_logs(new_ai_wallet, "ProtocolSubscriptionPaid")[0]
    assert log.recipient == price_sheets.protocolRecipient()
    assert log.asset == alpha_token.address
    assert log.amount == 10 * EIGHTEEN_DECIMALS
    assert log.usdValue == 10 * EIGHTEEN_DECIMALS

    protocol_sub = new_ai_wallet.protocolSub()
    assert log.paidThroughBlock == protocol_sub.paidThroughBlock

    # Verify subscription payment
    assert protocol_sub.paidThroughBlock == orig_paid_through_block + 302_400 + 1  # pay period


def test_subscription_payment_checks(new_ai_wallet, agent, alpha_token, alpha_token_whale):
    """Test canMakeSubscriptionPayments function"""
    # Initially both should be true since in trial period
    can_pay_agent, can_pay_protocol = new_ai_wallet.canMakeSubscriptionPayments(agent)
    assert can_pay_agent and can_pay_protocol

    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Should be false for both since no funds
    can_pay_agent, can_pay_protocol = new_ai_wallet.canMakeSubscriptionPayments(agent)
    assert not can_pay_agent and not can_pay_protocol

    # Fund wallet with just enough for agent subscription
    alpha_token.transfer(new_ai_wallet, 5 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Should be true for agent but false for protocol
    can_pay_agent, can_pay_protocol = new_ai_wallet.canMakeSubscriptionPayments(agent)
    assert can_pay_agent and not can_pay_protocol

    # Fund wallet with enough for protocol subscription
    alpha_token.transfer(new_ai_wallet, 10 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Should be true for both
    can_pay_agent, can_pay_protocol = new_ai_wallet.canMakeSubscriptionPayments(agent)
    assert can_pay_agent and can_pay_protocol


def test_subscription_pricing_removal(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test subscription behavior when pricing is removed and re-added"""
    # Initial state check
    agent_info = new_ai_wallet.agentSettings(agent)
    protocol_sub = new_ai_wallet.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0

    # Remove both subscription prices
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Trigger subscription check
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0 and d != 0

    # Verify subscriptions are cleared
    agent_info = new_ai_wallet.agentSettings(agent)
    protocol_sub = new_ai_wallet.protocolSub()
    assert agent_info.paidThroughBlock == 0
    assert protocol_sub.paidThroughBlock == 0

    # Re-add subscription prices
    assert price_sheets.setAgentSubPrice(agent, alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert price_sheets.setProtocolSubPrice(alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)

    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0 and d != 0

    # Verify new trial periods started
    agent_info = new_ai_wallet.agentSettings(agent)
    protocol_sub = new_ai_wallet.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0


def test_subscription_payment_insufficient_balance(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test subscription payment behavior with insufficient balance"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)

    # Fund wallet with less than required for subscriptions
    alpha_token.transfer(new_ai_wallet, 2 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Verify cannot make payments
    can_pay_agent, can_pay_protocol = new_ai_wallet.canMakeSubscriptionPayments(agent)
    assert not can_pay_agent and not can_pay_protocol

    # Try to trigger subscription payment - should still work but not pay subscription
    orig_agent_paid_through = new_ai_wallet.agentSettings(agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet.protocolSub().paidThroughBlock

    with boa.reverts("insufficient balance for protocol payment"):
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)

    # remove price, will allow transaction through
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)

    # trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 2 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0

    # Verify paid through blocks haven't changed
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_subscription_status_view_functions(new_ai_wallet, agent, governor, price_sheets):
    """Test getAgentSubscriptionStatus and getProtocolSubscriptionStatus view functions"""
    # Check during trial period
    agent_payment, agent_paid_through, agent_changed = new_ai_wallet.getAgentSubscriptionStatus(agent)
    protocol_payment, protocol_paid_through, protocol_changed = new_ai_wallet.getProtocolSubscriptionStatus()
    
    assert agent_payment == 0  # No payment needed during trial
    assert protocol_payment == 0  # No payment needed during trial
    assert agent_paid_through > 0  # Trial period active
    assert protocol_paid_through > 0  # Trial period active
    assert not agent_changed  # No state change
    assert not protocol_changed  # No state change

    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Check after trial period
    agent_payment, agent_paid_through, agent_changed = new_ai_wallet.getAgentSubscriptionStatus(agent)
    protocol_payment, protocol_paid_through, protocol_changed = new_ai_wallet.getProtocolSubscriptionStatus()
    
    assert agent_payment == 5 * EIGHTEEN_DECIMALS  # Payment needed
    assert protocol_payment == 10 * EIGHTEEN_DECIMALS  # Payment needed
    assert agent_changed  # State will change when paid
    assert protocol_changed  # State will change when paid

    # Remove pricing and check status
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    
    agent_payment, agent_paid_through, agent_changed = new_ai_wallet.getAgentSubscriptionStatus(agent)
    protocol_payment, protocol_paid_through, protocol_changed = new_ai_wallet.getProtocolSubscriptionStatus()
    
    assert agent_payment == 0  # No payment needed when no pricing
    assert protocol_payment == 0  # No payment needed when no pricing
    assert agent_changed  # State will change to clear paid through
    assert protocol_changed  # State will change to clear paid through


def test_multiple_subscription_payments(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test multiple subscription payments in sequence"""
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # First payment
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    first_agent_paid_through = new_ai_wallet.agentSettings(agent).paidThroughBlock
    first_protocol_paid_through = new_ai_wallet.protocolSub().paidThroughBlock
    
    # Fast forward past first payment period
    boa.env.time_travel(blocks=302_400 + 1)
    
    # Second payment
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    second_agent_paid_through = new_ai_wallet.agentSettings(agent).paidThroughBlock
    second_protocol_paid_through = new_ai_wallet.protocolSub().paidThroughBlock
    
    # Verify paid through blocks increased correctly
    assert second_agent_paid_through > first_agent_paid_through
    assert second_protocol_paid_through > first_protocol_paid_through
    assert second_agent_paid_through == first_agent_paid_through + 302_400 + 1
    assert second_protocol_paid_through == first_protocol_paid_through + 302_400 + 1


def test_subscription_state_transitions(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test subscription state transitions and edge cases"""
    # Initial state - in trial
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock > 0
    assert new_ai_wallet.protocolSub().paidThroughBlock > 0
    
    # Remove pricing during trial
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)
    
    # Trigger check - should clear paid through
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock == 0
    assert new_ai_wallet.protocolSub().paidThroughBlock == 0
    
    # Re-add pricing with different amounts
    assert price_sheets.setAgentSubPrice(agent, alpha_token, 7 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert price_sheets.setProtocolSubPrice(alpha_token, 12 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    
    # Trigger check - should start new trial
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    trial_agent_paid_through = new_ai_wallet.agentSettings(agent).paidThroughBlock
    trial_protocol_paid_through = new_ai_wallet.protocolSub().paidThroughBlock
    assert trial_agent_paid_through > 0
    assert trial_protocol_paid_through > 0
    
    # Fast forward past trial
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Trigger payment with new amounts
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    
    # Verify new payment amounts in logs
    agent_log = filter_logs(new_ai_wallet, "AgentSubscriptionPaid")[-1]
    protocol_log = filter_logs(new_ai_wallet, "ProtocolSubscriptionPaid")[-1]
    assert agent_log.amount == 7 * EIGHTEEN_DECIMALS
    assert protocol_log.amount == 12 * EIGHTEEN_DECIMALS


def test_protocol_transaction_fees(new_ai_wallet, owner, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, agent):
    """Test protocol transaction fees"""
    # Remove agent pricing to isolate protocol fees
    assert price_sheets.setAgentTxPricingEnabled(False, sender=governor)
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    assert not new_ai_wallet.hasEnoughForTxFees(agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert new_ai_wallet.hasEnoughForTxFees(agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)

    pre_protocol_wallet = alpha_token.balanceOf(governor)

    # Test deposit fee (0.50%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 200 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256  # DEPOSIT
    assert log.transactionUsdValue == 200 * EIGHTEEN_DECIMALS
    assert log.protocolRecipient == governor
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 1 * EIGHTEEN_DECIMALS  # 0.50% of 200
    assert log.protocolUsdValue == 1 * EIGHTEEN_DECIMALS
    assert log.agentAsset == ZERO_ADDRESS
    assert log.agentAssetAmount == 0

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount
    pre_protocol_wallet = new_protocol_wallet

    # Test withdrawal fee (1.00%)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 1 * EIGHTEEN_DECIMALS  # 1.00% of 100
    assert log.protocolUsdValue == 1 * EIGHTEEN_DECIMALS
    assert log.protocolRecipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount
    pre_protocol_wallet = new_protocol_wallet

    # Test rebalance fee (1.50%)
    a, b, c, d = new_ai_wallet.rebalance(mock_lego_alpha.legoId(), mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == REBALANCE_UINT256  # REBALANCE
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 1.5 * EIGHTEEN_DECIMALS  # 1.50% of 100
    assert log.protocolUsdValue == 1.5 * EIGHTEEN_DECIMALS
    assert log.protocolRecipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount
    pre_protocol_wallet = new_protocol_wallet

    # Test transfer fee (2.00%)
    a, b = new_ai_wallet.transferFunds(owner, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == TRANSFER_UINT256  # TRANSFER
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log.protocolUsdValue == 2 * EIGHTEEN_DECIMALS
    assert log.protocolRecipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount
    pre_protocol_wallet = new_protocol_wallet
    
    # Test swap fee (2.50%)
    a, b, c = new_ai_wallet.swapTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token, 100 * EIGHTEEN_DECIMALS, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == SWAP_UINT256  # SWAP
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 2.5 * EIGHTEEN_DECIMALS  # 2.50% of 100
    assert log.protocolUsdValue == 2.5 * EIGHTEEN_DECIMALS
    assert log.protocolRecipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount


def test_agent_transaction_fees(new_ai_wallet, owner, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, agent):
    """Test agent transaction fees"""
    # Remove protocol pricing to isolate agent fees
    assert price_sheets.removeProtocolTxPriceSheet(sender=governor)
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    assert not new_ai_wallet.hasEnoughForTxFees(agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert new_ai_wallet.hasEnoughForTxFees(agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)

    pre_agent_wallet = alpha_token.balanceOf(agent)

    # Test deposit fee (1.00%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 200 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256  # DEPOSIT
    assert log.agent == agent
    assert log.transactionUsdValue == 200 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 2 * EIGHTEEN_DECIMALS  # 1.00% of 200
    assert log.agentUsdValue == 2 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == ZERO_ADDRESS
    assert log.protocolAssetAmount == 0

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal fee (2.00%)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log.agent == agent
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log.agentUsdValue == 2 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount
    pre_agent_wallet = new_agent_wallet

    # Test rebalance fee (3.00%)
    a, b, c, d = new_ai_wallet.rebalance(mock_lego_alpha.legoId(), mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == REBALANCE_UINT256  # REBALANCE
    assert log.agent == agent
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 3 * EIGHTEEN_DECIMALS  # 3.00% of 100
    assert log.agentUsdValue == 3 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount
    pre_agent_wallet = new_agent_wallet

    # Test transfer fee (4.00%)
    a, b = new_ai_wallet.transferFunds(owner, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == TRANSFER_UINT256  # TRANSFER
    assert log.agent == agent
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 4 * EIGHTEEN_DECIMALS  # 4.00% of 100
    assert log.agentUsdValue == 4 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount
    pre_agent_wallet = new_agent_wallet

    # Test swap fee (5.00%)
    a, b, c = new_ai_wallet.swapTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token, 100 * EIGHTEEN_DECIMALS, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == SWAP_UINT256  # SWAP
    assert log.agent == agent
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 5 * EIGHTEEN_DECIMALS  # 5.00% of 100
    assert log.agentUsdValue == 5 * EIGHTEEN_DECIMALS

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount


def test_combined_transaction_fees(new_ai_wallet, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, agent):
    """Test combined protocol and agent transaction fees"""
    # Enable both protocol and agent fees
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    assert not new_ai_wallet.hasEnoughForTxFees(agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert new_ai_wallet.hasEnoughForTxFees(agent, DEPOSIT_UINT256, 200 * EIGHTEEN_DECIMALS)

    pre_protocol_wallet = alpha_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(agent)

    # Test deposit fees (protocol: 0.50% + agent: 1.00%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 200 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256  # DEPOSIT
    assert log.transactionUsdValue == 200 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 1 * EIGHTEEN_DECIMALS  # 0.50% of 200
    assert log.protocolUsdValue == 1 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 2 * EIGHTEEN_DECIMALS  # 1.00% of 200
    assert log.agentUsdValue == 2 * EIGHTEEN_DECIMALS
    assert log.protocolRecipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount
    pre_protocol_wallet = new_protocol_wallet

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal fees (protocol: 1.00% + agent: 2.00%)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log.transactionUsdValue == 100 * EIGHTEEN_DECIMALS
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 1 * EIGHTEEN_DECIMALS  # 1.00% of 100
    assert log.protocolUsdValue == 1 * EIGHTEEN_DECIMALS
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log.agentUsdValue == 2 * EIGHTEEN_DECIMALS

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.protocolAssetAmount

    new_agent_wallet = alpha_token.balanceOf(agent)
    assert new_agent_wallet == pre_agent_wallet + log.agentAssetAmount


def test_wallet_transaction_fee_edge_cases(new_ai_wallet, alpha_token, owner, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, agent, oracle_custom):
    """Test edge cases for transaction fees"""
    # Enable both protocol and agent fees
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # not enough to pay agent tx fee
    with boa.reverts("insufficient balance for agent tx fee payment"):
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 1000 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)

    # Test with price feed returning zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert len(logs) == 0  # No fees when price feed returns zero

    # Test owner bypass of agent fees
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=owner)
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert len(logs) == 0  # No agent fees for owner


def test_batch_transaction_fees(new_ai_wallet, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, agent):
    """Test transaction fees in batch operations"""
    # Enable both protocol and agent fees
    assert price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_protocol_wallet = alpha_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(agent)

    # Create batch instructions
    instructions = [
        # Deposit instruction
        (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),
        # Withdrawal instruction
        (WITHDRAWAL_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0)
    ]

    # Execute batch
    assert new_ai_wallet.performManyActions(instructions, sender=agent)

    # Verify batch fees
    log = filter_logs(new_ai_wallet, "BatchTransactionFeesPaid")[0]
    assert log.agent == agent
    # Protocol fees: (0.50% of 100) + (1.00% of 50) = 1 alpha
    assert log.protocolAsset == alpha_token.address
    assert log.protocolAssetAmount == 1 * EIGHTEEN_DECIMALS
    assert log.protocolUsdValue == 1 * EIGHTEEN_DECIMALS
    # Agent fees: (1.00% of 100) + (2.00% of 50) = 2 alpha
    assert log.agentAsset == alpha_token.address
    assert log.agentAssetAmount == 2 * EIGHTEEN_DECIMALS
    assert log.agentUsdValue == 2 * EIGHTEEN_DECIMALS

    assert alpha_token.balanceOf(governor) == pre_protocol_wallet + log.protocolAssetAmount
    assert alpha_token.balanceOf(agent) == pre_agent_wallet + log.agentAssetAmount


def test_subscription_status_during_trial(new_ai_wallet, agent):
    """Test subscription status checks during trial period"""
    # Check initial trial period status
    agent_payment, agent_paid_through, agent_changed = new_ai_wallet.getAgentSubscriptionStatus(agent)
    protocol_payment, protocol_paid_through, protocol_changed = new_ai_wallet.getProtocolSubscriptionStatus()
    
    # During trial period, no payment should be needed
    assert agent_payment == 0
    assert protocol_payment == 0
    assert not agent_changed
    assert not protocol_changed
    
    # Verify trial period end blocks
    agent_info = new_ai_wallet.agentSettings(agent)
    protocol_sub = new_ai_wallet.protocolSub()
    assert agent_paid_through == agent_info.paidThroughBlock
    assert protocol_paid_through == protocol_sub.paidThroughBlock


def test_subscription_payment_zero_price(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test subscription payment behavior when price feed returns zero"""
    # Fast forward past trial period
    boa.env.time_travel(blocks=43_200 + 1)
    
    # Set price to zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Get original paid through blocks
    orig_agent_paid_through = new_ai_wallet.agentSettings(agent).paidThroughBlock
    orig_protocol_paid_through = new_ai_wallet.protocolSub().paidThroughBlock
    
    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0
    
    # Verify no subscription payments were made
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet.protocolSub().paidThroughBlock == orig_protocol_paid_through
    
    # Verify no subscription events were emitted
    agent_logs = filter_logs(new_ai_wallet, "AgentSubscriptionPaid")
    protocol_logs = filter_logs(new_ai_wallet, "ProtocolSubscriptionPaid")
    assert len(agent_logs) == 0
    assert len(protocol_logs) == 0


def test_transaction_fees_zero_usd_value(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test transaction fee behavior with zero USD value"""
    # Set price to zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Perform transaction
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0
    
    # Verify no transaction fees were charged
    logs = filter_logs(new_ai_wallet, "TransactionFeePaid")
    assert len(logs) == 0


def test_transaction_fees_different_assets(new_ai_wallet, agent, oracle_custom, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets):
    """Test transaction fees with different assets for protocol vs agent"""
    
    oracle_custom.setPrice(bravo_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)

    # Set different fee assets for protocol and agent
    assert price_sheets.setProtocolTxPriceSheet(
        bravo_token,
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        sender=governor
    )
    
    assert price_sheets.setAgentTxPriceSheet(
        agent,
        alpha_token,
        100,    # depositFee (1.00%)
        200,    # withdrawalFee (2.00%)
        300,    # rebalanceFee (3.00%)
        400,    # transferFee (4.00%)
        500,    # swapFee (5.00%)
        sender=governor
    )
    
    # Fund wallet with both tokens
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    bravo_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    
    pre_protocol_wallet = bravo_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(agent)
    
    # Perform transaction
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 200 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    
    # Verify fees in different assets
    log = filter_logs(new_ai_wallet, "TransactionFeePaid")[0]
    assert log.protocolAsset == bravo_token.address
    assert log.agentAsset == alpha_token.address
    assert log.protocolAssetAmount == 1 * EIGHTEEN_DECIMALS  # 0.50% of 200
    assert log.agentAssetAmount == 2 * EIGHTEEN_DECIMALS  # 1.00% of 200
    
    # Verify balances
    assert bravo_token.balanceOf(governor) == pre_protocol_wallet + log.protocolAssetAmount
    assert alpha_token.balanceOf(agent) == pre_agent_wallet + log.agentAssetAmount

