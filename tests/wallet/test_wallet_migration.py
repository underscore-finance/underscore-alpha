import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, MAX_MIGRATION_ASSETS, MAX_MIGRATION_WHITELIST
from contracts.core.templates import UserWalletTemplate, UserWalletConfigTemplate


@pytest.fixture(scope="module")
def new_wallet(agent_factory, owner, bob_agent):
    """Create a new wallet to migrate to"""
    w = agent_factory.createUserWallet(owner, bob_agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return UserWalletTemplate.at(w)


@pytest.fixture(scope="module")
def new_wallet_config(new_wallet):
    """Get config for new wallet"""
    return UserWalletConfigTemplate.at(new_wallet.walletConfig())


@pytest.fixture(scope="module")
def other_wallet(agent_factory, owner, bob_agent, sally):
    """Create another wallet with different owner"""
    w = agent_factory.createUserWallet(sally, bob_agent, sender=sally)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return UserWalletTemplate.at(w)


def test_basic_migration(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, alpha_token, alpha_token_whale):
    """Test basic migration with ERC20 tokens"""
    # Setup initial state
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [alpha_token], [], sender=owner)
    
    # Verify state changes
    assert ai_wallet_config.didMigrateOut()
    assert new_wallet_config.didMigrateIn()
    
    # Verify balances
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(new_wallet) == amount


def test_migration_with_eth(ai_wallet, ai_wallet_config, new_wallet, owner):
    """Test migration with ETH balance"""
    # Setup ETH balance
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, eth_amount)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)
    
    # Verify ETH balances
    assert boa.env.get_balance(ai_wallet.address) == 0
    assert boa.env.get_balance(new_wallet.address) == eth_amount


def test_migration_with_whitelist(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, sally):
    """Test migration with whitelist addresses"""
    # Setup whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    delay = ai_wallet_config.ownershipChangeDelay()
    boa.env.time_travel(blocks=delay)
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    assert ai_wallet_config.isRecipientAllowed(sally)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [], [sally], sender=owner)
    
    # Verify whitelist state
    assert new_wallet_config.isRecipientAllowed(sally)


def test_migration_with_vault_tokens(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, mock_lego_alpha, alpha_token, alpha_token_whale, alpha_token_erc4626_vault):
    """Test migration with vault tokens and yield tracking"""
    # Setup initial deposit
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Deposit into vault
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _ = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount, sender=owner)
    
    # Record initial tracking state
    orig_vault_token_amount = ai_wallet_config.vaultTokenAmounts(vaultToken)
    orig_deposited_amount = ai_wallet_config.depositedAmounts(vaultToken)
    
    # Generate some yield
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [vaultToken], [], sender=owner)
    
    # Verify vault token state and yield tracking
    assert alpha_token_erc4626_vault.balanceOf(new_wallet) == vaultTokenAmountReceived
    assert new_wallet_config.isVaultToken(vaultToken)
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == orig_vault_token_amount
    assert new_wallet_config.depositedAmounts(vaultToken) == orig_deposited_amount


def test_migration_with_trial_funds(ai_wallet, ai_wallet_config, new_wallet, owner, agent_factory):
    """Test migration with trial funds"""
    # Verify trial funds must be recovered first
    if ai_wallet.trialFundsAsset() != ZERO_ADDRESS:
        with boa.reverts("must recover trial funds"):
            ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)
        
        # Recover trial funds
        assert ai_wallet.recoverTrialFunds(sender=agent_factory.address)
    
    # Now migration should succeed
    assert ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)


def test_migration_security(ai_wallet, ai_wallet_config, new_wallet, owner, agent, sally):
    """Test migration security and permissions"""
    # Only owner can start migration
    with boa.reverts("no perms"):
        ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=agent)
    
    # Cannot migrate with pending ownership change
    ai_wallet_config.changeOwnership(sally, sender=owner)
    with boa.reverts("this wallet has pending owner change"):
        ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)
    
    # Cancel ownership change
    ai_wallet_config.cancelOwnershipChange(sender=owner)
    
    # Migration should now succeed
    assert ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)


def test_migration_with_existing_state(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, sally, alpha_token, alpha_token_whale):
    """Test migration when destination wallet has existing state"""
    # Setup existing state in new wallet
    amount = 500 * EIGHTEEN_DECIMALS
    alpha_token.transfer(new_wallet, amount, sender=alpha_token_whale)
    
    # Add existing whitelist in new wallet
    new_wallet_config.addWhitelistAddr(sally, sender=owner)
    delay = new_wallet_config.ownershipChangeDelay()
    boa.env.time_travel(blocks=delay)
    new_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Setup state in old wallet
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [alpha_token], [], sender=owner)
    
    # Verify combined state
    assert alpha_token.balanceOf(new_wallet) == amount * 2
    assert new_wallet_config.isRecipientAllowed(sally)


