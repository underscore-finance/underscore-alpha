import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256
from contracts.core.templates import UserWalletTemplate, UserWalletConfigTemplate


@pytest.fixture(scope="module")
def new_ai_wallet(agent_factory, owner, bob_agent):
    w = agent_factory.createUserWallet(owner, bob_agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return UserWalletTemplate.at(w)


@pytest.fixture(scope="module")
def new_ai_wallet_config(new_ai_wallet):
    return UserWalletConfigTemplate.at(new_ai_wallet.walletConfig())


@pytest.fixture(scope="module", autouse=True)
def setup_pricing(price_sheets, governor, alpha_token, bob_agent, oracle_custom, oracle_registry):
    oracle_custom.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set protocol transaction fees
    """Setup protocol pricing for tests"""
    # Set protocol transaction fees
    assert price_sheets.setProtocolTxPriceSheet(
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        300,    # addLiqFee (3.00%)
        350,    # removeLiqFee (3.50%)
        400,    # claimRewardsFee (4.00%)
        450,    # borrowFee (4.50%)
        500,    # repayFee (5.00%)
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
    assert price_sheets.setAgentSubPricingEnabled(True, sender=governor)

    # Set bob_agent subscription pricing (instead of transaction fees)
    assert price_sheets.setAgentSubPrice(
        bob_agent,
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
    assert price_sheets.setAgentSubPricingEnabled(False, sender=governor)

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
   
    log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[0]
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
    assert price_sheets.setAgentSubPricingEnabled(False, sender=governor)

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
   
    log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[0]
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
    agent_log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[1]
    protocol_log = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")[0]
    assert agent_log.amount == 7 * EIGHTEEN_DECIMALS
    assert protocol_log.amount == 12 * EIGHTEEN_DECIMALS


def test_protocol_transaction_fees(new_ai_wallet, new_ai_wallet_config, owner, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test protocol transaction fees"""
    # Remove bob_agent pricing to isolate protocol fees
    assert price_sheets.setAgentSubPricingEnabled(False, sender=governor)
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_protocol_wallet = alpha_token.balanceOf(governor)

    # Test deposit fee (0.50%)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256  # DEPOSIT
    assert log.recipient == governor
    assert log.asset == alpha_token_erc4626_vault.address
    assert log.amount > 0  # Fee amount will depend on vault token value

    # For deposit, the fee is in vault tokens, not in alpha_token
    # So we don't check the governor's alpha_token balance here

    # Test withdrawal fee (1.00%)
    pre_protocol_wallet = alpha_token.balanceOf(governor)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log.asset == alpha_token.address
    assert log.amount > 0  # Fee amount will depend on asset value
    assert log.fee == 100  # 1.00%
    assert log.recipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet > pre_protocol_wallet
    pre_protocol_wallet = new_protocol_wallet

    # Test rebalance fee (1.50%)
    a, b, c, d = new_ai_wallet.rebalance(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, mock_lego_alpha.legoId(), alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.action == REBALANCE_UINT256  # REBALANCE
    assert log.asset == alpha_token_erc4626_vault.address
    assert log.amount > 0  # Fee amount will depend on vault token value
    assert log.recipient == governor

    # For rebalance, the fee is in vault tokens, not in alpha_token
    # So we don't check the governor's alpha_token balance here

    # Test transfer fee (2.00%)
    pre_protocol_wallet = alpha_token.balanceOf(governor)
    a, b = new_ai_wallet.transferFunds(owner, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=bob_agent)
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.action == TRANSFER_UINT256  # TRANSFER
    assert log.asset == alpha_token.address
    assert log.amount == 2 * EIGHTEEN_DECIMALS  # 2.00% of 100
    assert log.recipient == governor

    new_protocol_wallet = alpha_token.balanceOf(governor)
    assert new_protocol_wallet == pre_protocol_wallet + log.amount
    pre_protocol_wallet = new_protocol_wallet
    
    # Test swap fee (2.50%)
    bravo_token.transfer(mock_lego_alpha.address, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    
    # Get the pre-swap bravo_token balance of the governor
    pre_protocol_wallet_bravo = bravo_token.balanceOf(governor)

    # setup swap 
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(new_ai_wallet, deposit_amount, sender=alpha_token_whale)
    bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)
    instruction = (
        mock_lego_alpha.legoId(),
        deposit_amount,
        0,
        [alpha_token, bravo_token],
        [alpha_token]
    )
    a, b, c = new_ai_wallet.swapTokens([instruction], sender=bob_agent)
    log = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.action == SWAP_UINT256  # SWAP
    assert log.asset == bravo_token.address  # Fee is in bravo_token (the output token)
    assert log.amount > 0  # Fee amount will depend on asset value
    assert log.recipient == governor
    
    # Check that the governor's bravo_token balance increased by the fee amount
    new_protocol_wallet_bravo = bravo_token.balanceOf(governor)
    assert new_protocol_wallet_bravo == pre_protocol_wallet_bravo + log.amount


def test_agent_transaction_fees(new_ai_wallet, new_ai_wallet_config, owner, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test bob_agent transaction fees"""
    # Remove protocol pricing to isolate bob_agent fees
    assert price_sheets.removeProtocolTxPriceSheet(sender=governor)
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_agent_wallet = alpha_token.balanceOf(bob_agent)

    # Test deposit - no agent transaction fees should be charged
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # No agent transaction fees should be charged
    assert len(logs) == 0

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    # Agent wallet balance should remain unchanged since no fees are charged
    assert new_agent_wallet == pre_agent_wallet
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal - no agent transaction fees should be charged
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # No agent transaction fees should be charged
    assert len(logs) == 0

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    # Agent wallet balance should remain unchanged since no fees are charged
    assert new_agent_wallet == pre_agent_wallet

    # Test rebalance - no agent transaction fees should be charged
    a, b, c, d = new_ai_wallet.rebalance(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, mock_lego_alpha.legoId(), alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # No agent transaction fees should be charged
    assert len(logs) == 0

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    # Agent wallet balance should remain unchanged since no fees are charged
    assert new_agent_wallet == pre_agent_wallet


def test_combined_transaction_fees(new_ai_wallet, new_ai_wallet_config, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
    """Test combined protocol and bob_agent transaction fees"""
    # Enable protocol fees, but agent transaction fees are no longer supported
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    pre_protocol_wallet = alpha_token.balanceOf(governor)
    pre_agent_wallet = alpha_token.balanceOf(bob_agent)

    # Test deposit fees (only protocol fees should be charged)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # Only protocol fee should be charged
    assert len(logs) == 1
    log0 = logs[0]

    assert log0.action == DEPOSIT_UINT256  # DEPOSIT
    assert log0.asset == alpha_token_erc4626_vault.address
    assert log0.amount > 0  # Fee amount will depend on vault token value
    assert log0.recipient == governor
    assert not hasattr(log0, "isAgent") or not log0.isAgent

    new_protocol_wallet = alpha_token.balanceOf(governor)
    # Protocol wallet balance may not change if fee is in vault token
    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    # Agent wallet balance should remain unchanged since no agent fees are charged
    assert new_agent_wallet == pre_agent_wallet
    pre_agent_wallet = new_agent_wallet

    # Test withdrawal fees (only protocol fees should be charged)
    a, b, c = new_ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # Only protocol fee should be charged
    assert len(logs) == 1
    log0 = logs[0]

    assert log0.action == WITHDRAWAL_UINT256  # WITHDRAWAL
    assert log0.asset == alpha_token.address
    assert log0.amount > 0  # Fee amount will depend on asset value
    assert log0.recipient == governor
    assert not hasattr(log0, "isAgent") or not log0.isAgent

    new_agent_wallet = alpha_token.balanceOf(bob_agent)
    # Agent wallet balance should remain unchanged since no agent fees are charged
    assert new_agent_wallet == pre_agent_wallet


def test_wallet_transaction_fee_edge_cases(new_ai_wallet, alpha_token, owner, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent, oracle_custom):
    """Test edge cases for transaction fees"""
    # Enable both protocol and bob_agent fees
    assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
    assert price_sheets.removeProtocolSubPrice(sender=governor)

    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Test with price feed returning zero
    oracle_custom.setPrice(alpha_token.address, 0, sender=governor)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # Fees are still charged even when price feed returns zero
    assert len(logs) == 1
    assert logs[0].asset == alpha_token_erc4626_vault.address
    assert logs[0].amount > 0

    # Test owner bypass of fees
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=owner)
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    # The current implementation does not charge fees to the owner
    assert len(logs) == 0


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
    logs = filter_logs(new_ai_wallet, "UserWalletSubscriptionPaid")
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
    
    # Verify transaction fees are still charged even with zero USD value
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    assert len(logs) == 1
    assert logs[0].asset == alpha_token_erc4626_vault.address
    assert logs[0].amount > 0


def test_transaction_fees_different_assets(
    price_sheets,
    governor,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob_agent,
    mock_lego_alpha,
    alpha_token_erc4626_vault,
    new_ai_wallet,
):
    """Test transaction fees in different assets"""
    # Set protocol transaction fees in bravo_token
    assert price_sheets.setProtocolTxPriceSheet(
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        300,    # addLiqFee (3.00%)
        350,    # removeLiqFee (3.50%)
        400,    # claimRewardsFee (4.00%)
        450,    # borrowFee (4.50%)
        500,    # repayFee (5.00%)
        sender=governor
    )
    
    # Note: Agent transaction fees are no longer supported
    # Instead, we'll set up agent subscription pricing
    # Agent subscription pricing is already enabled, so we don't need to enable it again
    assert price_sheets.setAgentSubPrice(
        bob_agent,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,  # usdValue
        43_200,                   # trialPeriod (1 day)
        302_400,                  # payPeriod (7 days)
        sender=governor
    )
    
    # Fund wallet with both tokens
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    bravo_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    
    pre_protocol_wallet = bravo_token.balanceOf(governor)
    
    # Perform transaction
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 200 * EIGHTEEN_DECIMALS, sender=bob_agent)
    
    # Verify protocol fees
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    assert logs[0].asset == alpha_token_erc4626_vault.address  # Fee is in vault token, not bravo_token
    assert logs[0].amount > 0


def test_maximum_fee_boundary(price_sheets, governor):
    """Test the maximum fee boundary (10%) for transaction fees"""
    # Test setting fees at the maximum boundary (10.00%)
    assert price_sheets.setProtocolTxPriceSheet(
        1000,    # depositFee (10.00%)
        1000,    # withdrawalFee (10.00%)
        1000,    # rebalanceFee (10.00%)
        1000,    # transferFee (10.00%)
        1000,    # swapFee (10.00%)
        1000,    # addLiqFee (10.00%)
        1000,    # removeLiqFee (10.00%)
        1000,    # claimRewardsFee (10.00%)
        1000,    # borrowFee (10.00%)
        1000,    # repayFee (10.00%)
        sender=governor
    )
    
    # Verify the fees were set correctly
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.depositFee == 1000
    assert sheet.withdrawalFee == 1000
    assert sheet.rebalanceFee == 1000
    assert sheet.transferFee == 1000
    assert sheet.swapFee == 1000
    assert sheet.addLiqFee == 1000
    assert sheet.removeLiqFee == 1000
    assert sheet.claimRewardsFee == 1000
    assert sheet.borrowFee == 1000
    assert sheet.repayFee == 1000
    
    # Test setting fees above the maximum boundary (10.01%)
    assert not price_sheets.setProtocolTxPriceSheet(
        1001,    # depositFee (10.01%)
        1000,    # withdrawalFee (10.00%)
        1000,    # rebalanceFee (10.00%)
        1000,    # transferFee (10.00%)
        1000,    # swapFee (10.00%)
        1000,    # addLiqFee (10.00%)
        1000,    # removeLiqFee (10.00%)
        1000,    # claimRewardsFee (10.00%)
        1000,    # borrowFee (10.00%)
        1000,    # repayFee (10.00%)
        sender=governor
    )
    
    # Verify the fees were not changed
    sheet = price_sheets.protocolTxPriceData()
    assert sheet.depositFee == 1000  # Still at 10.00%


def test_subscription_payment_failure(new_ai_wallet, new_ai_wallet_config, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, oracle_custom):
    """Test behavior when subscription payments fail due to insufficient balance"""
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


def test_transaction_fee_calculation_with_zero_balance(new_ai_wallet, bob_agent, alpha_token, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test transaction fee calculation when token balance is zero"""
    # Don't fund the wallet, so balance is zero
    
    # Attempt a transaction
    with boa.reverts():  # Should revert due to insufficient balance
        new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    
    # No transaction fee events should be emitted
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    assert len(logs) == 0


def test_transaction_fees_at_maximum(price_sheets, governor, new_ai_wallet, bob_agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test transaction fees at the maximum allowed percentage (10%)"""
    # Set maximum transaction fees (10%)
    assert price_sheets.setProtocolTxPriceSheet(
        1000,    # depositFee (10.00%)
        1000,    # withdrawalFee (10.00%)
        1000,    # rebalanceFee (10.00%)
        1000,    # transferFee (10.00%)
        1000,    # swapFee (10.00%)
        1000,    # addLiqFee (10.00%)
        1000,    # removeLiqFee (10.00%)
        1000,    # claimRewardsFee (10.00%)
        1000,    # borrowFee (10.00%)
        1000,    # repayFee (10.00%)
        sender=governor
    )
    
    # Fund wallet
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Perform deposit transaction
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=bob_agent)
    
    # Verify fee is 10% of vault tokens received
    logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")
    assert logs[0].fee == 1000  # 10.00%
    assert logs[0].asset == alpha_token_erc4626_vault.address
    # The exact amount will depend on the vault token value



# def test_swap_tokens(ai_wallet, agent, mock_lego_alpha, alpha_token, alpha_token_whale, bravo_token, bravo_token_whale):
#     deposit_amount = 1000 * EIGHTEEN_DECIMALS
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)

#     instruction = (
#         mock_lego_alpha.legoId(),
#         deposit_amount,
#         0,
#         [alpha_token, bravo_token],
#         [alpha_token]
#     )

#     initialAmountIn, lastTokenOutAmount, lastUsdValue = ai_wallet.swapTokens([instruction], sender=agent)

#     assert lastTokenOutAmount != 0