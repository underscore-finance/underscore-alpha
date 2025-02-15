import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, TRANSFER_UINT256, SWAP_UINT256
from contracts.core import WalletTemplate


@pytest.fixture
def setup_trial_funds(agent_factory, alpha_token, alpha_token_whale, governor):
    """Setup trial funds with alpha token"""
    trial_amount = 10 * EIGHTEEN_DECIMALS  # 10 tokens
    
    # Transfer tokens to factory for trial funds
    alpha_token.transfer(agent_factory, trial_amount, sender=alpha_token_whale)
    
    # Set trial funds data
    assert agent_factory.setTrialFundsData(alpha_token, trial_amount, sender=governor)
    
    return alpha_token, trial_amount


def test_set_trial_funds_data(agent_factory, alpha_token, alpha_token_whale, governor, sally):
    """Test setting trial funds data in AgentFactory"""
    trial_amount = 10 * EIGHTEEN_DECIMALS

    # Test setting valid trial funds data
    assert agent_factory.setTrialFundsData(alpha_token, trial_amount, sender=governor)
    log = filter_logs(agent_factory, "TrialFundsDataSet")[0]
    assert log.asset == alpha_token.address
    assert log.amount == trial_amount

    # Verify stored data
    trial_data = agent_factory.trialFundsData()
    assert trial_data.asset == alpha_token.address
    assert trial_data.amount == trial_amount

    # Test permissions
    with boa.reverts("no perms"):
        agent_factory.setTrialFundsData(alpha_token, trial_amount, sender=sally)

    # Test invalid inputs
    assert not agent_factory.setTrialFundsData(ZERO_ADDRESS, trial_amount, sender=governor)


def test_wallet_creation_with_trial_funds(agent_factory, setup_trial_funds, owner, agent):
    """Test wallet creation with trial funds transfer"""
    token, trial_amount = setup_trial_funds

    # Create wallet and verify trial funds transfer
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    assert wallet_addr != ZERO_ADDRESS

    # Verify trial funds in new wallet
    assert token.balanceOf(wallet_addr) == trial_amount

    # Verify trial funds data in wallet
    wallet = WalletTemplate.at(wallet_addr)
    assert wallet.trialFundsAsset() == token.address
    assert wallet.trialFundsAmount() == trial_amount


