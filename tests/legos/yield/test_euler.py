import pytest
import boa

from constants import ZERO_ADDRESS
from conf_tokens import TEST_AMOUNTS, TOKENS


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
def setup_assets(lego_euler, governor, alpha_token, fork, getVaultToken):
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
        assert lego_euler.addAssetOpportunity(token, vault_token, sender=governor)


#########
# Tests #
#########


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_deposit_max(
    token_str,
    testLegoDeposit,
    getTokenAndWhale,
    bob_ai_wallet,
    lego_euler,
    getVaultToken,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[token_str] * (10 ** asset.decimals()), sender=whale)

    testLegoDeposit(lego_euler.legoId(), asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_deposit_partial(
    token_str,
    testLegoDeposit,
    getVaultToken,
    bob_ai_wallet,
    lego_euler,
    getTokenAndWhale,
):
    # setup
    vault_token = getVaultToken(token_str)
    asset, whale = getTokenAndWhale(token_str)
    amount = TEST_AMOUNTS[token_str] * (10 ** asset.decimals())
    asset.transfer(bob_ai_wallet.address, amount, sender=whale)

    testLegoDeposit(lego_euler.legoId(), asset, vault_token, amount // 2)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_withdraw_max(
    token_str,
    setupWithdrawal,
    lego_euler,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_euler.legoId()
    vault_token = getVaultToken(token_str)
    asset, _ = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token)


@pytest.mark.parametrize("token_str", TEST_ASSETS)
@pytest.always
def test_euler_withdraw_partial(
    token_str,
    setupWithdrawal,
    lego_euler,
    getVaultToken,
    testLegoWithdrawal,
):
    lego_id = lego_euler.legoId()
    vault_token = getVaultToken(token_str)
    asset, vault_tokens_received = setupWithdrawal(lego_id, token_str, vault_token)

    testLegoWithdrawal(lego_id, asset, vault_token, vault_tokens_received // 2)


@pytest.base
def test_euler_operator_access(
    lego_euler,
    bob,
    bob_ai_wallet,
    governor,
):
    # set rewards
    euler_rewards = boa.from_etherscan("0x3ef3d8ba38ebe18db133cec108f4d14ce00dd9ae", name="euler_rewards")
    assert lego_euler.setEulerRewardsAddr(euler_rewards, sender=governor)

    # no acccess
    assert not euler_rewards.operators(bob_ai_wallet.address, lego_euler.address)

    # claim rewards, will only set access (no rewards tokens given)
    bob_ai_wallet.claimRewards(lego_euler.legoId(), [], [], [], sender=bob)

    # has access
    assert euler_rewards.operators(bob_ai_wallet.address, lego_euler.address)