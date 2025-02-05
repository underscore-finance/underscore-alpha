import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS, TOKENS


VAULT_TOKENS = {
    "usdc": {
        "base": "0x5875eEE11Cf8398102FdAd704C9E96607675467a",
        "local": ZERO_ADDRESS,
    },
    "usds": {
        "base": "0x5875eEE11Cf8398102FdAd704C9E96607675467a",
        "local": ZERO_ADDRESS,
    },
}


TEST_ASSETS = [
    "usdc",
    "usds",
]


@pytest.fixture(scope="module")
def getVaultToken(fork):
    def getVaultToken(_token_str):
        vault_token = VAULT_TOKENS[_token_str][fork]
        if vault_token == ZERO_ADDRESS:
            pytest.skip("asset not relevant on this fork")
        return boa.from_etherscan(vault_token, name=_token_str + "_vault_token")

    yield getVaultToken


@pytest.fixture(scope="module", autouse=True)
def setup_assets(lego_sky, governor, alpha_token, fork):
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
        assert lego_sky.addAssetOpportunity(token, sender=governor)


#########
# Tests #
#########


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_sky_deposit_max(
    getVaultToken,
    token_str,
    testLegoDeposit,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_sky,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_sky.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_sky_deposit_partial(
    token_str,
    testLegoDeposit,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_sky,
    getVaultToken,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_sky.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_sky_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_sky,
    testLegoWithdrawal,
    getVaultToken,
):
    lego_id = lego_sky.legoId()
    vault_token = getVaultToken(token_str)
    asset, _ = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_sky_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_sky,
    testLegoWithdrawal,
    getVaultToken,
):
    lego_id = lego_sky.legoId()
    vault_token = getVaultToken(token_str)
    asset, vault_tokens_received = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)