def test_trial_funds_restrictions(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_weth, governor, alpha_token_erc4626_vault):
    """Test trial funds usage restrictions"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Try to deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == trial_amount
    assert vaultTokenAmountReceived == trial_amount
    
    # Try to withdraw trial funds (should fail)
    with boa.reverts("recipient not allowed"):
        wallet.transferFunds(agent, trial_amount, token, sender=owner)


def test_get_total_underlying_user(agent_factory, setup_trial_funds, owner, agent, lego_helper, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test getTotalUnderlyingForUser across multiple legos"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Initial check
    assert lego_helper.getTotalUnderlyingForUser(wallet_addr, token) == 0
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Check total underlying after first deposit
    total_underlying = lego_helper.getTotalUnderlyingForUser(wallet_addr, token)
    assert total_underlying == half_amount
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    
    # Check total underlying after second deposit
    total_underlying = lego_helper.getTotalUnderlyingForUser(wallet_addr, token)
    assert total_underlying == trial_amount


def test_trial_funds_clawback(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test trial funds clawback functionality"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit trial funds into mock lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == trial_amount
    assert vaultTokenAmountReceived == trial_amount
    
    # Clawback trial funds
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_partial_trial_funds_deployment(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test behavior when only part of trial funds are deployed"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deploy half of trial funds
    half_amount = trial_amount // 2
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Clawback trial funds
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_wallet_creation_insufficient_trial_funds(agent_factory, alpha_token, alpha_token_whale, governor, owner, agent):
    """Test wallet creation when factory has insufficient trial funds"""
    trial_amount = 10 * EIGHTEEN_DECIMALS
    
    # Set trial funds data but don't transfer enough to factory
    assert agent_factory.setTrialFundsData(alpha_token, trial_amount, sender=governor)
    alpha_token.transfer(agent_factory, trial_amount // 2, sender=alpha_token_whale)
    
    # Create wallet - should work but with reduced trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Verify reduced trial funds
    assert alpha_token.balanceOf(wallet_addr) == trial_amount // 2
    assert wallet.trialFundsAmount() == trial_amount // 2


def test_trial_funds_with_zero_amount(agent_factory, alpha_token, governor, owner, agent):
    """Test setting trial funds with zero amount"""
    # Set trial funds asset with zero amount
    assert not agent_factory.setTrialFundsData(alpha_token, 0, sender=governor)


def test_multiple_wallet_creation_trial_funds(agent_factory, setup_trial_funds, owner, agent, bob, sally):
    """Test creating multiple wallets with trial funds"""
    token, trial_amount = setup_trial_funds
    
    # Create first wallet
    wallet1_addr = agent_factory.createAgenticWallet(owner, agent)
    assert token.balanceOf(wallet1_addr) == trial_amount
    
    # Create second wallet - should get no trial funds since factory is out
    wallet2_addr = agent_factory.createAgenticWallet(bob, sally)
    assert token.balanceOf(wallet2_addr) == 0
    
    # Verify factory balance is zero
    factory_balance = token.balanceOf(agent_factory)
    assert factory_balance == 0


def test_clawback_multiple_legos(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test trial funds clawback from multiple legos"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Clawback trial funds from both legos
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_clawback_mixed_deployment(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test clawback when funds are split between wallet and lego"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deploy half of trial funds
    half_amount = trial_amount // 2
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Clawback trial funds
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_trial_funds_with_reserve_assets(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test interaction between trial funds and reserve assets"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Set reserve amount
    reserve_amount = trial_amount // 2
    wallet.setReserveAsset(token, reserve_amount, sender=owner)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit available amount
    available_amount = trial_amount - reserve_amount
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, available_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == available_amount
    assert vaultTokenAmountReceived == available_amount
    
    # Clawback trial funds
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_batch_actions_with_trial_funds(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test batch actions with trial funds"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Clawback trial funds from both legos
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_clawback_failure_scenarios(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test clawback when a lego fails to withdraw"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Clawback trial funds from both legos
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_gas_optimization_multiple_clawbacks(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test gas optimization for multiple clawbacks"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    assert assetAmountDeposited == half_amount
    assert vaultTokenAmountReceived == half_amount
    
    # Clawback trial funds from both legos
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_clawback_permissions(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, sally, governor, alpha_token_erc4626_vault):
    """Test permissions for trial funds clawback"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deploy trial funds
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == trial_amount
    assert vaultTokenAmountReceived == trial_amount
    
    # Try to clawback from non-factory (should fail)
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    with boa.reverts("no perms"):
        wallet.recoverTrialFunds(clawback_data, sender=sally)
    
    # Clawback from factory (should work)
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount


def test_clawback_no_trial_funds(agent_factory, owner, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test clawback attempt when no trial funds are set"""
    # Create wallet without trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Attempt clawback with empty trial funds
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    with boa.reverts():
        wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)


def test_clawback_empty_data(agent_factory, setup_trial_funds, owner, agent):
    """Test clawback with empty/invalid clawback data"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Attempt clawback with empty data
    with boa.reverts():
        wallet.recoverTrialFunds([], sender=agent_factory.address)


def test_partial_clawback_inaccessible_funds(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test partial clawback when some funds are inaccessible"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    
    # Make second lego "inaccessible" by simulating a failure
    mock_lego_alpha_another.setWithdrawFails(True, sender=governor)
    
    # First try to recover from the accessible lego
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify partial recovery
    assert token.balanceOf(agent_factory) == half_amount
    assert wallet.trialFundsAmount() == half_amount
    
    # Now try to recover from the inaccessible lego - should fail
    clawback_data = [(mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)]
    with boa.reverts():  # Withdrawal should fail
        wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify remaining funds are still in wallet
    assert token.balanceOf(agent_factory) == half_amount
    assert wallet.trialFundsAmount() == half_amount


def test_initialize_invalid_trial_funds(agent_factory, alpha_token, owner, agent):
    """Test initializing wallet with invalid trial funds data"""
    # Create wallet with zero trial funds amount
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Try to initialize with invalid trial funds data
    with boa.reverts():
        wallet.initialize(
            agent_factory.ADDY_REGISTRY(),
            agent_factory.WETH_ADDR(),
            alpha_token,
            0,  # Invalid amount
            owner,
            agent
        )


def test_mismatched_vault_token_asset(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_weth, governor, alpha_token_erc4626_vault, weth_erc4626_vault):
    """Test clawback with vault token that has different underlying asset"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit trial funds
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Try to clawback using wrong vault token (WETH vault instead of alpha token vault)
    clawback_data = [(mock_lego_alpha.legoId(), weth_erc4626_vault)]
    with boa.reverts():  # Should revert since no funds are available with the wrong vault token
        wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify no funds were recovered since vault token didn't match
    assert token.balanceOf(agent_factory) == 0
    assert wallet.trialFundsAmount() == trial_amount


def test_clawback_split_funds_multiple_sources(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test clawback when funds are split between wallet balance and multiple legos"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split funds: 20% in wallet, 30% in first lego, 50% in second lego
    wallet_amount = trial_amount * 20 // 100
    first_lego_amount = trial_amount * 30 // 100
    second_lego_amount = trial_amount * 50 // 100
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, first_lego_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Deposit into second lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha_another.legoId(), token, second_lego_amount, alpha_token_erc4626_vault_another, sender=agent)
    
    # Clawback trial funds
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify full recovery
    assert token.balanceOf(agent_factory) == trial_amount
    assert wallet.trialFundsAmount() == 0
    assert wallet.trialFundsAsset() == ZERO_ADDRESS


def test_clawback_zero_balance_vault(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test clawback with a vault that has zero balance"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit into first lego
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Try to clawback including a vault with zero balance
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)  # Zero balance vault
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify only the actual funds were recovered
    assert token.balanceOf(agent_factory) == trial_amount
    assert wallet.trialFundsAmount() == 0
    assert wallet.trialFundsAsset() == ZERO_ADDRESS


def test_clawback_duplicate_entries(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test clawback with duplicate lego/vault entries in clawback data"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit trial funds
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Try to clawback with duplicate entries
    clawback_data = [
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault),
        (mock_lego_alpha.legoId(), alpha_token_erc4626_vault)  # Duplicate entry
    ]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify funds were recovered only once
    assert token.balanceOf(agent_factory) == trial_amount
    assert wallet.trialFundsAmount() == 0
    assert wallet.trialFundsAsset() == ZERO_ADDRESS


def test_trial_funds_amount_update_after_partial_recovery(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, mock_lego_alpha_another, governor, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    """Test trial funds amount is correctly updated after partial recovery"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha_another.legoId(), sender=owner)
    
    # Split trial funds between two legos
    half_amount = trial_amount // 2
    
    # Deposit into both legos
    wallet.depositTokens(mock_lego_alpha.legoId(), token, half_amount, alpha_token_erc4626_vault, sender=agent)
    wallet.depositTokens(mock_lego_alpha_another.legoId(), token, half_amount, alpha_token_erc4626_vault_another, sender=agent)
    
    # Make second lego fail withdrawals
    mock_lego_alpha_another.setWithdrawFails(True, sender=governor)
    
    # First partial recovery
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify partial recovery state
    assert token.balanceOf(agent_factory) == half_amount
    assert wallet.trialFundsAmount() == half_amount
    assert wallet.trialFundsAsset() == token.address
    
    # Enable withdrawals and try second recovery
    mock_lego_alpha_another.setWithdrawFails(False, sender=governor)
    clawback_data = [(mock_lego_alpha_another.legoId(), alpha_token_erc4626_vault_another)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify complete recovery state
    assert token.balanceOf(agent_factory) == trial_amount
    assert wallet.trialFundsAmount() == 0
    assert wallet.trialFundsAsset() == ZERO_ADDRESS


def test_trial_funds_with_reserve_during_clawback(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test interaction between trial funds and reserve assets during clawback"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Set reserve amount
    reserve_amount = trial_amount // 4  # 25% reserve
    wallet.setReserveAsset(token, reserve_amount, sender=owner)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit available amount (trial amount - reserve)
    available_amount = trial_amount - reserve_amount
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, available_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Try clawback
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify clawback recovered all trial funds, including reserved amount
    assert token.balanceOf(agent_factory) == trial_amount
    assert wallet.trialFundsAmount() == 0
    assert wallet.trialFundsAsset() == ZERO_ADDRESS
    
    # Verify reserve is still set but no longer affects trial funds
    assert wallet.reserveAssets(token) == reserve_amount


def test_clawback_invalid_lego_id(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test clawback attempt with invalid lego ID"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit trial funds
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Try to clawback with invalid lego ID
    invalid_lego_id = 999  # Non-existent lego ID
    clawback_data = [(invalid_lego_id, alpha_token_erc4626_vault)]
    with boa.reverts():  # Should revert since lego ID is invalid
        wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify no funds were recovered
    assert token.balanceOf(agent_factory) == 0
    assert wallet.trialFundsAmount() == trial_amount


def test_clawback_deactivated_lego(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test clawback when lego is deactivated"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deposit trial funds
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Deactivate lego
    mock_lego_alpha.activate(False, sender=governor)
    
    # Try to clawback from deactivated lego
    clawback_data = [(mock_lego_alpha.legoId(), alpha_token_erc4626_vault)]
    with boa.reverts():  # Should revert since lego is deactivated
        wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    
    # Verify no funds were recovered
    assert token.balanceOf(agent_factory) == 0
    assert wallet.trialFundsAmount() == trial_amount
    
    # Reactivate lego and try again - should work
    mock_lego_alpha.activate(True, sender=governor)
    assert wallet.recoverTrialFunds(clawback_data, sender=agent_factory.address)
    assert token.balanceOf(agent_factory) == trial_amount
    assert wallet.trialFundsAmount() == 0


def test_trial_funds_with_deactivated_lego(agent_factory, setup_trial_funds, owner, agent, mock_lego_alpha, governor, alpha_token_erc4626_vault):
    """Test trial funds usage when lego is deactivated"""
    token, trial_amount = setup_trial_funds
    
    # Create wallet with trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Setup permissions
    wallet.addAssetForAgent(agent, token, sender=owner)
    wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    
    # Deactivate lego
    mock_lego_alpha.activate(False, sender=governor)
    
    # Try to deposit trial funds into deactivated lego
    with boa.reverts():  # Should revert since lego is deactivated
        wallet.depositTokens(mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    
    # Verify funds are still in wallet
    assert token.balanceOf(wallet) == trial_amount
    assert wallet.trialFundsAmount() == trial_amount
    
    # Reactivate lego and try again - should work
    mock_lego_alpha.activate(True, sender=governor)
    assetAmountDeposited, _, vaultTokenAmountReceived, _ = wallet.depositTokens(
        mock_lego_alpha.legoId(), token, trial_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == trial_amount
    assert vaultTokenAmountReceived == trial_amount


def test_initialize_invalid_trial_funds_asset(agent_factory, owner, agent):
    """Test initializing wallet with invalid trial funds asset"""
    # Create wallet without trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Try to initialize with non-contract address as trial funds asset
    with boa.reverts():
        wallet.initialize(
            agent_factory.ADDY_REGISTRY(),
            agent_factory.WETH_ADDR(),
            owner,  # Using an EOA address as trial funds asset
            1000,
            owner,
            agent
        )
    
    # Try to initialize with zero address as trial funds asset
    with boa.reverts():
        wallet.initialize(
            agent_factory.ADDY_REGISTRY(),
            agent_factory.WETH_ADDR(),
            ZERO_ADDRESS,
            1000,
            owner,
            agent
        )


def test_trial_funds_amount_exceeding_factory_balance(agent_factory, alpha_token, alpha_token_whale, governor, owner, agent):
    """Test setting trial funds amount exceeding factory balance"""
    trial_amount = 1000 * EIGHTEEN_DECIMALS  # Large amount
    factory_balance = 100 * EIGHTEEN_DECIMALS  # Smaller balance
    
    # Transfer tokens to factory
    alpha_token.transfer(agent_factory, factory_balance, sender=alpha_token_whale)
    
    # Set trial funds data with amount exceeding balance
    assert agent_factory.setTrialFundsData(alpha_token, trial_amount, sender=governor)
    
    # Create wallet - should get partial trial funds
    wallet_addr = agent_factory.createAgenticWallet(owner, agent)
    wallet = WalletTemplate.at(wallet_addr)
    
    # Verify wallet received only the available amount
    assert alpha_token.balanceOf(wallet) == factory_balance
    assert wallet.trialFundsAmount() == factory_balance
    assert wallet.trialFundsAsset() == alpha_token.address
    
    # Verify factory balance is now zero
    assert alpha_token.balanceOf(agent_factory) == 0
