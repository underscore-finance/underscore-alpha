import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
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

    assert price_sheets.setProtocolTxPriceSheet(
        10_00, # yield fee (10.00%)
        0, # swap fee (1.00%)
        0, # claim fee (10.00%)
        sender=governor
    )

    return price_sheets


#########
# Tests #
#########


def test_basic_yield_tracking(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault, price_sheets):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # test yield tracking
    assert ai_wallet.isVaultToken(vaultToken)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited

    # send more to vault
    alpha_token.transfer(alpha_token_erc4626_vault, 10 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # test underlying amount
    underlying_amount = mock_lego_alpha.getUnderlyingAmount(vaultToken, vaultTokenAmountReceived)
    assert underlying_amount == 110 * EIGHTEEN_DECIMALS

    # withdraw
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    log = filter_logs(ai_wallet, "UserWalletTransactionFeePaid")[0]

    # test yield tracking
    assert ai_wallet.vaultTokenAmounts(vaultToken) == 0
    assert ai_wallet.depositedAmounts(vaultToken) == 0

    assert assetAmountReceived == 109 * EIGHTEEN_DECIMALS

    assert log.asset == alpha_token.address
    assert log.protocolRecipient == price_sheets.protocolRecipient()
    assert log.protocolAmount == 1 * EIGHTEEN_DECIMALS # 10.00% of 10 * EIGHTEEN_DECIMALS
    assert log.ambassadorRecipient == ZERO_ADDRESS
    assert log.ambassadorAmount == 0
    assert log.fee == 10_00 # 10.00%


def test_yield_tracking_on_exit(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # test exit with amount less than untracked balance
    untracked_amount = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, untracked_amount, sender=alpha_token_whale)
    ai_wallet.transferFunds(owner, untracked_amount, alpha_token, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived  # Should not change

    # test exit with amount greater than untracked balance
    exit_amount = vaultTokenAmountReceived // 2
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, exit_amount, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived - vaultTokenAmountBurned
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited - assetAmountReceived


def test_yield_tracking_on_entry(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # test entry with vault token
    entry_amount = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, entry_amount, sender=alpha_token_whale)
    ai_wallet.depositTokens(lego_id, alpha_token, alpha_token_erc4626_vault, entry_amount, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) > vaultTokenAmountReceived
    assert ai_wallet.depositedAmounts(vaultToken) > assetAmountDeposited

    # test entry with non-vault token
    non_vault_token = alpha_token
    assert not ai_wallet.isVaultToken(non_vault_token)
    alpha_token.transfer(ai_wallet, entry_amount, sender=alpha_token_whale)
    ai_wallet.transferFunds(owner, entry_amount, non_vault_token, sender=owner)
    assert not ai_wallet.isVaultToken(non_vault_token)  # Should remain false


def test_yield_tracking_on_withdrawal(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # generate yield
    yield_amount = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alpha_token_erc4626_vault, yield_amount, sender=alpha_token_whale)

    # test partial withdrawal
    withdraw_amount = vaultTokenAmountReceived // 2
    assetAmountReceived_one, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, vaultToken, withdraw_amount, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived - vaultTokenAmountBurned
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited - assetAmountReceived_one

    # test full withdrawal with profit
    assetAmountReceived_two, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, vaultToken, MAX_UINT256, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == 0
    assert ai_wallet.depositedAmounts(vaultToken) == 0
    assert assetAmountReceived_one + assetAmountReceived_two > assetAmountDeposited  # Should have profit


def test_yield_tracking_exact_amounts(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # test withdrawal with exact tracked amount
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, vaultTokenAmountReceived, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == 0
    assert ai_wallet.depositedAmounts(vaultToken) == 0
    assert vaultTokenAmountBurned == vaultTokenAmountReceived


def test_yield_tracking_invalid_lego(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # test entry with invalid lego (should update tracking)
    entry_amount = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, entry_amount, sender=alpha_token_whale)
    ai_wallet.transferFunds(owner, entry_amount, vaultToken, sender=owner)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived - entry_amount
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited - (assetAmountDeposited * entry_amount // vaultTokenAmountReceived)


def test_extra_vault_tokens(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # extra vault tokens
    alpha_token.approve(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    extra_amount = alpha_token_erc4626_vault.deposit(50 * EIGHTEEN_DECIMALS, ai_wallet.address, sender=alpha_token_whale)

    # test yield tracking
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited

    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == vaultTokenAmountReceived + extra_amount


def test_extra_vault_tokens_withdrawal_within_tracked_amount(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # extra vault tokens
    alpha_token.approve(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    extra_amount = alpha_token_erc4626_vault.deposit(50 * EIGHTEEN_DECIMALS, ai_wallet.address, sender=alpha_token_whale)

    # test withdrawal with extra tokens
    withdraw_amount = vaultTokenAmountReceived // 2
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, withdraw_amount, sender=owner)

    # verify tracking is correct
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived  # Should not change since actual balance >= tracked balance
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited  # Should not change since actual balance >= tracked balance
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == vaultTokenAmountReceived - vaultTokenAmountBurned + extra_amount


def test_extra_vault_tokens_withdrawal_outside_tracked_amount(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # extra vault tokens
    alpha_token.approve(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    extra_amount = alpha_token_erc4626_vault.deposit(50 * EIGHTEEN_DECIMALS, ai_wallet.address, sender=alpha_token_whale)

    # test withdrawal with extra tokens
    withdraw_amount = extra_amount + (vaultTokenAmountReceived // 2)
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, withdraw_amount, sender=owner)

    # verify tracking is correct
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived // 2  # Should reduce by half since actual balance < tracked balance
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited // 2  # Should reduce proportionally
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == vaultTokenAmountReceived // 2


def test_extra_vault_tokens_transfer(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # extra vault tokens
    alpha_token.approve(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    extra_amount = alpha_token_erc4626_vault.deposit(50 * EIGHTEEN_DECIMALS, ai_wallet.address, sender=alpha_token_whale)

    # test transferring extra tokens out
    transfer_amount = extra_amount // 2
    ai_wallet.transferFunds(owner, transfer_amount, vaultToken, sender=owner)

    # verify tracking is correct
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == vaultTokenAmountReceived + extra_amount - transfer_amount


def test_extra_vault_tokens_mixed_operations(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # extra vault tokens
    alpha_token.approve(alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    extra_amount = alpha_token_erc4626_vault.deposit(50 * EIGHTEEN_DECIMALS, ai_wallet.address, sender=alpha_token_whale)

    # test mixed operations
    # 1. Withdraw half of tracked tokens
    withdraw_amount = vaultTokenAmountReceived // 2
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, withdraw_amount, sender=owner)

    # Verify tracking remains unchanged because we have enough total tokens
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived  # Should not change since actual balance >= tracked balance
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited  # Should not change since actual balance >= tracked balance

    # 2. Transfer some extra tokens
    transfer_amount = extra_amount // 2
    ai_wallet.transferFunds(owner, transfer_amount, vaultToken, sender=owner)

    # Verify tracking is reduced because _updateYieldTrackingOnExit reduces tracked amount
    # when transferring more than untracked balance
    assert ai_wallet.vaultTokenAmounts(vaultToken) == vaultTokenAmountReceived - transfer_amount  # Should be reduced by transfer amount
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited - (assetAmountDeposited * transfer_amount // vaultTokenAmountReceived)  # Should be reduced proportionally

    # 3. Deposit more tokens
    new_deposit = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, new_deposit, sender=alpha_token_whale)
    new_assetAmountDeposited, same_vaultToken, new_vaultTokenAmountReceived, new_usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)

    # verify final state
    assert vaultToken == same_vaultToken  # Same vault should return same token
    
    # After all operations:
    # - Original tracked amount (100) was reduced to 75 by transfer
    # - New deposit (75) adds to tracking
    # Total tracked amount = Reduced original (75) + New deposit (75) = 150
    # Total actual balance = Remaining from first deposit (50) + Remaining extra (25) + New deposit (75) = 150
    assert ai_wallet.vaultTokenAmounts(vaultToken) == (vaultTokenAmountReceived - transfer_amount) + new_vaultTokenAmountReceived  # Reduced original (75) + new deposit (75)
    assert ai_wallet.depositedAmounts(vaultToken) == (assetAmountDeposited - (assetAmountDeposited * transfer_amount // vaultTokenAmountReceived)) + new_assetAmountDeposited  # Reduced original + new deposit
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == (
        vaultTokenAmountReceived - vaultTokenAmountBurned +  # remaining from first deposit (50)
        extra_amount - transfer_amount +  # remaining extra tokens (25)
        new_vaultTokenAmountReceived  # new deposit (75)
    )


def test_yield_tracking_edge_cases(mock_lego_alpha, alpha_token, alpha_token_whale, ai_wallet, owner, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 100 * EIGHTEEN_DECIMALS

    # transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # Test 1: Deposit to a vault token that was previously not recognized as a vault token
    # First, ensure the token is not recognized as a vault token
    assert not ai_wallet.isVaultToken(alpha_token_erc4626_vault)
    
    # Deposit and verify it's now recognized as a vault token
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)
    initial_tracked_amount = vaultTokenAmountReceived
    assert ai_wallet.isVaultToken(vaultToken)
    assert ai_wallet.vaultTokenAmounts(vaultToken) == initial_tracked_amount
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited

    # Test 2: Additional deposit should increase tracked amount
    extra_amount = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, extra_amount, sender=alpha_token_whale)
    extra_asset_deposited, _, extra_vault_tokens, _ = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, extra_amount, sender=owner)
    
    # Verify both deposits are tracked
    assert ai_wallet.vaultTokenAmounts(vaultToken) == initial_tracked_amount + extra_vault_tokens
    assert ai_wallet.depositedAmounts(vaultToken) == assetAmountDeposited + extra_asset_deposited
    
    # Test 3: Withdraw part of the tracked amount
    withdraw_amount = initial_tracked_amount // 2  # Withdraw half of initial deposit
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, vaultToken, withdraw_amount, sender=owner)
    
    # Verify tracking is reduced proportionally
    expected_remaining_tracked = initial_tracked_amount + extra_vault_tokens - withdraw_amount
    assert ai_wallet.vaultTokenAmounts(vaultToken) == expected_remaining_tracked
    
    # Test 4: Enter with a vault token that has no associated lego
    mock_vault_token = alpha_token_erc4626_vault  # Using existing vault token for simplicity
    previous_tracked_amount = ai_wallet.vaultTokenAmounts(mock_vault_token)
    
    # Try to enter with the vault token via transfer
    ai_wallet.transferFunds(owner, 25 * EIGHTEEN_DECIMALS, mock_vault_token, sender=owner)
    
    # Verify tracking is updated since it's already recognized as a vault token
    assert ai_wallet.vaultTokenAmounts(mock_vault_token) == previous_tracked_amount - 25 * EIGHTEEN_DECIMALS
    
    # Test 5: Withdraw with very small amount (close to zero)
    # First, deposit some tokens
    alpha_token.transfer(ai_wallet, 25 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)
    
    # Try to withdraw with very small amount
    previous_tracked = ai_wallet.vaultTokenAmounts(vaultToken)
    small_amount = 1  # Smallest possible amount
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, vaultToken, small_amount, sender=owner)
    
    # Verify tracking is reduced by the small amount
    assert ai_wallet.vaultTokenAmounts(vaultToken) == previous_tracked - small_amount