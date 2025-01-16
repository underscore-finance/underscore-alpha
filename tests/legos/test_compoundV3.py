import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS


VAULT_TOKENS = {
    "usdc": {
        "base": "0xb125E6687d4313864e53df431d5425969c15Eb2F",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x46e6b214b524310239732D51387075E0e70970bf",
        "local": ZERO_ADDRESS,
    },
    "aero": {
        "base": "0x784efeB622244d2348d4F2522f8860B96fbEcE89",
        "local": ZERO_ADDRESS,
    },
}


TEST_ASSETS = [
    "alpha",
    "usdc",
    "weth",
    "aero",
]


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_compoundV3_deposit_max(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_compound_v3,
    alpha_token_comp_vault,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, alpha_token_comp_vault)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_compound_v3.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_compoundV3_deposit_partial(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_compound_v3,
    alpha_token_comp_vault,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, alpha_token_comp_vault)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_compound_v3.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_compoundV3_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_compound_v3,
    alpha_token_comp_vault,
    testLegoWithdrawal,
):
    lego_id = lego_compound_v3.legoId()
    asset, vault_token, _ = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, alpha_token_comp_vault)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_compoundV3_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_compound_v3,
    alpha_token_comp_vault,
    testLegoWithdrawal,
):
    lego_id = lego_compound_v3.legoId()
    asset, vault_token, vault_tokens_received = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, alpha_token_comp_vault)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)