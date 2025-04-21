import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from contracts.core import WalletFunds, WalletConfig


def test_whitelist_add_and_confirm(ai_wallet_config, owner, sally, bob):
    """Test adding an address to the whitelist and confirming it after the delay"""
    # Check initial state
    assert not ai_wallet_config.isRecipientAllowed(sally)
    assert not ai_wallet_config.isRecipientAllowed(bob)
    
    # Add sally to the whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    logs = filter_logs(ai_wallet_config, "WhitelistAddrPending")
    
    # Check pending whitelist data
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    assert pending_data.initiatedBlock == boa.env.evm.patch.block_number
    confirm_block = pending_data.confirmBlock
    assert confirm_block > boa.env.evm.patch.block_number
    
    # Check event was emitted
    assert len(logs) > 0
    log = logs[0]
    assert log.addr == sally
    assert log.confirmBlock == confirm_block
    
    # Confirm before delay should fail
    with boa.reverts("time delay not reached"):
        ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Advance blocks to reach confirmation block
    blocks_to_advance = confirm_block - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Confirm whitelist
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    logs = filter_logs(ai_wallet_config, "WhitelistAddrConfirmed")
    
    # Check state after confirmation
    assert ai_wallet_config.isRecipientAllowed(sally)
    assert not ai_wallet_config.isRecipientAllowed(bob)
    
    # Check pending whitelist data is cleared
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    assert pending_data.initiatedBlock == 0
    assert pending_data.confirmBlock == 0
    
    # Check event was emitted
    assert len(logs) > 0
    log = logs[0]
    assert log.addr == sally
    assert log.initiatedBlock < log.confirmBlock


def test_whitelist_cancel_pending(ai_wallet_config, owner, sally):
    """Test cancelling a pending whitelist address"""
    # Add sally to the whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    
    # Check pending whitelist data
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    assert pending_data.initiatedBlock == boa.env.evm.patch.block_number
    confirm_block = pending_data.confirmBlock
    
    # Cancel the pending whitelist
    ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=owner)
    logs = filter_logs(ai_wallet_config, "WhitelistAddrCancelled")
    
    # Check event was emitted
    assert len(logs) > 0
    log = logs[0]
    assert log.addr == sally
    assert log.initiatedBlock == pending_data.initiatedBlock
    assert log.confirmBlock == confirm_block
    
    # Check pending whitelist data is cleared
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    assert pending_data.initiatedBlock == 0
    assert pending_data.confirmBlock == 0
    
    # Check that sally is not whitelisted
    assert not ai_wallet_config.isRecipientAllowed(sally)


def test_whitelist_remove(ai_wallet_config, owner, sally):
    """Test removing an address from the whitelist"""
    # Add and confirm sally to the whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    
    # Advance blocks to reach confirmation block
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    blocks_to_advance = pending_data.confirmBlock - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    assert ai_wallet_config.isRecipientAllowed(sally)
    
    # Remove sally from the whitelist
    ai_wallet_config.removeWhitelistAddr(sally, sender=owner)
    logs = filter_logs(ai_wallet_config, "WhitelistAddrRemoved")
    
    # Check event was emitted
    assert len(logs) > 0
    log = logs[0]
    assert log.addr == sally
    
    # Check that sally is no longer whitelisted
    assert not ai_wallet_config.isRecipientAllowed(sally)


