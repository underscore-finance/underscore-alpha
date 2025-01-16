import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS


VAULT_TOKENS = {
    "usdc": {
        "base": "0x0A1a3b5f2041F33522C4efc754a7D096f880eE16",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x859160DB5841E5cfB8D3f144C6b3381A85A4b410",
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": "0x9ECD9fbbdA32b81dee51AdAed28c5C5039c87117",
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0x882018411Bc4A020A879CEE183441fC9fa5D7f8B",
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
def test_euler_deposit_max(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_euler,
    alpha_token_erc4626_vault,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, alpha_token_erc4626_vault)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_euler.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_deposit_partial(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_euler,
    alpha_token_erc4626_vault,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, alpha_token_erc4626_vault)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_euler.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_euler,
    alpha_token_erc4626_vault,
    testLegoWithdrawal,
):
    lego_id = lego_euler.legoId()
    asset, vault_token, _ = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, alpha_token_erc4626_vault)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_euler,
    alpha_token_erc4626_vault,
    testLegoWithdrawal,
):
    lego_id = lego_euler.legoId()
    asset, vault_token, vault_tokens_received = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, alpha_token_erc4626_vault)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)