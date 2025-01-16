import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS


VAULT_TOKENS = {
    "usdc": {
        "base": "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7",
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6",
        "local": ZERO_ADDRESS,
    },
    "wsteth": {
        "base": "0x99CBC45ea5bb7eF3a5BC08FB1B7E56bB2442Ef0D",
        "local": ZERO_ADDRESS,
    },
    "cbeth": {
        "base": "0xcf3D55c10DB69f28fD1A75Bd73f3D8A2d9c595ad",
        "local": ZERO_ADDRESS,
    },
}


TEST_ASSETS = [
    "alpha",
    "usdc",
    "weth",
    "cbbtc",
    "wsteth",
    "cbeth",
]


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aaveV3_deposit_max(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_aave_v3,
    mock_aave_v3_pool,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, mock_aave_v3_pool)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_aave_v3.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aaveV3_deposit_partial(
    token_str,
    testLegoDeposit,
    getAssetInfo,
    bob_ai_wallet,
    lego_aave_v3,
    mock_aave_v3_pool,
):
    # setup
    asset, whale, vault_token = getAssetInfo(token_str, VAULT_TOKENS, mock_aave_v3_pool)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_aave_v3.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aaveV3_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_aave_v3,
    mock_aave_v3_pool,
    testLegoWithdrawal,
):
    lego_id = lego_aave_v3.legoId()
    asset, vault_token, _ = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, mock_aave_v3_pool)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_aaveV3_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_aave_v3,
    mock_aave_v3_pool,
    testLegoWithdrawal,
):
    lego_id = lego_aave_v3.legoId()
    asset, vault_token, vault_tokens_received = setupWithdrawal(lego_id, token_str, VAULT_TOKENS, mock_aave_v3_pool)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)