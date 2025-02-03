import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from contracts.core import OracleRegistry, WalletTemplate, PriceSheets


@pytest.fixture(scope="module", autouse=True)
def setup_pricing(current_price_sheets, governor, alpha_token, agent, new_oracle, current_oracle_registry):
    new_oracle.setPrice(alpha_token.address, 1 * EIGHTEEN_DECIMALS, sender=governor)
    assert current_oracle_registry.getPrice(alpha_token.address) == 1 * EIGHTEEN_DECIMALS

    # Set protocol transaction fees
    """Setup protocol pricing for tests"""
    # Set protocol transaction fees
    assert current_price_sheets.setProtocolTxPriceSheet(
        alpha_token,
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        sender=governor
    )

    # Set protocol subscription
    assert current_price_sheets.setProtocolSubPrice(
        alpha_token,
        10 * EIGHTEEN_DECIMALS,  # usdValue
        43_200,                    # trialPeriod (1 day)
        302_400,                   # payPeriod (7 days)
        sender=governor
    )

    """Setup agent pricing for tests"""
    # Enable agent pricing
    assert current_price_sheets.setAgentTxPricingEnabled(True, sender=governor)
    assert current_price_sheets.setAgentSubPricingEnabled(True, sender=governor)

    # Set agent transaction fees
    assert current_price_sheets.setAgentTxPriceSheet(
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
    assert current_price_sheets.setAgentSubPrice(
        agent,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,   # usdValue
        43_200,                    # trialPeriod (1 day)
        302_400,                   # payPeriod (7 days)
        sender=governor
    )


@pytest.fixture(scope="module")
def current_oracle_registry(addy_registry):
    oracle_registry_addr = addy_registry.getAddy(4)
    return OracleRegistry.at(oracle_registry_addr)


@pytest.fixture(scope="module")
def current_price_sheets(addy_registry):
    price_sheets_addr = addy_registry.getAddy(3)
    return PriceSheets.at(price_sheets_addr)


@pytest.fixture(scope="module")
def new_oracle(current_oracle_registry, addy_registry, governor):
    addr = boa.load("contracts/oracles/CustomOracle.vy", addy_registry, name="new_oracle")
    assert current_oracle_registry.registerNewOraclePartner(addr, "Custom Oracle", sender=governor) != 0 # dev: invalid oracle id
    return addr


@pytest.fixture(scope="module")
def new_ai_wallet(agent_factory, owner, agent):
    w = agent_factory.createAgenticWallet(owner, agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isAgenticWallet(w)
    return WalletTemplate.at(w)


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


def test_agent_subscription_payment(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, current_price_sheets):
    """Test agent subscription payment after trial"""

    # remove protocol sub pricing and tx pricing
    assert current_price_sheets.removeProtocolSubPrice(sender=governor)
    assert current_price_sheets.setAgentTxPricingEnabled(False, sender=governor)

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


def test_protocol_subscription_payment(new_ai_wallet, alpha_token, alpha_token_whale, governor, current_price_sheets, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test protocol subscription payment after trial"""
    # remove agent sub pricing and tx pricing
    assert current_price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert current_price_sheets.setAgentTxPricingEnabled(False, sender=governor)

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
    assert log.recipient == current_price_sheets.protocolRecipient()
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


def test_subscription_pricing_removal(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, current_price_sheets):
    """Test subscription behavior when pricing is removed and re-added"""
    # Initial state check
    agent_info = new_ai_wallet.agentSettings(agent)
    protocol_sub = new_ai_wallet.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0

    # Remove both subscription prices
    assert current_price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert current_price_sheets.removeProtocolSubPrice(sender=governor)

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
    assert current_price_sheets.setAgentSubPrice(agent, alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert current_price_sheets.setProtocolSubPrice(alpha_token, 5 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)

    # Trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0 and d != 0

    # Verify new trial periods started
    agent_info = new_ai_wallet.agentSettings(agent)
    protocol_sub = new_ai_wallet.protocolSub()
    assert agent_info.paidThroughBlock > 0
    assert protocol_sub.paidThroughBlock > 0


def test_subscription_payment_insufficient_balance(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, new_oracle):
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
    new_oracle.setPrice(alpha_token.address, 0, sender=governor)

    # trigger subscription check
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 2 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert a != 0

    # Verify paid through blocks haven't changed
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock == orig_agent_paid_through
    assert new_ai_wallet.protocolSub().paidThroughBlock == orig_protocol_paid_through


def test_subscription_status_view_functions(new_ai_wallet, agent, alpha_token, alpha_token_whale, governor, current_price_sheets):
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
    assert current_price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert current_price_sheets.removeProtocolSubPrice(sender=governor)
    
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


def test_subscription_state_transitions(new_ai_wallet, agent, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, current_price_sheets):
    """Test subscription state transitions and edge cases"""
    # Initial state - in trial
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock > 0
    assert new_ai_wallet.protocolSub().paidThroughBlock > 0
    
    # Remove pricing during trial
    assert current_price_sheets.removeAgentSubPrice(agent, sender=governor)
    assert current_price_sheets.removeProtocolSubPrice(sender=governor)
    
    # Trigger check - should clear paid through
    alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    a, b, c, d = new_ai_wallet.depositTokens(mock_lego_alpha.legoId(), alpha_token, 100 * EIGHTEEN_DECIMALS, alpha_token_erc4626_vault, sender=agent)
    assert new_ai_wallet.agentSettings(agent).paidThroughBlock == 0
    assert new_ai_wallet.protocolSub().paidThroughBlock == 0
    
    # Re-add pricing with different amounts
    assert current_price_sheets.setAgentSubPrice(agent, alpha_token, 7 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    assert current_price_sheets.setProtocolSubPrice(alpha_token, 12 * EIGHTEEN_DECIMALS, 43_200, 302_400, sender=governor)
    
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

