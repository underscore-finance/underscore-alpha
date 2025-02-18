import pytest
import boa

from constants import MAX_UINT256
from conf_utils import filter_logs
from conf_tokens import TEST_AMOUNTS


@pytest.fixture(scope="package")
def setupWithdrawal(getTokenAndWhale, bob_ai_wallet, bob_agent):
    def setupWithdrawal(_legoId, _token_str, _vaultToken):
        asset, whale = getTokenAndWhale(_token_str)
        asset.transfer(bob_ai_wallet.address, TEST_AMOUNTS[_token_str] * (10 ** asset.decimals()), sender=whale)
        _a, _b, vault_tokens_received, _c = bob_ai_wallet.depositTokens(_legoId, asset.address, _vaultToken, MAX_UINT256, sender=bob_agent)
        return asset, vault_tokens_received

    yield setupWithdrawal


@pytest.fixture(scope="package")
def testLegoDeposit(bob_ai_wallet, bob_agent, lego_registry, _test):
    def testLegoDeposit(
        _legoId,
        _asset,
        _vaultToken,
        _amount = MAX_UINT256,
    ):
        # pre balances
        pre_user_asset_bal = _asset.balanceOf(bob_ai_wallet)
        pre_user_vault_bal = _vaultToken.balanceOf(bob_ai_wallet)

        lego_addr = lego_registry.getLegoAddr(_legoId)
        pre_lego_asset_bal = _asset.balanceOf(lego_addr)
        pre_lego_vault_bal = _vaultToken.balanceOf(lego_addr)

        # deposit
        deposit_amount, vault_token, vault_tokens_received, usd_value = bob_ai_wallet.depositTokens(_legoId, _asset.address, _vaultToken, _amount, sender=bob_agent)

        # event
        log_wallet = filter_logs(bob_ai_wallet, "AgenticDeposit")[0]
        assert log_wallet.signer == bob_agent
        assert log_wallet.asset == _asset.address
        assert log_wallet.vaultToken == vault_token
        assert log_wallet.assetAmountDeposited == deposit_amount
        assert log_wallet.vaultTokenAmountReceived == vault_tokens_received
        assert log_wallet.usdValue == usd_value
        assert log_wallet.legoId == _legoId
        assert log_wallet.legoAddr == lego_addr
        assert log_wallet.isSignerAgent == True

        assert _vaultToken.address == vault_token
        assert deposit_amount != 0
        assert vault_tokens_received != 0

        if _amount == MAX_UINT256:
            _test(deposit_amount, pre_user_asset_bal)
        else:
            _test(deposit_amount, _amount)

        # lego addr should not have any leftover
        assert _asset.balanceOf(lego_addr) == pre_lego_asset_bal
        assert _vaultToken.balanceOf(lego_addr) == pre_lego_vault_bal

        # vault tokens
        _test(pre_user_vault_bal + vault_tokens_received, _vaultToken.balanceOf(bob_ai_wallet.address))

        # asset amounts
        _test(pre_user_asset_bal - deposit_amount, _asset.balanceOf(bob_ai_wallet.address))


    yield testLegoDeposit


@pytest.fixture(scope="package")
def testLegoWithdrawal(bob_ai_wallet, bob_agent, lego_registry, _test):
    def testLegoWithdrawal(
        _legoId,
        _asset,
        _vaultToken,
        _amount = MAX_UINT256,
    ):
        # pre balances
        pre_user_asset_bal = _asset.balanceOf(bob_ai_wallet)
        pre_user_vault_bal = _vaultToken.balanceOf(bob_ai_wallet)

        lego_addr = lego_registry.getLegoAddr(_legoId)
        pre_lego_asset_bal = _asset.balanceOf(lego_addr)
        pre_lego_vault_bal = _vaultToken.balanceOf(lego_addr)

        # deposit
        amount_received, vault_token_burned, usd_value = bob_ai_wallet.withdrawTokens(_legoId, _asset.address, _vaultToken, _amount, sender=bob_agent)

        # event
        log_wallet = filter_logs(bob_ai_wallet, "AgenticWithdrawal")[0]
        assert log_wallet.signer == bob_agent
        assert log_wallet.asset == _asset.address
        assert log_wallet.vaultToken == _vaultToken.address
        assert log_wallet.assetAmountReceived == amount_received
        assert log_wallet.vaultTokenAmountBurned == vault_token_burned
        assert log_wallet.legoId == _legoId
        assert log_wallet.legoAddr == lego_addr
        assert log_wallet.isSignerAgent == True
        assert log_wallet.usdValue == usd_value
        assert amount_received != 0
        assert vault_token_burned != 0

        if _amount == MAX_UINT256:
            _test(vault_token_burned, pre_user_vault_bal)
        else:
            _test(vault_token_burned, _amount)

        # lego addr should not have any leftover
        assert _asset.balanceOf(lego_addr) == pre_lego_asset_bal
        assert _vaultToken.balanceOf(lego_addr) == pre_lego_vault_bal

        # vault tokens
        _test(pre_user_vault_bal - vault_token_burned, _vaultToken.balanceOf(bob_ai_wallet.address))

        # asset amounts
        _test(pre_user_asset_bal + amount_received, _asset.balanceOf(bob_ai_wallet.address))

    yield testLegoWithdrawal


@pytest.fixture(scope="package")
def testLegoSwap(bob_ai_wallet, bob_agent, lego_registry, _test):
    def testLegoSwap(
        _legoId,
        _tokenIn,
        _tokenOut,
        _amountIn = MAX_UINT256,
        _minAmountOut = 0, 
    ):
        # pre balances
        pre_user_from_bal = _tokenIn.balanceOf(bob_ai_wallet)
        pre_user_to_bal = _tokenOut.balanceOf(bob_ai_wallet)

        lego_addr = lego_registry.getLegoAddr(_legoId)
        pre_lego_from_bal = _tokenIn.balanceOf(lego_addr)
        pre_lego_to_bal = _tokenOut.balanceOf(lego_addr)

        # swap
        fromSwapAmount, toAmount, usd_value = bob_ai_wallet.swapTokens(_legoId, _tokenIn.address, _tokenOut.address, _amountIn, _minAmountOut, sender=bob_agent)

        # event
        log_wallet = filter_logs(bob_ai_wallet, "AgenticSwap")[0]
        assert log_wallet.signer == bob_agent
        assert log_wallet.tokenIn == _tokenIn.address
        assert log_wallet.tokenOut == _tokenOut.address
        assert log_wallet.swapAmount == fromSwapAmount
        assert log_wallet.toAmount == toAmount
        assert log_wallet.legoId == _legoId
        assert log_wallet.legoAddr == lego_addr
        assert log_wallet.isSignerAgent == True
        assert log_wallet.usdValue == usd_value

        assert fromSwapAmount != 0
        assert toAmount != 0

        if _amountIn == MAX_UINT256:
            _test(fromSwapAmount, pre_user_from_bal)
        else:
            _test(fromSwapAmount, _amountIn)

        # lego addr should not have any leftover
        assert _tokenIn.balanceOf(lego_addr) == pre_lego_from_bal
        assert _tokenOut.balanceOf(lego_addr) == pre_lego_to_bal

        # to tokens
        _test(pre_user_to_bal + toAmount, _tokenOut.balanceOf(bob_ai_wallet.address))

        # from tokens
        _test(pre_user_from_bal - fromSwapAmount, _tokenIn.balanceOf(bob_ai_wallet.address))

    yield testLegoSwap