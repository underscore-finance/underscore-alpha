import pytest
import boa

from constants import ZERO_ADDRESS, MAX_UINT256


@pytest.fixture(scope="module")
def getTokenAndWhale(usdc, usdc_whale, alpha_token, alpha_token_whale):
    def getTokenAndWhale():
        if usdc == ZERO_ADDRESS or usdc_whale == ZERO_ADDRESS:
            return alpha_token, alpha_token_whale
        return usdc, usdc_whale
    yield getTokenAndWhale


@pytest.fixture(scope="module")
def getEulerVault(usdc, usdc_whale, alpha_token_erc4626_vault):
    def getEulerVault():
        if usdc != ZERO_ADDRESS and usdc_whale != ZERO_ADDRESS:
            return boa.from_etherscan("0x0A1a3b5f2041F33522C4efc754a7D096f880eE16", name="usdc_euler_vault")
        return alpha_token_erc4626_vault
    yield getEulerVault


@pytest.always
def test_euler_deposit(
    getTokenAndWhale,
    getEulerVault,
    bob_ai_wallet,
    lego_euler,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_euler.legoId()   

    # setup
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, token.address, sender=sally)

    # success
    euler_vault = getEulerVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, euler_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == euler_vault.address
    
    # check balances
    assert euler_vault.balanceOf(bob_ai_wallet.address) == vault_tokens_received

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_euler.address) == 0


@pytest.always
def test_euler_withdrawal(
    getTokenAndWhale,
    getEulerVault,
    bob_ai_wallet,
    lego_euler,
    bob_agent,
    _test,
):
    lego_id = lego_euler.legoId()   

    # setup (deposit)
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)
    euler_vault = getEulerVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, euler_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == euler_vault.address

    # withdraw
    withdraw_amount, vault_tokens_burned = bob_ai_wallet.withdrawTokens(lego_id, token.address, euler_vault, MAX_UINT256, sender=bob_agent)
    _test(amount, withdraw_amount)
    assert vault_tokens_burned == vault_tokens_received

    # check balances
    assert euler_vault.balanceOf(bob_ai_wallet.address) == 0

    assert token.balanceOf(bob_ai_wallet.address) == withdraw_amount
    assert token.balanceOf(lego_euler.address) == 0
