import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, YIELD_OPP_UINT256, HUNDRED_PERCENT
from contracts.core.templates import UserWalletTemplate, UserWalletConfigTemplate

TRIAL_AMOUNT = 10 * EIGHTEEN_DECIMALS


@pytest.fixture(scope="module")
def new_ai_wallet(agent_factory, owner):
    w = agent_factory.createUserWallet(owner, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return UserWalletTemplate.at(w)


@pytest.fixture(scope="module")
def new_ai_wallet_config(new_ai_wallet):
    return UserWalletConfigTemplate.at(new_ai_wallet.walletConfig())


@pytest.fixture(scope="module")
def mock_lego_alpha_third(alpha_token, alpha_token_erc4626_vault_third, lego_registry, addy_registry_deploy, governor):
    addr = boa.load("contracts/mock/MockLego.vy", addy_registry_deploy, name="mock_lego_alpha_another")
    assert addr.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault_third, sender=governor)
    lego_registry.registerNewLego(addr, "Mock Lego Alpha Another", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


@pytest.fixture(scope="module")
def alpha_token_erc4626_vault_third(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault_another")


@pytest.fixture(scope="module", autouse=True)
def setup_trial_funds(agent_factory, alpha_token, alpha_token_whale, governor):
    """Setup trial funds with alpha token"""

    # Transfer tokens to factory for trial funds
    alpha_token.transfer(agent_factory, TRIAL_AMOUNT, sender=alpha_token_whale)

    # Set trial funds data
    assert agent_factory.setTrialFundsData(alpha_token, TRIAL_AMOUNT, sender=governor)


#########
# Tests #
#########


def test_set_trial_funds_data(agent_factory, bravo_token, governor, sally):
    """Test setting trial funds data in AgentFactory"""
    trial_amount = 20 * EIGHTEEN_DECIMALS

    # Test setting valid trial funds data
    assert agent_factory.setTrialFundsData(bravo_token, trial_amount, sender=governor)
    log = filter_logs(agent_factory, "TrialFundsDataSet")[0]
    assert log.asset == bravo_token.address
    assert log.amount == trial_amount

    # Verify stored data
    trial_data = agent_factory.trialFundsData()
    assert trial_data.asset == bravo_token.address
    assert trial_data.amount == trial_amount

    # Test permissions
    with boa.reverts("no perms"):
        agent_factory.setTrialFundsData(bravo_token, trial_amount, sender=sally)

    # Test invalid inputs
    assert not agent_factory.setTrialFundsData(ZERO_ADDRESS, trial_amount, sender=governor)


def test_wallet_creation_with_trial_funds(agent_factory, alpha_token, owner):
    """Test wallet creation with trial funds transfer"""

    # Create wallet and verify trial funds transfer
    wallet_addr = agent_factory.createUserWallet(owner)
    assert wallet_addr != ZERO_ADDRESS

    # Verify trial funds in new wallet
    assert alpha_token.balanceOf(wallet_addr) == TRIAL_AMOUNT

    # Verify trial funds data in wallet
    wallet = UserWalletTemplate.at(wallet_addr)
    assert wallet.trialFundsAsset() == alpha_token.address
    assert wallet.trialFundsInitialAmount() == TRIAL_AMOUNT


def test_trial_funds_restrictions(new_ai_wallet, alpha_token, owner, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test trial funds usage restrictions"""

    # Try to deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)
    assert assetAmountDeposited == TRIAL_AMOUNT
    assert vaultTokenAmountReceived == TRIAL_AMOUNT

    # Try to withdraw trial funds (should fail)
    with boa.reverts("recipient not allowed"):
        new_ai_wallet.transferFunds(agent, TRIAL_AMOUNT, alpha_token, sender=owner)


def test_get_total_underlying_user(new_ai_wallet, alpha_token, agent, lego_registry, mock_lego_alpha, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test getTotalUnderlyingForUser across multiple legos"""

    # Initial check
    assert lego_registry.getUnderlyingForUser(new_ai_wallet, alpha_token) == 0

    # Split trial funds between two legos
    half_amount = TRIAL_AMOUNT // 2

    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, half_amount, sender=agent.address)

    # Check total underlying after first deposit
    total_underlying = lego_registry.getUnderlyingForUser(new_ai_wallet, alpha_token)
    assert total_underlying == half_amount

    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha_another.legoId(), alpha_token, alpha_token_erc4626_vault_another, half_amount, sender=agent.address)

    # Check total underlying after second deposit
    total_underlying = lego_registry.getUnderlyingForUser(new_ai_wallet, alpha_token)
    assert total_underlying == TRIAL_AMOUNT


def test_trial_funds_clawback(new_ai_wallet, agent_factory, alpha_token, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test trial funds clawback functionality"""

    # Deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)
    assert assetAmountDeposited == TRIAL_AMOUNT
    assert vaultTokenAmountReceived == TRIAL_AMOUNT

    # Clawback trial funds
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    assert alpha_token.balanceOf(agent_factory) == TRIAL_AMOUNT


def test_partial_trial_funds_deployment(new_ai_wallet, agent_factory, alpha_token, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test behavior when only part of trial funds are deployed"""

    # Deploy half of trial funds
    half_amount = TRIAL_AMOUNT // 2
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, half_amount, sender=agent.address)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount

    # Clawback trial funds
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    assert alpha_token.balanceOf(agent_factory) == TRIAL_AMOUNT


def test_wallet_creation_insufficient_trial_funds(agent_factory, bravo_token, bravo_token_whale, governor, owner):
    """Test wallet creation when factory has insufficient trial funds"""
    all_funds = bravo_token.balanceOf(agent_factory)
    bravo_token.transfer(bravo_token_whale, all_funds, sender=agent_factory.address)

    # Set trial funds data but don't transfer enough to factory
    assert agent_factory.setTrialFundsData(bravo_token, TRIAL_AMOUNT, sender=governor)
    bravo_token.transfer(agent_factory, TRIAL_AMOUNT // 2, sender=bravo_token_whale)

    # Create wallet - should work but with reduced trial funds
    wallet_addr = agent_factory.createUserWallet(owner)
    wallet = UserWalletTemplate.at(wallet_addr)

    # Verify reduced trial funds
    assert bravo_token.balanceOf(wallet_addr) == TRIAL_AMOUNT // 2
    assert wallet.trialFundsAsset() == bravo_token.address
    assert wallet.trialFundsInitialAmount() == TRIAL_AMOUNT // 2


def test_trial_funds_with_zero_amount(agent_factory, alpha_token, governor):
    """Test setting trial funds with zero amount"""
    # Set trial funds asset with zero amount
    assert not agent_factory.setTrialFundsData(alpha_token, 0, sender=governor)


def test_trial_funds_balance_calculations(new_ai_wallet, agent_factory, alpha_token, agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, lego_registry):
    """Test trial funds balance calculations with split deployments"""

    # Split trial funds between wallet and two legos
    third_amount = TRIAL_AMOUNT // 3

    # Deploy to first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, third_amount, sender=agent.address)

    # Deploy to second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha_another.legoId(), alpha_token, alpha_token_erc4626_vault_another, third_amount, sender=agent.address)

    # Verify balances
    deployed_balance = lego_registry.getUnderlyingForUser(new_ai_wallet, alpha_token)
    wallet_balance = alpha_token.balanceOf(new_ai_wallet)
    assert deployed_balance == 2 * third_amount  # Two thirds deployed
    assert wallet_balance == TRIAL_AMOUNT - deployed_balance  # One third remains in wallet


def test_trial_funds_availability_edge_cases(new_ai_wallet, new_ai_wallet_config, alpha_token, agent, mock_lego_alpha, alpha_token_erc4626_vault, alpha_token_whale):
    """Test edge cases in trial funds availability calculations"""

    # Case 1: All funds deployed
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)

    # Verify no funds available for transfer
    with boa.reverts():  # Should revert due to no available funds
        new_ai_wallet.transferFunds(agent, TRIAL_AMOUNT // 2, alpha_token, sender=agent.address)

    # Case 2: Partial deployment with additional deposits
    # First withdraw everything
    assetAmountReceived, vaultTokenAmountBurned, _ = new_ai_wallet.withdrawTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)

    # Deploy half
    half_amount = TRIAL_AMOUNT // 2
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, half_amount, sender=agent.address)

    # Add extra funds from external source
    alpha_token.transfer(new_ai_wallet, TRIAL_AMOUNT, sender=alpha_token_whale)

    # Should only allow transfer of added funds, not trial funds
    transferrable_amount = new_ai_wallet_config.getAvailableTxAmount(alpha_token, MAX_UINT256, True)
    assert transferrable_amount == TRIAL_AMOUNT  # Only the additional funds are available


