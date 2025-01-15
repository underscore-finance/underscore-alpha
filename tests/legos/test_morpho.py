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
def getMorphoVault(usdc, usdc_whale, alpha_token_erc4626_vault):
    def getMorphoVault():
        if usdc != ZERO_ADDRESS and usdc_whale != ZERO_ADDRESS:
            return boa.from_etherscan("0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca", name="usdc_morpho_vault")
        return alpha_token_erc4626_vault
    yield getMorphoVault


@pytest.always
def test_morpho_deposit(
    getTokenAndWhale,
    getMorphoVault,
    bob_ai_wallet,
    lego_morpho,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_morpho.legoId()   

    # setup
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, token.address, sender=sally)

    # success
    morpho_vault = getMorphoVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, morpho_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == morpho_vault.address
    
    # check balances
    assert morpho_vault.balanceOf(bob_ai_wallet.address) == vault_tokens_received

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_morpho.address) == 0


@pytest.always
def test_morpho_withdrawal(
    getTokenAndWhale,
    getMorphoVault,
    bob_ai_wallet,
    lego_morpho,
    bob_agent,
    _test,
):
    lego_id = lego_morpho.legoId()   

    # setup (deposit)
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)
    morpho_vault = getMorphoVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, morpho_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == morpho_vault.address

    # withdraw
    withdraw_amount, vault_tokens_burned = bob_ai_wallet.withdrawTokens(lego_id, token.address, morpho_vault, MAX_UINT256, sender=bob_agent)
    _test(amount, withdraw_amount)
    assert vault_tokens_burned == vault_tokens_received

    # check balances
    assert morpho_vault.balanceOf(bob_ai_wallet.address) == 0

    assert token.balanceOf(bob_ai_wallet.address) == withdraw_amount
    assert token.balanceOf(lego_morpho.address) == 0
