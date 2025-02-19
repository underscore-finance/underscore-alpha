import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS, TOKENS


VAULT_TOKENS = {
    "usdc": {
        "base": "0xedc817a28e8b93b03976fbd4a3ddbc9f7d176c22",
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": "0x628ff693426583D9a7FB391E54366292F509D457",
        "local": ZERO_ADDRESS,
    },
    "cbbtc": {
        "base": "0xF877ACaFA28c19b96727966690b2f44d35aD5976",
        "local": ZERO_ADDRESS,
    },
    "wsteth": {
        "base": "0x627fe393bc6edda28e99ae648fd6ff362514304b",
        "local": ZERO_ADDRESS,
    },
    "cbeth": {
        "base": "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5",
        "local": ZERO_ADDRESS,
    },
    "aero": {
        "base": "0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6",
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
    "aero",
]


@pytest.fixture(scope="module")
def getVaultToken(fork, alpha_token_comp_vault):
    def getVaultToken(_token_str):
        if _token_str == "alpha":
            if fork == "local":
                return alpha_token_comp_vault
            else:
                pytest.skip("asset not relevant on this fork")

        vault_token = VAULT_TOKENS[_token_str][fork]
        if vault_token == ZERO_ADDRESS:
            pytest.skip("asset not relevant on this fork")
        return boa.from_etherscan(vault_token, name=_token_str + "_vault_token")

    yield getVaultToken


@pytest.fixture(scope="module", autouse=True)
def setup_assets(lego_moonwell, governor, alpha_token, fork, getVaultToken):
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
        assert lego_moonwell.addAssetOpportunity(token, vault_token, sender=governor)


#########
# Tests #
#########


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_moonwell_deposit_max(
    token_str,
    testLegoDeposit,
    getVaultToken,
    bob_ai_wallet,
    lego_moonwell,
    getTokenAndWhale,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_moonwell.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_moonwell_deposit_partial(
    token_str,
    testLegoDeposit,
    getVaultToken,
    bob_ai_wallet,
    lego_moonwell,
    getTokenAndWhale,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_moonwell.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_moonwell_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_moonwell,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_moonwell.legoId()
    vault_token = getVaultToken(token_str)
    asset, _ = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_moonwell_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_moonwell,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_moonwell.legoId()
    vault_token = getVaultToken(token_str)
    asset, vault_tokens_received = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)