def test_whitelist_permissions(ai_wallet_config, owner, agent, sally, bob):
    """Test permissions for whitelist operations"""
    # Only owner can add to whitelist
    with boa.reverts("only owner can add whitelist"):
        ai_wallet_config.addWhitelistAddr(sally, sender=agent)
    
    with boa.reverts("only owner can add whitelist"):
        ai_wallet_config.addWhitelistAddr(sally, sender=bob)
    
    # Add sally to whitelist as owner
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    
    # Only owner can cancel pending whitelist
    with boa.reverts("no perms (only owner or governance)"):
        ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=agent)
    
    with boa.reverts("no perms (only owner or governance)"):
        ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=bob)
    
    # Cancel as owner
    ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=owner)
    
    # Add and confirm sally to whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    blocks_to_advance = pending_data.confirmBlock - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Only owner can confirm whitelist
    with boa.reverts("only owner can confirm"):
        ai_wallet_config.confirmWhitelistAddr(sally, sender=agent)
    
    with boa.reverts("only owner can confirm"):
        ai_wallet_config.confirmWhitelistAddr(sally, sender=bob)
    
    # Confirm as owner
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Only owner can remove from whitelist
    with boa.reverts("only owner can remove whitelist"):
        ai_wallet_config.removeWhitelistAddr(sally, sender=agent)
    
    with boa.reverts("only owner can remove whitelist"):
        ai_wallet_config.removeWhitelistAddr(sally, sender=bob)
    
    # Remove as owner
    ai_wallet_config.removeWhitelistAddr(sally, sender=owner)


def test_whitelist_validation(ai_wallet_config, owner, ai_wallet):
    """Test validation rules for whitelist operations"""
    # Cannot whitelist zero address
    with boa.reverts("invalid addr"):
        ai_wallet_config.addWhitelistAddr(ZERO_ADDRESS, sender=owner)
    
    # Cannot whitelist owner
    with boa.reverts("owner cannot be whitelisted"):
        ai_wallet_config.addWhitelistAddr(owner, sender=owner)
    
    # Cannot whitelist wallet config
    with boa.reverts("wallet cannot be whitelisted"):
        ai_wallet_config.addWhitelistAddr(ai_wallet_config.address, sender=owner)
    
    # Cannot confirm non-existent pending whitelist
    with boa.reverts("no pending whitelist"):
        ai_wallet_config.confirmWhitelistAddr(owner, sender=owner)
    
    # Cannot cancel non-existent pending whitelist
    with boa.reverts("no pending whitelist"):
        ai_wallet_config.cancelPendingWhitelistAddr(owner, sender=owner)
    
    # Cannot remove non-whitelisted address
    with boa.reverts("not on whitelist"):
        ai_wallet_config.removeWhitelistAddr(owner, sender=owner)


def test_can_transfer_to_recipient(ai_wallet_config, owner, sally, bob, agent_factory, addy_registry):
    """Test the canTransferToRecipient function"""
    # Initially, cannot transfer to non-whitelisted address
    assert not ai_wallet_config.canTransferToRecipient(sally)
    
    # Add and confirm sally to whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    blocks_to_advance = pending_data.confirmBlock - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Now can transfer to sally
    assert ai_wallet_config.canTransferToRecipient(sally)
    
    # Create a new wallet owned by the same owner
    new_wallet = agent_factory.createUserWallet(owner, ZERO_ADDRESS, sender=owner)
    
    # Should be able to transfer to a wallet with the same owner
    assert ai_wallet_config.canTransferToRecipient(new_wallet)
    
    # Create a wallet with a different owner
    other_wallet = agent_factory.createUserWallet(bob, ZERO_ADDRESS, sender=bob)
    
    # Should not be able to transfer to a wallet with a different owner
    assert not ai_wallet_config.canTransferToRecipient(other_wallet)


def test_pending_ownership_change_affects_transfers(ai_wallet_config, owner, bob, agent_factory):
    """Test that pending ownership changes affect transfers to other wallets"""
    # Create a new wallet owned by the same owner
    new_wallet = agent_factory.createUserWallet(owner, ZERO_ADDRESS, sender=owner)
    
    # Initially can transfer to wallet with same owner
    assert ai_wallet_config.canTransferToRecipient(new_wallet)
    
    # Initiate ownership change
    ai_wallet_config.changeOwnership(bob, sender=owner)
    
    # Now should not be able to transfer to any wallet, even with same owner
    assert not ai_wallet_config.canTransferToRecipient(new_wallet)
    
    # Cancel ownership change
    ai_wallet_config.cancelOwnershipChange(sender=owner)
    
    # Should be able to transfer again
    assert ai_wallet_config.canTransferToRecipient(new_wallet)


