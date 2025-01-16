import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS


VAULT_TOKENS = {
    "usdc": {
        "base": "0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1",
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": "0xf24608E0CCb972b0b0f4A6446a0BBf58c701a026",
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796",
        "local": ZERO_ADDRESS,
    },
}


TEST_ASSETS = [
    "alpha",
    "usdc",
    "weth",
    "eurc",
    "cbbtc",
]


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_deposit_max(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_morpho,
    alpha_token_erc4626_vault,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, alpha_token_erc4626_vault)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_morpho.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_deposit_partial(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_morpho,
    alpha_token_erc4626_vault,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, alpha_token_erc4626_vault)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_morpho.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_morpho,
    alpha_token_erc4626_vault,
    testLegoWithdrawal,
):
    lego_id = lego_morpho.legoId()
    asset, vault_token, _ = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, alpha_token_erc4626_vault)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_morpho,
    alpha_token_erc4626_vault,
    testLegoWithdrawal,
):
    lego_id = lego_morpho.legoId()
    asset, vault_token, vault_tokens_received = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, alpha_token_erc4626_vault)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)