def test_trial_funds_with_multiple_assets(agent_factory, alpha_token, bravo_token, owner, governor, alpha_token_whale, bravo_token_whale):
    """Test trial funds behavior with multiple assets"""

    # Setup trial funds with both tokens
    alpha_amount = 5 * EIGHTEEN_DECIMALS
    bravo_amount = 7 * EIGHTEEN_DECIMALS

    # Transfer tokens to factory
    alpha_token.transfer(agent_factory, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(agent_factory, bravo_amount, sender=bravo_token_whale)

    # Set trial funds for first token
    assert agent_factory.setTrialFundsData(alpha_token, alpha_amount, sender=governor)

    # Create first wallet
    wallet1 = agent_factory.createUserWallet(owner)
    wallet1_contract = UserWalletTemplate.at(wallet1)

    # Verify first wallet trial funds
    assert alpha_token.balanceOf(wallet1) == alpha_amount
    assert wallet1_contract.trialFundsAsset() == alpha_token.address
    assert wallet1_contract.trialFundsInitialAmount() == alpha_amount

    # Set trial funds for second token
    assert agent_factory.setTrialFundsData(bravo_token, bravo_amount, sender=governor)

    # Create second wallet
    wallet2 = agent_factory.createUserWallet(owner)
    wallet2_contract = UserWalletTemplate.at(wallet2)

    # Verify second wallet trial funds
    assert bravo_token.balanceOf(wallet2) == bravo_amount
    assert wallet2_contract.trialFundsAsset() == bravo_token.address
    assert wallet2_contract.trialFundsInitialAmount() == bravo_amount


def test_trial_funds_recovery_complex(new_ai_wallet, agent_factory, alpha_token, agent, mock_lego_alpha, mock_lego_alpha_another, mock_lego_alpha_third, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_erc4626_vault_third):
    """Test trial funds recovery with multiple deployed positions"""

    # Split trial funds across three legos
    third_amount = TRIAL_AMOUNT // 3

    # Deploy to first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, third_amount, sender=agent.address)

    # Deploy to second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha_another.legoId(), alpha_token, alpha_token_erc4626_vault_another, third_amount, sender=agent.address)

    # Deploy to third lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha_third.legoId(), alpha_token, alpha_token_erc4626_vault_third, third_amount, sender=agent.address)

    # Recover trial funds
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    assert alpha_token.balanceOf(agent_factory) == TRIAL_AMOUNT


def test_trial_funds_recovery_many_wallets(agent_factory, alpha_token, owner, agent, governor, alpha_token_whale, mock_lego_alpha, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test trial funds recovery from multiple wallets in a single transaction"""
    pre_agent_factory = alpha_token.balanceOf(agent_factory)

    # Transfer additional funds to factory for second wallet
    new_trial_funds = TRIAL_AMOUNT * 2
    alpha_token.transfer(agent_factory, new_trial_funds, sender=alpha_token_whale)

    # Create two wallets
    wallet1 = agent_factory.createUserWallet(owner)
    wallet2 = agent_factory.createUserWallet(owner)
    wallet1_contract = UserWalletTemplate.at(wallet1)
    wallet2_contract = UserWalletTemplate.at(wallet2)

    # Verify initial trial funds
    assert alpha_token.balanceOf(wallet1) == TRIAL_AMOUNT
    assert alpha_token.balanceOf(wallet2) == TRIAL_AMOUNT

    # Deposit trial funds from both wallets
    wallet1_contract.depositTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)
    wallet2_contract.depositTokens(mock_lego_alpha_another.legoId(), alpha_token, alpha_token_erc4626_vault_another, TRIAL_AMOUNT, sender=agent.address)

    # Verify trial funds are in vaults
    assert alpha_token.balanceOf(wallet1) == 0
    assert alpha_token_erc4626_vault.balanceOf(wallet1) != 0
    assert alpha_token.balanceOf(wallet2) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(wallet2) != 0

    # Recover trial funds from both wallets
    assert wallet1_contract.clawBackTrialFunds(sender=agent_factory.address)
    assert wallet2_contract.clawBackTrialFunds(sender=agent_factory.address)

    # Verify trial funds are gone
    assert alpha_token_erc4626_vault.balanceOf(wallet1) == 0
    assert alpha_token.balanceOf(wallet1) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(wallet2) == 0
    assert alpha_token.balanceOf(wallet2) == 0

    # Verify all funds were recovered to the factory
    assert alpha_token.balanceOf(agent_factory) == pre_agent_factory + new_trial_funds

    # Verify trial funds data was cleared in both wallets
    assert wallet1_contract.trialFundsAsset() == ZERO_ADDRESS
    assert wallet1_contract.trialFundsInitialAmount() == 0
    assert wallet2_contract.trialFundsAsset() == ZERO_ADDRESS
    assert wallet2_contract.trialFundsInitialAmount() == 0


def test_trial_funds_vault_token_transfer_restrictions(new_ai_wallet, alpha_token, agent, mock_lego_alpha, alpha_token_erc4626_vault, owner):
    """Test restrictions on transferring vault tokens that represent trial funds"""

    # First deposit trial funds into mock lego to get vault tokens
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)
    assert vaultTokenAmountReceived == TRIAL_AMOUNT

    # Try to transfer vault tokens - should fail since they represent trial funds
    with boa.reverts("cannot transfer trial funds vault token"):
        new_ai_wallet.transferFunds(owner, vaultTokenAmountReceived, alpha_token_erc4626_vault, sender=owner)

    # Verify vault tokens are still in wallet
    assert alpha_token_erc4626_vault.balanceOf(new_ai_wallet) == vaultTokenAmountReceived


def test_trial_funds_vault_token_partial_transfer(lego_registry, new_ai_wallet, alpha_token, alpha_token_whale, agent, mock_lego_alpha, alpha_token_erc4626_vault, owner):
    """Test partial transfers of vault tokens while maintaining minimum trial funds"""

    assert new_ai_wallet.trialFundsAsset() == alpha_token.address
    assert new_ai_wallet.trialFundsInitialAmount() == TRIAL_AMOUNT

    # First deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)

    # Add extra funds on top of trial funds
    extra_amount = TRIAL_AMOUNT // 2
    alpha_token.transfer(new_ai_wallet, extra_amount, sender=alpha_token_whale)

    # Deposit extra funds to get more vault tokens
    assetAmountDeposited, _, extra_vault_tokens, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, extra_amount, sender=agent.address)

    underlying = lego_registry.getUnderlyingAsset(alpha_token_erc4626_vault)
    assert underlying == alpha_token.address

    underlying_amount = lego_registry.getUnderlyingForUser(new_ai_wallet, alpha_token)

    # Should be able to transfer the extra vault tokens
    new_ai_wallet.transferFunds(owner, extra_vault_tokens, alpha_token_erc4626_vault, sender=owner)

    # But should not be able to transfer more
    with boa.reverts("cannot transfer trial funds vault token"):
        new_ai_wallet.transferFunds(owner, 1, alpha_token_erc4626_vault, sender=owner)


def test_trial_funds_vault_token_transfer_different_vault(new_ai_wallet, alpha_token, agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, owner):
    """Test transfer restrictions apply across different vaults for same underlying asset"""

    # Split trial funds between two vaults
    half_amount = TRIAL_AMOUNT // 2

    # Deposit into first vault
    assetAmountDeposited, _, vault1_tokens, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, half_amount, sender=agent.address)

    # Deposit into second vault
    assetAmountDeposited, _, vault2_tokens, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha_another.legoId(), alpha_token, alpha_token_erc4626_vault_another, half_amount, sender=agent.address)

    # Try to transfer vault tokens from first vault - should fail
    with boa.reverts("cannot transfer trial funds vault token"):
        new_ai_wallet.transferFunds(owner, vault1_tokens, alpha_token_erc4626_vault, sender=owner)

    # Try to transfer vault tokens from second vault - should also fail
    with boa.reverts("cannot transfer trial funds vault token"):
        new_ai_wallet.transferFunds(owner, vault2_tokens, alpha_token_erc4626_vault_another, sender=owner)


def test_trial_funds_recovery_permissions(new_ai_wallet, agent_factory, owner, sally):
    """Test that only authorized addresses can recover trial funds"""
    
    # Test agent factory can recover
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    
    # Test unauthorized address cannot recover
    with boa.reverts("no perms"):
        new_ai_wallet.clawBackTrialFunds(sender=sally)


def test_trial_funds_recovery_with_yield(new_ai_wallet, agent_factory, alpha_token, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test recovery when vault has generated yield beyond trial funds amount"""
    
    # Deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)
    
    # Record balances before recovery
    pre_factory_balance = alpha_token.balanceOf(agent_factory)
    
    # Recover trial funds
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    
    # Verify factory got trial funds
    recovered_amount = alpha_token.balanceOf(agent_factory) - pre_factory_balance
    assert recovered_amount == TRIAL_AMOUNT
    
    # Verify trial funds data is cleared
    assert new_ai_wallet.trialFundsAsset() == ZERO_ADDRESS
    assert new_ai_wallet.trialFundsInitialAmount() == 0


def test_trial_funds_recovery_partial_success(new_ai_wallet, agent_factory, alpha_token, agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test recovery when some vaults succeed and others fail"""
    
    # Split trial funds between two vaults
    half_amount = TRIAL_AMOUNT // 2
    
    # Deposit into first vault
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, half_amount, sender=agent.address)
        
    # Deposit into second vault
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha_another.legoId(), alpha_token, alpha_token_erc4626_vault_another, half_amount, sender=agent.address)
    
    # Record balances before recovery
    pre_factory_balance = alpha_token.balanceOf(agent_factory)
    
    # Recover trial funds
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    
    # Verify full recovery
    recovered_amount = alpha_token.balanceOf(agent_factory) - pre_factory_balance
    assert recovered_amount == TRIAL_AMOUNT
    
    # Verify trial funds data is cleared
    assert new_ai_wallet.trialFundsAsset() == ZERO_ADDRESS
    assert new_ai_wallet.trialFundsInitialAmount() == 0


def test_trial_funds_recovery_zero_balance(new_ai_wallet, agent_factory, alpha_token, agent):
    """Test recovery when wallet has trial funds data but zero balance"""
    
    # Verify initial trial funds data
    assert new_ai_wallet.trialFundsAsset() == alpha_token.address
    assert new_ai_wallet.trialFundsInitialAmount() == TRIAL_AMOUNT
    
    # Try recovery with no actual funds - should still return true and clear data
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)
    
    # Verify trial funds data is cleared
    assert new_ai_wallet.trialFundsAsset() == ZERO_ADDRESS
    assert new_ai_wallet.trialFundsInitialAmount() == 0


def test_trial_funds_recovery_with_extra_yield(_test, mock_lego_alpha, agent_factory, alpha_token, alpha_token_whale, new_ai_wallet, agent, alpha_token_erc4626_vault):
    # Verify initial trial funds data
    assert new_ai_wallet.trialFundsAsset() == alpha_token.address
    assert new_ai_wallet.trialFundsInitialAmount() == TRIAL_AMOUNT
    assert alpha_token.balanceOf(new_ai_wallet) == TRIAL_AMOUNT
    
    # deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = new_ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=agent.address)
    assert assetAmountDeposited == TRIAL_AMOUNT

    # send more to vault
    alpha_token.transfer(alpha_token_erc4626_vault, TRIAL_AMOUNT, sender=alpha_token_whale)

    # test underlying amount
    orig_underlying_amount = mock_lego_alpha.getUnderlyingAmount(alpha_token_erc4626_vault, vaultTokenAmountReceived)
    assert orig_underlying_amount == TRIAL_AMOUNT * 2

    pre_factory_balance = alpha_token.balanceOf(agent_factory)

    # Recover trial funds
    assert new_ai_wallet.clawBackTrialFunds(sender=agent_factory.address)

    # Verify factory got trial funds
    take_back_amount = TRIAL_AMOUNT * 101_00 // HUNDRED_PERCENT
    assert alpha_token.balanceOf(agent_factory) == pre_factory_balance + take_back_amount

    new_vault_balance = alpha_token_erc4626_vault.balanceOf(new_ai_wallet)
    underlying_amount = mock_lego_alpha.getUnderlyingAmount(alpha_token_erc4626_vault, new_vault_balance)
    assert underlying_amount == orig_underlying_amount - take_back_amount
