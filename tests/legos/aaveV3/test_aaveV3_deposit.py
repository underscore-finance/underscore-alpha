import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


def test_aaveV3_deposit_already_in_wallet(
    bob_ai_wallet,
    alpha_token,
    lego_aave_v3,
    governor,
    bob_agent,
    sally,
    mock_aave_v3_pool,
):
    alpha_token.mint(bob_ai_wallet.address, 100 * EIGHTEEN_DECIMALS, sender=governor)
    lego_id = lego_aave_v3.legoId()

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, alpha_token.address, sender=sally)

    # success
    deposit_amount, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, alpha_token.address, sender=bob_agent)
    
    # wallet log
    log_wallet = filter_logs(bob_ai_wallet, "AgenticLegoDeposit")[0]
    assert log_wallet.user == bob_agent
    assert log_wallet.asset == alpha_token.address
    assert log_wallet.vault == ZERO_ADDRESS
    assert log_wallet.legoId == lego_id
    assert log_wallet.legoAddr == lego_aave_v3.address
    assert log_wallet.depositAmount == deposit_amount
    assert log_wallet.vaultTokensReceived == vault_tokens_received

    # aave v3 log
    log_pool = filter_logs(bob_ai_wallet, "AaveV3Deposit")[0]
    assert log_pool.user == bob_ai_wallet.address
    assert log_pool.asset == alpha_token.address
    assert log_pool.depositAmount == deposit_amount
    assert log_pool.vaultTokens == vault_tokens_received
    assert log_pool.refundAmount == 0

    # check balances
    assert mock_aave_v3_pool.balanceOf(bob_ai_wallet.address) == vault_tokens_received
    assert alpha_token.balanceOf(bob_ai_wallet.address) == 0
    assert alpha_token.balanceOf(lego_aave_v3.address) == 0
    assert alpha_token.balanceOf(mock_aave_v3_pool.address) == deposit_amount


def test_aaveV3_deposit_on_transfer(
    bob_ai_wallet,
    alpha_token,
    lego_aave_v3,
    governor,
    bob_agent,
    sally,
    mock_aave_v3_pool,
):
    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.mint(bob_agent, amount, sender=governor)
    alpha_token.approve(bob_ai_wallet.address, amount, sender=bob_agent)
    lego_id = lego_aave_v3.legoId()

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokensWithTransfer(lego_id, alpha_token.address, sender=sally)

    # success
    deposit_amount, vault_tokens_received = bob_ai_wallet.depositTokensWithTransfer(lego_id, alpha_token.address, sender=bob_agent)

    # check balances
    assert mock_aave_v3_pool.balanceOf(bob_ai_wallet.address) == vault_tokens_received
    assert mock_aave_v3_pool.balanceOf(bob_agent) == 0
    assert alpha_token.balanceOf(bob_agent) == 0
    assert alpha_token.balanceOf(bob_ai_wallet.address) == 0
    assert alpha_token.balanceOf(lego_aave_v3.address) == 0
    assert alpha_token.balanceOf(mock_aave_v3_pool.address) == deposit_amount