def test_migration_edge_cases(ai_wallet, ai_wallet_config, new_wallet, owner, other_wallet):
    """Test migration edge cases"""
    # Migration with empty arrays should succeed
    assert ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)
    
    # Cannot migrate twice
    with boa.reverts("already migrated out"):
        ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)
    
    # Cannot migrate to non-Underscore wallet
    with boa.reverts():
        ai_wallet_config.startMigrationOut(owner, [], [], sender=owner)
    
    # Cannot migrate to wallet with different owner
    with boa.reverts():
        ai_wallet_config.startMigrationOut(other_wallet, [], [], sender=owner)


def test_migration_complex_scenario(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, mock_lego_alpha, alpha_token, alpha_token_whale, alpha_token_erc4626_vault, sally, bob):
    """Test complex migration scenario with multiple assets and states"""
    # Setup ETH balance
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, eth_amount)
    
    # Setup ERC20 balance
    token_amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, token_amount, sender=alpha_token_whale)
    
    # Setup vault tokens with yield
    vault_amount = 500 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, vault_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _ = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, vault_amount, sender=owner)
    
    # Record initial tracking state
    orig_vault_token_amount = ai_wallet_config.vaultTokenAmounts(vaultToken)
    orig_deposited_amount = ai_wallet_config.depositedAmounts(vaultToken)
    
    # Generate yield before migration
    alpha_token.transfer(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Setup whitelist
    for addr in [sally, bob]:
        ai_wallet_config.addWhitelistAddr(addr, sender=owner)
        delay = ai_wallet_config.ownershipChangeDelay()
        boa.env.time_travel(blocks=delay)
        ai_wallet_config.confirmWhitelistAddr(addr, sender=owner)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [alpha_token, vaultToken], [sally, bob], sender=owner)
    
    # Verify complete state transfer
    assert boa.env.get_balance(new_wallet.address) == eth_amount
    assert alpha_token.balanceOf(new_wallet) == token_amount
    assert alpha_token_erc4626_vault.balanceOf(new_wallet) == vaultTokenAmountReceived
    assert new_wallet_config.isVaultToken(vaultToken)
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == orig_vault_token_amount
    assert new_wallet_config.depositedAmounts(vaultToken) == orig_deposited_amount
    for addr in [sally, bob]:
        assert new_wallet_config.isRecipientAllowed(addr)


def test_migration_vault_token_yield_tracking(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, mock_lego_alpha, alpha_token, alpha_token_whale, alpha_token_erc4626_vault):
    """Test migration preserves vault token yield tracking"""
    # Initial deposit
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _ = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount, sender=owner)
    
    # Record initial tracking state
    orig_vault_token_amount = ai_wallet_config.vaultTokenAmounts(vaultToken)
    orig_deposited_amount = ai_wallet_config.depositedAmounts(vaultToken)
    
    # Generate yield before migration
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Migrate
    assert ai_wallet_config.startMigrationOut(new_wallet, [vaultToken], [], sender=owner)
    
    # Verify yield tracking state is preserved
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == orig_vault_token_amount
    assert new_wallet_config.depositedAmounts(vaultToken) == orig_deposited_amount
    
    # Generate more yield after migration
    alpha_token.transfer(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Withdraw from new wallet and verify yield tracking still works
    assetAmountReceived, vaultTokenAmountBurned, _ = new_wallet.withdrawTokens(
        mock_lego_alpha.legoId(), alpha_token, vaultToken, MAX_UINT256, sender=owner)
    
    # Should receive original amount plus all yield
    assert assetAmountReceived > amount
    assert vaultTokenAmountBurned == vaultTokenAmountReceived
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == 0
    assert new_wallet_config.depositedAmounts(vaultToken) == 0


def test_migration_old_wallet_yield_tracking(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, mock_lego_alpha, alpha_token, alpha_token_whale, alpha_token_erc4626_vault):
    """Test that old wallet's yield tracking state is properly updated after migration"""
    # Initial deposit
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _ = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount, sender=owner)
    
    # Record initial tracking state
    orig_vault_token_amount = ai_wallet_config.vaultTokenAmounts(vaultToken)
    orig_deposited_amount = ai_wallet_config.depositedAmounts(vaultToken)
    assert orig_vault_token_amount > 0
    assert orig_deposited_amount > 0
    
    # Generate yield before migration
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [vaultToken], [], sender=owner)
    
    # Verify old wallet's yield tracking state is zeroed out
    assert ai_wallet_config.vaultTokenAmounts(vaultToken) == 0
    assert ai_wallet_config.depositedAmounts(vaultToken) == 0
    
    # Verify new wallet got the original amounts
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == orig_vault_token_amount
    assert new_wallet_config.depositedAmounts(vaultToken) == orig_deposited_amount
    
    # Verify balances
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault.balanceOf(new_wallet) == vaultTokenAmountReceived


