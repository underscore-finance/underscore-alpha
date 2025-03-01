import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS, TOKENS
from utils.BluePrint import YIELD_TOKENS


VAULT_TOKENS = {
    "usdc": {
        "base": YIELD_TOKENS["base"]["FLUID_USDC"],
        "local": ZERO_ADDRESS,
    },
    "weth": {
        "base": YIELD_TOKENS["base"]["FLUID_WETH"],
        "local": ZERO_ADDRESS,
    },
    "wsteth": {
        "base": YIELD_TOKENS["base"]["FLUID_WSTETH"],
        "local": ZERO_ADDRESS,
    },
    "eurc": {
        "base": YIELD_TOKENS["base"]["FLUID_EURC"],
        "local": ZERO_ADDRESS,
    },
}


TEST_ASSETS = [
    "alpha",
    "usdc",
    "weth",
    "wsteth",
    "eurc",
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
def setup_assets(lego_fluid, governor, alpha_token, fork, getVaultToken):
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
        assert lego_fluid.addAssetOpportunity(token, vault_token, sender=governor)


#########
# Tests #
#########


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_fluid_deposit_max(
    token_str,
    testLegoDeposit,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_fluid,
    getVaultToken,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_fluid.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_fluid_deposit_partial(
    token_str,
    testLegoDeposit,
    getVaultToken,
    bob_ai_wallet,
    lego_fluid,
    getTokenAndWhale,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_fluid.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_fluid_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_fluid,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_fluid.legoId()
    vault_token = getVaultToken(token_str)
    asset, _ = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_fluid_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_fluid,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_fluid.legoId()
    vault_token = getVaultToken(token_str)
    asset, vault_tokens_received = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)