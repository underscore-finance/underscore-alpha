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
def getFluidVault(usdc, usdc_whale, alpha_token_erc4626_vault):
    def getFluidVault():
        if usdc != ZERO_ADDRESS and usdc_whale != ZERO_ADDRESS:
            return boa.from_etherscan("0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169", name="usdc_fluid_vault")
        return alpha_token_erc4626_vault
    yield getFluidVault


@pytest.always
def test_fluid_deposit(
    getTokenAndWhale,
    getFluidVault,
    bob_ai_wallet,
    lego_fluid,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_fluid.legoId()   

    # setup
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, token.address, sender=sally)

    # success
    fluid_vault = getFluidVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, fluid_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == fluid_vault.address
    
    # check balances
    assert fluid_vault.balanceOf(bob_ai_wallet.address) == vault_tokens_received

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_fluid.address) == 0


@pytest.always
def test_fluid_withdrawal(
    getTokenAndWhale,
    getFluidVault,
    bob_ai_wallet,
    lego_fluid,
    bob_agent,
    _test,
):
    lego_id = lego_fluid.legoId()   

    # setup (deposit)
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)
    fluid_vault = getFluidVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, fluid_vault, sender=bob_agent)
    _test(amount, deposit_amount)

    # withdraw
    withdraw_amount, vault_tokens_burned = bob_ai_wallet.withdrawTokens(lego_id, token.address, vault_token, MAX_UINT256, fluid_vault, sender=bob_agent)
    _test(amount, withdraw_amount)
    assert vault_tokens_burned == vault_tokens_received

    # check balances
    assert fluid_vault.balanceOf(bob_ai_wallet.address) == 0

    assert token.balanceOf(bob_ai_wallet.address) == withdraw_amount
    assert token.balanceOf(lego_fluid.address) == 0
