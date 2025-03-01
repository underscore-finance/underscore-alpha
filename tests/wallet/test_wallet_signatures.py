import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


#########
# Tests #
#########


def test_deposit_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signDeposit):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # signature
    signature = signDeposit(special_agent, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, MAX_UINT256)

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = special_agent.depositTokens(
        special_ai_wallet, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, signature, sender=broadcaster)

    # deposit
    log = filter_logs(special_agent, "UserWalletDeposit")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert assetAmountDeposited == deposit_amount
    assert alpha_token.balanceOf(special_ai_wallet) == 0
    assert alpha_token_erc4626_vault.balanceOf(special_ai_wallet) == vaultTokenAmountReceived


def test_withdraw_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signWithdrawal):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = special_ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=special_agent.address)

    # signature
    signature = signWithdrawal(special_agent, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, MAX_UINT256)

    # withdrawal
    assetAmountReceived, vaultTokenAmountBurned, usdValue = special_agent.withdrawTokens(
        special_ai_wallet, lego_id, alpha_token, alpha_token_erc4626_vault.address, MAX_UINT256, signature, sender=broadcaster)

    # withdrawal
    log = filter_logs(special_agent, "UserWalletWithdrawal")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert alpha_token.balanceOf(special_ai_wallet) == assetAmountDeposited == assetAmountReceived
    assert alpha_token_erc4626_vault.balanceOf(special_ai_wallet) == 0


def test_rebalance_with_signature(special_ai_wallet, owner, broadcaster, special_agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale, signRebalance):
    # setup
    lego_id = mock_lego_alpha.legoId()
    alt_lego_id = mock_lego_alpha_another.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # deposit
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived, usdValue = special_ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=owner)

    # signature
    signature = signRebalance(special_agent, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, alt_lego_id, alpha_token_erc4626_vault_another.address, MAX_UINT256)

    # rebalance
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = special_agent.rebalance(
        special_ai_wallet, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, alt_lego_id, alpha_token_erc4626_vault_another.address, MAX_UINT256, signature, sender=broadcaster)
    
    # rebalance
    log = filter_logs(special_agent, "UserWalletWithdrawal")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    log = filter_logs(special_agent, "UserWalletDeposit")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert alpha_token_erc4626_vault.balanceOf(special_ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(special_ai_wallet) == vaultTokenAmountReceived


def test_swap_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signSwap, bravo_token, bravo_token_whale):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # put amount for swap
    bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)

    # signature
    signature = signSwap(special_agent, lego_id, alpha_token.address, bravo_token.address, MAX_UINT256, 0, ZERO_ADDRESS)

    # swap
    actualSwapAmount, toAmount, usdValue = special_agent.swapTokens(
        special_ai_wallet, lego_id, alpha_token.address, bravo_token.address, MAX_UINT256, 0, ZERO_ADDRESS, signature, sender=broadcaster)
    
    # swap
    log = filter_logs(special_agent, "UserWalletSwap")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert actualSwapAmount == deposit_amount
    assert alpha_token.balanceOf(special_ai_wallet) == 0
    assert bravo_token.balanceOf(special_ai_wallet) == toAmount == deposit_amount


def test_transfer_with_signature(special_ai_wallet, special_ai_wallet_config, sally, special_agent, owner, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signTransfer):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # setup whitelist
    assert special_ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

    # signature
    signature = signTransfer(special_agent, sally, MAX_UINT256, alpha_token.address)

    # transfer
    amount, usdValue = special_agent.transferFunds(
        special_ai_wallet, sally, MAX_UINT256, alpha_token.address, signature, sender=broadcaster)
    
    # transfer
    log = filter_logs(special_agent, "UserWalletFundsTransferred")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert amount == deposit_amount
    assert alpha_token.balanceOf(special_ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == deposit_amount


def test_signature_expiration_and_reuse(special_agent, special_ai_wallet, special_ai_wallet_config, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signDeposit):
    """Test signature expiration and reuse prevention"""
    # Setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # Test expired signature
    expired_signature = signDeposit(
        special_agent, 
        lego_id, 
        alpha_token.address, 
        alpha_token_erc4626_vault.address,
        MAX_UINT256, 
        1,  # Set expiration to past block
    )

    with boa.reverts("signature expired"):
        special_agent.depositTokens(
            special_ai_wallet,
            lego_id, 
            alpha_token, 
            alpha_token_erc4626_vault, 
            MAX_UINT256, 
            expired_signature, 
            sender=broadcaster
        )

    # Test signature reuse
    valid_signature = signDeposit(
        special_agent, 
        lego_id, 
        alpha_token.address, 
        alpha_token_erc4626_vault.address,
        MAX_UINT256, 
    )

    # First use should succeed
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue =  special_agent.depositTokens(
        special_ai_wallet,
        lego_id, 
        alpha_token, 
        alpha_token_erc4626_vault, 
        MAX_UINT256, 
        valid_signature, 
        sender=broadcaster
    )
    assert assetAmountDeposited == deposit_amount

    # Second use should fail
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)
    with boa.reverts("signature already used"):
        special_agent.depositTokens(
            special_ai_wallet,
            lego_id, 
            alpha_token, 
            alpha_token_erc4626_vault, 
            MAX_UINT256, 
            valid_signature, 
            sender=broadcaster
        )


def test_signature_with_reserve_assets(special_ai_wallet, special_agent, owner, special_ai_wallet_config, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signDeposit, signWithdrawal, signTransfer, sally):
    """Test signature operations with reserve assets"""
    # Setup
    lego_id = mock_lego_alpha.legoId()
    amount = 1_000 * EIGHTEEN_DECIMALS
    reserve_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, amount, sender=alpha_token_whale)

    # Set reserve amount
    assert special_ai_wallet_config.setReserveAsset(alpha_token, reserve_amount, sender=owner)
    assert special_ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

    # Test deposit with signature (should work with reserve)
    signature = signDeposit(special_agent, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, MAX_UINT256)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = special_agent.depositTokens(
        special_ai_wallet, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, signature, sender=broadcaster)
    assert assetAmountDeposited == amount - reserve_amount

    # Test withdrawal with signature (should respect reserve)
    signature = signWithdrawal(special_agent, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, MAX_UINT256)
    assetAmountReceived, vaultTokenAmountBurned, usdValue = special_agent.withdrawTokens(
        special_ai_wallet, lego_id, alpha_token, alpha_token_erc4626_vault.address, MAX_UINT256, signature, sender=broadcaster)
    assert assetAmountReceived == assetAmountDeposited

    # Test transfer with signature (should respect reserve)
    signature = signTransfer(special_agent, sally, MAX_UINT256, alpha_token.address)
    special_agent.transferFunds(special_ai_wallet, sally, MAX_UINT256, alpha_token, signature, sender=broadcaster)
    assert alpha_token.balanceOf(special_ai_wallet) == reserve_amount

    # Test transfer, only has reserve amount
    signature = signTransfer(special_agent, sally, amount, alpha_token.address)
    with boa.reverts("insufficient balance after reserve"):
        special_agent.transferFunds(special_ai_wallet, sally, amount, alpha_token, signature, sender=broadcaster)
