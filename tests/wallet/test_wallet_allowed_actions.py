import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256, CONVERSION_UINT256


def test_modify_allowed_actions(ai_wallet, ai_wallet_config, owner, agent, sally):
    # Test non-owner cannot modify allowed actions
    with boa.reverts("no perms"):
        ai_wallet_config.modifyAllowedActions(agent, sender=sally)

    # Test cannot modify non-active agent
    with boa.reverts("agent not active"):
        ai_wallet_config.modifyAllowedActions(sally, sender=owner)

    # Test default state - all actions allowed when not set
    assert ai_wallet_config.canAgentAccess(agent, DEPOSIT_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, WITHDRAWAL_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, REBALANCE_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, TRANSFER_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, SWAP_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, CONVERSION_UINT256, [], [])

    # Test setting specific allowed actions
    allowed_actions = (True, True, False, False, True, False, True)
    assert ai_wallet_config.modifyAllowedActions(agent, allowed_actions, sender=owner)

    # Verify event
    log = filter_logs(ai_wallet_config, "AllowedActionsModified")[0]
    assert log.agent == agent
    assert log.canDeposit == True
    assert log.canWithdraw == False
    assert log.canRebalance == False
    assert log.canTransfer == True
    assert log.canSwap == False
    assert log.canConvert == True

    # Verify permissions
    assert ai_wallet_config.canAgentAccess(agent, DEPOSIT_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, WITHDRAWAL_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, REBALANCE_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, TRANSFER_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, SWAP_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, CONVERSION_UINT256, [], [])


def test_allowed_actions_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, sally):
    # Setup initial permissions
    ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

    # Set restricted permissions - only allow deposits and transfers
    allowed_actions = (True, True, False, False, True, False, False)
    ai_wallet_config.modifyAllowedActions(agent, allowed_actions, sender=owner)

    # Test deposit (allowed)
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == deposit_amount

    # Test withdrawal (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, vaultTokenAmountReceived, alpha_token_erc4626_vault, sender=agent)

    # Test transfer (allowed)
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    transfer_amount = deposit_amount // 2    
    assert ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=agent)

    # Test rebalance (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.rebalance(mock_lego_alpha.legoId(), mock_lego_alpha.legoId(), alpha_token, 
                          vaultTokenAmountReceived, alpha_token_erc4626_vault, alpha_token_erc4626_vault, sender=agent)

    # Test swap (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.swapTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token, deposit_amount, sender=agent)

    # Test conversion (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.convertWethToEth(deposit_amount, sender=agent)


def test_allowed_actions_batch_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, sally):
    # Setup initial permissions
    ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

    # Set restricted permissions - only allow deposits and transfers
    allowed_actions = (True, True, False, False, True, False, False)
    ai_wallet_config.modifyAllowedActions(agent, allowed_actions, sender=owner)

    # Transfer tokens to wallet
    amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)

    # Create batch instructions with mix of allowed and disallowed actions
    instructions = [
        # Deposit (allowed)
        (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),
        # Withdrawal (not allowed)
        (WITHDRAWAL_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 2, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),
    ]

    # Test batch operations fail if any action is not allowed
    with boa.reverts("agent not allowed"):
        ai_wallet.performManyActions(instructions, sender=agent)

    # Test batch operations with only allowed actions
    allowed_instructions = [
        # Deposit (allowed)
        (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 2, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),
        # Transfer (allowed)
        (TRANSFER_UINT256, 0, alpha_token, ZERO_ADDRESS, amount // 2, sally, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),
    ]

    assert ai_wallet.performManyActions(allowed_instructions, sender=agent) 