def test_transfer_to_wallet_with_pending_ownership(ai_wallet_config, owner, bob, agent_factory):
    """Test that transfers to wallets with pending ownership changes are not allowed"""
    # Create a new wallet owned by the same owner
    new_wallet = agent_factory.createUserWallet(owner, ZERO_ADDRESS, sender=owner)
    new_wallet_config = WalletConfig.at(WalletFunds.at(new_wallet).walletConfig())
    
    # Initially can transfer to wallet with same owner
    assert ai_wallet_config.canTransferToRecipient(new_wallet)
    
    # Initiate ownership change on the target wallet
    new_wallet_config.changeOwnership(bob, sender=owner)
    
    # Now should not be able to transfer to that wallet
    assert not ai_wallet_config.canTransferToRecipient(new_wallet)


def test_transfer_from_wallet_with_pending_ownership(ai_wallet, ai_wallet_config, owner, bob, agent, alpha_token, alpha_token_whale, agent_factory):
    """Test that transfers from wallets with pending ownership changes are allowed"""
    # Fund the wallet
    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Add bob to whitelist
    ai_wallet_config.addWhitelistAddr(bob, sender=owner)
    pending_data = ai_wallet_config.pendingWhitelist(bob)
    blocks_to_advance = pending_data.confirmBlock - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    ai_wallet_config.confirmWhitelistAddr(bob, sender=owner)
    
    # Initiate ownership change
    ai_wallet_config.changeOwnership(bob, sender=owner)
    
    # Transfer should still work
    ai_wallet.transferFunds(bob, amount // 2, alpha_token, sender=owner)
    
    # Check balances
    assert alpha_token.balanceOf(bob) == amount // 2
    assert alpha_token.balanceOf(ai_wallet) == amount // 2


def test_transfer_funds_with_whitelist(ai_wallet, ai_wallet_config, owner, agent, sally, bob, alpha_token, alpha_token_whale, agent_factory):
    """Test transferring funds with whitelist restrictions"""
    # Fund the wallet
    amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Try to transfer to non-whitelisted address
    with boa.reverts("recipient not allowed"):
        ai_wallet.transferFunds(sally, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=owner)
    
    # Add sally to whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    pending_data = ai_wallet_config.pendingWhitelist(sally)
    blocks_to_advance = pending_data.confirmBlock - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    ai_wallet_config.confirmWhitelistAddr(sally, sender=owner)
    
    # Now transfer should succeed
    ai_wallet.transferFunds(sally, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=owner)
    assert alpha_token.balanceOf(sally) == 100 * EIGHTEEN_DECIMALS
    
    # Try to transfer to another non-whitelisted address
    with boa.reverts("recipient not allowed"):
        ai_wallet.transferFunds(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=owner)
    
    # Create a new wallet owned by the same owner
    new_wallet = agent_factory.createUserWallet(owner, ZERO_ADDRESS, sender=owner)
    
    # Should be able to transfer to wallet with same owner without whitelisting
    ai_wallet.transferFunds(new_wallet, 100 * EIGHTEEN_DECIMALS, alpha_token, sender=owner)
    assert alpha_token.balanceOf(new_wallet) == 100 * EIGHTEEN_DECIMALS


def test_transfer_from_wallet_with_pending_ownership(ai_wallet, ai_wallet_config, owner, bob, agent, alpha_token, alpha_token_whale, agent_factory):
    """Test that transfers from wallets with pending ownership changes are allowed"""
    # Fund the wallet
    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    
    # Add bob to whitelist
    ai_wallet_config.addWhitelistAddr(bob, sender=owner)
    pending_data = ai_wallet_config.pendingWhitelist(bob)
    blocks_to_advance = pending_data.confirmBlock - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_advance)
    ai_wallet_config.confirmWhitelistAddr(bob, sender=owner)
    
    # Initiate ownership change
    ai_wallet_config.changeOwnership(bob, sender=owner)
    
    # Transfer should still work
    ai_wallet.transferFunds(bob, amount // 2, alpha_token, sender=owner)
    
    # Check balances
    assert alpha_token.balanceOf(bob) == amount // 2
    assert alpha_token.balanceOf(ai_wallet) == amount // 2 