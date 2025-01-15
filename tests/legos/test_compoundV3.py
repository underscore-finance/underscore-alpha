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
def getCompoundV3Vault(usdc, usdc_whale, alpha_token_compV3_vault):
    def getCompoundV3Vault():
        if usdc != ZERO_ADDRESS and usdc_whale != ZERO_ADDRESS:
            return boa.from_etherscan("0xb125E6687d4313864e53df431d5425969c15Eb2F", name="usdc_compound_v3_vault")
        return alpha_token_compV3_vault
    yield getCompoundV3Vault


@pytest.always
def test_compv3_deposit(
    getTokenAndWhale,
    getCompoundV3Vault,
    bob_ai_wallet,
    lego_compound_v3,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_compound_v3.legoId()   

    # setup
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, token.address, sender=sally)

    # success
    comp_vault = getCompoundV3Vault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, comp_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == comp_vault.address
    
    # check balances
    assert comp_vault.balanceOf(bob_ai_wallet.address) == vault_tokens_received

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_compound_v3.address) == 0


@pytest.always
def test_compv3_withdrawal(
    getTokenAndWhale,
    getCompoundV3Vault,
    bob_ai_wallet,
    lego_compound_v3,
    bob_agent,
    _test,
):
    lego_id = lego_compound_v3.legoId()   

    # setup (deposit)
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)
    comp_vault = getCompoundV3Vault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, comp_vault, sender=bob_agent)
    _test(amount, deposit_amount)

    assert vault_token == comp_vault.address

    # withdraw
    withdraw_amount, vault_tokens_burned = bob_ai_wallet.withdrawTokens(lego_id, token.address, comp_vault.address, MAX_UINT256, comp_vault.address, sender=bob_agent)
    _test(amount, withdraw_amount)
    _test(vault_tokens_received, vault_tokens_burned)

    # check balances
    assert comp_vault.balanceOf(bob_ai_wallet.address) == 0

    _test(withdraw_amount, token.balanceOf(bob_ai_wallet.address))
    assert token.balanceOf(lego_compound_v3.address) == 0
