import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, SWAP_UINT256, CONVERSION_UINT256, ADD_LIQ_UINT256, REMOVE_LIQ_UINT256, CLAIM_REWARDS_UINT256, BORROW_UINT256, REPAY_UINT256


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
    assert ai_wallet_config.canAgentAccess(agent, ADD_LIQ_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, REMOVE_LIQ_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, CLAIM_REWARDS_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, BORROW_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, REPAY_UINT256, [], [])

    # Test setting specific allowed actions
    allowed_actions = (True, True, False, False, True, False, True, True, False, True, False, False)
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
    assert log.canAddLiq == True
    assert log.canRemoveLiq == False
    assert log.canClaimRewards == True
    assert log.canBorrow == False
    assert log.canRepay == False

    # Verify permissions
    assert ai_wallet_config.canAgentAccess(agent, DEPOSIT_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, WITHDRAWAL_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, REBALANCE_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, TRANSFER_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, SWAP_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, CONVERSION_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, ADD_LIQ_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, REMOVE_LIQ_UINT256, [], [])
    assert ai_wallet_config.canAgentAccess(agent, CLAIM_REWARDS_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, BORROW_UINT256, [], [])
    assert not ai_wallet_config.canAgentAccess(agent, REPAY_UINT256, [], [])


def test_allowed_actions_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, sally):
    # Setup initial permissions
    ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

    # Set restricted permissions - only allow deposits, transfers, add liquidity, claim rewards, and borrow
    allowed_actions = (True, True, False, False, True, False, False, True, False, True, True, False)
    ai_wallet_config.modifyAllowedActions(agent, allowed_actions, sender=owner)

    # Test deposit (allowed)
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=agent)
    assert assetAmountDeposited == deposit_amount

    # Test withdrawal (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.withdrawTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, vaultTokenAmountReceived, sender=agent)

    # Test transfer (allowed)
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    transfer_amount = deposit_amount // 2    
    assert ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=agent)

    # Test rebalance (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.rebalance(mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, mock_lego_alpha.legoId(), alpha_token_erc4626_vault, vaultTokenAmountReceived, sender=agent)

    # Test swap (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.swapTokens(mock_lego_alpha.legoId(), alpha_token, alpha_token, deposit_amount, sender=agent)

    # Test conversion (not allowed)
    with boa.reverts("agent not allowed"):
        ai_wallet.convertWethToEth(deposit_amount, sender=agent)

    # Test claim rewards (allowed)
    ai_wallet.claimRewards(mock_lego_alpha.legoId(), sender=agent)

    # Test borrow (allowed)
    # Note: This is a mock test since actual borrowing would require more setup
    assert ai_wallet_config.canAgentAccess(agent, BORROW_UINT256, [], [])

