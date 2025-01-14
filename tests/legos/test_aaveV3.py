import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs
from contracts.mock import MockErc20


@pytest.fixture(scope="module")
def getTokenAndWhale(usdc, usdc_whale, alpha_token, alpha_token_whale):
    def getTokenAndWhale():
        if usdc == ZERO_ADDRESS or usdc_whale == ZERO_ADDRESS:
            return alpha_token, alpha_token_whale
        return usdc, usdc_whale
    yield getTokenAndWhale


@pytest.always
def test_aaveV3_deposit_already_in_wallet(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aave_v3,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_aave_v3.legoId()   

    # setup
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, token.address, sender=sally)

    # success
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, sender=bob_agent)
    _test(amount, deposit_amount)
    
    # # wallet log
    # log_wallet = filter_logs(bob_ai_wallet, "AgenticDeposit")[0]
    # assert log_wallet.user == bob_agent
    # assert log_wallet.asset == token.address
    # assert log_wallet.vault == ZERO_ADDRESS
    # assert log_wallet.assetAmountDeposited == deposit_amount
    # assert log_wallet.vaultToken == vault_token
    # assert log_wallet.vaultTokenAmountReceived == vault_tokens_received
    # assert log_wallet.legoId == lego_id
    # assert log_wallet.legoAddr == lego_aave_v3.address
    # assert log_wallet.isAgent == True

    # # aave v3 log
    # log_pool = filter_logs(bob_ai_wallet, "AaveV3Deposit")[0]
    # assert log_pool.user == bob_ai_wallet.address
    # assert log_pool.asset == token.address
    # assert log_pool.vaultToken == vault_token
    # assert log_pool.assetAmountDeposited == deposit_amount
    # assert log_pool.vaultTokenAmountReceived == vault_tokens_received
    # assert log_pool.refundAmount == 0

    # check balances
    vault_token = MockErc20.at(vault_token)
    assert vault_token.balanceOf(bob_ai_wallet.address) == vault_tokens_received

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_aave_v3.address) == 0


@pytest.always
def test_aaveV3_deposit_on_transfer(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aave_v3,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_aave_v3.legoId()

    # setup
    token, whale = getTokenAndWhale()
    amount = 100 * (10 ** token.decimals())
    token.transfer(bob_agent, amount, sender=whale)

    token.approve(bob_ai_wallet.address, amount, sender=bob_agent)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokensWithTransfer(lego_id, token.address, sender=sally)

    # success
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokensWithTransfer(lego_id, token.address, sender=bob_agent)
    _test(amount, deposit_amount)

    # check balances
    vault_token = MockErc20.at(vault_token)
    assert vault_token.balanceOf(bob_ai_wallet.address) == vault_tokens_received
    assert vault_token.balanceOf(bob_agent) == 0

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_aave_v3.address) == 0
    assert token.balanceOf(bob_agent) == 0


@pytest.always
def test_aaveV3_withdrawal(
    getTokenAndWhale,
    bob_ai_wallet,
    lego_aave_v3,
    bob_agent,
    _test,
):
    lego_id = lego_aave_v3.legoId()   

    # setup (deposit)
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, sender=bob_agent)
    _test(amount, deposit_amount)

    # withdraw
    withdraw_amount, vault_tokens_burned = bob_ai_wallet.withdrawTokens(lego_id, token.address, vault_token, sender=bob_agent)
    _test(amount, withdraw_amount)
    assert vault_tokens_burned == vault_tokens_received

    # # wallet log
    # log_wallet = filter_logs(bob_ai_wallet, "AgenticWithdrawal")[0]
    # assert log_wallet.user == bob_agent
    # assert log_wallet.asset == token.address
    # assert log_wallet.vaultToken == vault_token
    # assert log_wallet.assetAmountReceived == withdraw_amount
    # assert log_wallet.vaultTokenAmountBurned == vault_tokens_burned
    # assert log_wallet.vault == ZERO_ADDRESS
    # assert log_wallet.legoId == lego_id
    # assert log_wallet.legoAddr == lego_aave_v3.address
    # assert log_wallet.isAgent == True

    # # aave v3 log
    # log_pool = filter_logs(bob_ai_wallet, "AaveV3Withdrawal")[0]
    # assert log_pool.user == bob_ai_wallet.address
    # assert log_pool.asset == token.address
    # assert log_pool.vaultToken == vault_token
    # assert log_pool.assetAmountReceived == withdraw_amount
    # assert log_pool.vaultTokenAmountBurned == vault_tokens_burned
    # assert log_pool.refundVaultTokenAmount == 0

    # check balances
    vault_token = MockErc20.at(vault_token)
    assert vault_token.balanceOf(bob_ai_wallet.address) == 0

    assert token.balanceOf(bob_ai_wallet.address) == withdraw_amount
    assert token.balanceOf(lego_aave_v3.address) == 0