def test_migration_revert_cases(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, bob_agent, sally, alpha_token, alpha_token_whale, agent_factory):
    """Test all possible revert conditions for migration"""
    # Setup initial state with some assets
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Test 1: Cannot migrate to non-Underscore wallet
    with boa.reverts():  # Will revert when trying to call walletConfig() on non-contract
        ai_wallet_config.startMigrationOut(sally, sender=owner)
    
    # Test 2: Cannot migrate to wallet with different owner
    other_wallet = agent_factory.createUserWallet(sally, bob_agent, sender=sally)
    with boa.reverts():  # Will revert when checking owner
        ai_wallet_config.startMigrationOut(other_wallet, sender=owner)
    
    # Test 3: Cannot migrate with pending owner change
    delay = ai_wallet_config.ownershipChangeDelay()
    ai_wallet_config.changeOwnership(sally, sender=owner)
    with boa.reverts():  # Will revert due to pending owner change
        ai_wallet_config.startMigrationOut(new_wallet, sender=owner)
    ai_wallet_config.cancelOwnershipChange(sender=owner)
    
    # Test 4: Cannot migrate when new wallet has pending owner change
    new_wallet_config.changeOwnership(sally, sender=owner)
    with boa.reverts():  # Will revert due to pending owner change
        ai_wallet_config.startMigrationOut(new_wallet, sender=owner)
    new_wallet_config.cancelOwnershipChange(sender=owner)
    
    # Test 5: Cannot migrate with invalid whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    boa.env.time_travel(blocks=delay)
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    with boa.reverts():  # Will revert due to whitelist mismatch
        ai_wallet_config.startMigrationOut(new_wallet, [sally], [], sender=owner)
    
    # Test 6: Cannot migrate twice
    assert ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)
    with boa.reverts():  # Will revert since already migrated
        ai_wallet_config.startMigrationOut(new_wallet, [], [], sender=owner)


def test_migration_vault_token_state(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault):
    """Test vault token state is perfectly preserved during migration"""
    # Setup complex vault token state
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Create deposit with yield
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _ = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount, sender=owner)
    
    # Generate some yield
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Record original state
    orig_vault_token_amount = ai_wallet_config.vaultTokenAmounts(vaultToken)
    orig_deposited_amount = ai_wallet_config.depositedAmounts(vaultToken)
    
    # Perform migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [vaultToken], [], sender=owner)
    
    # Verify state is preserved exactly
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == orig_vault_token_amount
    assert new_wallet_config.depositedAmounts(vaultToken) == orig_deposited_amount
    assert alpha_token_erc4626_vault.balanceOf(new_wallet) == vaultTokenAmountReceived


def test_migration_events(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, alpha_token, alpha_token_whale, sally):
    """Test all events are emitted correctly during migration"""
    # Setup initial state
    amount = 1000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Add whitelist address to both wallets
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    new_wallet_config.addWhitelistAddr(sally, sender=owner)
    delay = ai_wallet_config.ownershipChangeDelay()
    boa.env.time_travel(blocks=delay)
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    new_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Start migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [alpha_token], [sally], sender=owner)
    
    # Verify StartMigration event
    start_logs = filter_logs(ai_wallet_config, "UserWalletStartMigration")
    assert len(start_logs) == 1
    start_log = start_logs[0]
    assert start_log.newWallet == new_wallet.address
    assert start_log.numAssetsToMigrate == 1
    assert start_log.numWhitelistToMigrate == 1
    
    # Verify FinishMigration event
    finish_logs = filter_logs(ai_wallet_config, "UserWalletFinishMigration")
    assert len(finish_logs) == 1
    finish_log = finish_logs[0]
    assert finish_log.oldWallet == ai_wallet.address
    assert finish_log.numWhitelistMigrated == 1
    assert finish_log.numAssetsMigrated == 1
    assert finish_log.numVaultTokensMigrated == 0


def test_migration_state_consistency(ai_wallet, ai_wallet_config, new_wallet, new_wallet_config, owner, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, sally):
    """Test wallet state remains consistent through migration"""
    # Setup complex initial state
    amount = 1000 * EIGHTEEN_DECIMALS
    
    # 1. Setup ERC20 balance
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # 2. Setup vault token with yield
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, _ = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 2, sender=owner)
    alpha_token.transfer(alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # 3. Setup whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    delay = ai_wallet_config.ownershipChangeDelay()
    boa.env.time_travel(blocks=delay)
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Record all state before migration
    pre_erc20_balance = alpha_token.balanceOf(ai_wallet)
    pre_vault_balance = alpha_token_erc4626_vault.balanceOf(ai_wallet)
    pre_vault_token_amount = ai_wallet_config.vaultTokenAmounts(vaultToken)
    pre_deposited_amount = ai_wallet_config.depositedAmounts(vaultToken)
    pre_whitelist_state = ai_wallet_config.isRecipientAllowed(sally)
    
    # Perform migration
    assert ai_wallet_config.startMigrationOut(new_wallet, [alpha_token, vaultToken], [sally], sender=owner)
    
    # Verify complete state transfer
    assert alpha_token.balanceOf(new_wallet) == pre_erc20_balance
    assert alpha_token_erc4626_vault.balanceOf(new_wallet) == pre_vault_balance
    assert new_wallet_config.vaultTokenAmounts(vaultToken) == pre_vault_token_amount
    assert new_wallet_config.depositedAmounts(vaultToken) == pre_deposited_amount
    assert new_wallet_config.isRecipientAllowed(sally) == pre_whitelist_state
    
    # Verify old wallet state is cleared
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert ai_wallet_config.didMigrateOut()
