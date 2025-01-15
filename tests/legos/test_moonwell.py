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
def getMoonwellVault(usdc, usdc_whale, alpha_token_compV2_vault):
    def getMoonwellVault():
        if usdc != ZERO_ADDRESS and usdc_whale != ZERO_ADDRESS:
            return boa.from_etherscan("0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22", name="usdc_moonwell_vault")
        return alpha_token_compV2_vault
    yield getMoonwellVault


@pytest.always
def test_moonwell_deposit(
    getTokenAndWhale,
    getMoonwellVault,
    bob_ai_wallet,
    lego_moonwell,
    bob_agent,
    sally,
    _test,
):
    lego_id = lego_moonwell.legoId()   

    # setup
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)

    # no perms
    with boa.reverts():
        bob_ai_wallet.depositTokens(lego_id, token.address, sender=sally)

    # success
    moonwell_vault = getMoonwellVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, moonwell_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == moonwell_vault.address
    
    # check balances
    assert moonwell_vault.balanceOf(bob_ai_wallet.address) == vault_tokens_received

    assert token.balanceOf(bob_ai_wallet.address) == 0
    assert token.balanceOf(lego_moonwell.address) == 0


@pytest.always
def test_moonwell_withdrawal(
    getTokenAndWhale,
    getMoonwellVault,
    bob_ai_wallet,
    lego_moonwell,
    bob_agent,
    _test,
):
    lego_id = lego_moonwell.legoId()   

    # setup (deposit)
    token, whale = getTokenAndWhale()
    amount = 1_000 * (10 ** token.decimals())
    token.transfer(bob_ai_wallet.address, amount, sender=whale)
    moonwell_vault = getMoonwellVault()
    deposit_amount, vault_token, vault_tokens_received = bob_ai_wallet.depositTokens(lego_id, token.address, MAX_UINT256, moonwell_vault, sender=bob_agent)
    _test(amount, deposit_amount)
    assert vault_token == moonwell_vault.address

    # withdraw
    withdraw_amount, vault_tokens_burned = bob_ai_wallet.withdrawTokens(lego_id, token.address, moonwell_vault, MAX_UINT256, sender=bob_agent)
    _test(amount, withdraw_amount)
    assert vault_tokens_burned == vault_tokens_received

    # check balances
    assert moonwell_vault.balanceOf(bob_ai_wallet.address) == 0

    assert token.balanceOf(bob_ai_wallet.address) == withdraw_amount
    assert token.balanceOf(lego_moonwell.address) == 0
