import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256


#########
# Tests #
#########


def test_deposit_with_signature(ai_wallet, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signDeposit):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)

    # signature
    signature = signDeposit(ai_wallet, lego_id, alpha_token.address, MAX_UINT256, alpha_token_erc4626_vault.address)

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokens(
        lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, signature, sender=broadcaster)
    
    # deposit
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.signer == agent
    assert log.broadcaster == broadcaster
    assert log.isSignerAgent

    assert assetAmountDeposited == deposit_amount
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == vaultTokenAmountReceived


def test_withdraw_with_signature(ai_wallet, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signWithdrawal):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokens(
        lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=agent)
    
    # signature
    signature = signWithdrawal(ai_wallet, lego_id, alpha_token.address, MAX_UINT256, alpha_token_erc4626_vault.address)

    # withdrawal
    assetAmountReceived, vaultTokenAmountBurned = ai_wallet.withdrawTokens(
        lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, signature, sender=broadcaster)

    # withdrawal
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.signer == agent
    assert log.broadcaster == broadcaster
    assert log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == assetAmountDeposited == assetAmountReceived
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0


def test_rebalance_with_signature(ai_wallet, owner, broadcaster, agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale, signRebalance):
    # setup
    lego_id = mock_lego_alpha.legoId()
    alt_lego_id = mock_lego_alpha_another.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)

    # deposit
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived = ai_wallet.depositTokens(
        lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)

    # signature
    signature = signRebalance(ai_wallet, lego_id, alt_lego_id, alpha_token.address, MAX_UINT256, alpha_token_erc4626_vault.address, alpha_token_erc4626_vault_another.address)

    # rebalance
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived = ai_wallet.rebalance(
        lego_id, alt_lego_id, alpha_token.address, MAX_UINT256, alpha_token_erc4626_vault.address, alpha_token_erc4626_vault_another.address, signature, sender=broadcaster)
    
    # rebalance
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.signer == agent
    assert log.broadcaster == broadcaster
    assert log.isSignerAgent

    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.signer == agent
    assert log.broadcaster == broadcaster
    assert log.isSignerAgent

    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(ai_wallet) == vaultTokenAmountReceived


def test_swap_with_signature(ai_wallet, agent, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signSwap, bravo_token, bravo_token_whale):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)

    # put amount for swap
    bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)

    # signature
    signature = signSwap(ai_wallet, lego_id, alpha_token.address, bravo_token.address, MAX_UINT256, 0)

    # swap
    actualSwapAmount, toAmount = ai_wallet.swapTokens(
        lego_id, alpha_token.address, bravo_token.address, MAX_UINT256, 0, signature, sender=broadcaster)
    
    # swap
    log = filter_logs(ai_wallet, "AgenticSwap")[0]
    assert log.signer == agent
    assert log.broadcaster == broadcaster
    assert log.isSignerAgent

    assert actualSwapAmount == deposit_amount
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert bravo_token.balanceOf(ai_wallet) == toAmount == deposit_amount


def test_transfer_with_signature(ai_wallet, sally, agent, owner, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signTransfer):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)

    # setup whitelist
    assert ai_wallet.setWhitelistAddr(sally, True, sender=owner)

    # signature
    signature = signTransfer(ai_wallet, sally, MAX_UINT256, alpha_token.address)

    # transfer
    amount = ai_wallet.transferFunds(
        sally, MAX_UINT256, alpha_token.address, signature, sender=broadcaster)
    
    # transfer
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
    assert log.signer == agent
    assert log.broadcaster == broadcaster
    assert log.isSignerAgent

    assert amount == deposit_amount
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == deposit_amount
