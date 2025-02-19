import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS, TOKENS


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


@pytest.fixture(scope="module")
def getVaultToken(fork, alpha_token_erc4626_vault):
    def getVaultToken(_token_str):
        if _token_str == "alpha":
            if fork == "local":
                return alpha_token_erc4626_vault
            else:
                pytest.skip("asset not relevant on this fork")

        vault_token = VAULT_TOKENS[_token_str][fork]
        if vault_token == ZERO_ADDRESS:
            pytest.skip("asset not relevant on this fork")
        return boa.from_etherscan(vault_token, name=_token_str + "_vault_token")

    yield getVaultToken


@pytest.fixture(scope="module", autouse=True)
def setup_assets(lego_morpho, governor, alpha_token, fork, getVaultToken):
    for token_str in TEST_ASSETS:
        if token_str == "alpha":
            if fork == "local":
                token = alpha_token
            else:
                continue
        else:
            token = TOKENS[token_str][fork]
            if token == ZERO_ADDRESS:
                continue
        vault_token = getVaultToken(token_str)
        assert lego_morpho.addAssetOpportunity(token, vault_token, sender=governor)


#########
# Tests #
#########


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_deposit_max(
    token_str,
    testLegoDeposit,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_morpho,
    getVaultToken,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_morpho.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_deposit_partial(
    token_str,
    testLegoDeposit,
    getVaultToken,
    bob_ai_wallet,
    lego_morpho,
    getTokenAndWhale,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_morpho.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_morpho,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_morpho.legoId()
    vault_token = getVaultToken(token_str)
    asset, _ = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_morpho_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_morpho,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_morpho.legoId()
    vault_token = getVaultToken(token_str)
    asset, vault_tokens_received = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)
