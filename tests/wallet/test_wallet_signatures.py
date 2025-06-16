import pytest
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS, DEPOSIT_UINT256, WITHDRAWAL_UINT256
from utils.BluePrint import CORE_TOKENS


#########
# Tests #
#########


def test_deposit_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signDeposit):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # signature
    signature = signDeposit(special_agent, special_ai_wallet, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, MAX_UINT256)

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = special_agent.depositTokens(
        special_ai_wallet, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, signature, sender=broadcaster)

    # deposit
    log = filter_logs(special_agent, "UserWalletDeposit")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert assetAmountDeposited == deposit_amount
    assert alpha_token.balanceOf(special_ai_wallet) == 0
    assert alpha_token_erc4626_vault.balanceOf(special_ai_wallet) == vaultTokenAmountReceived


def test_withdraw_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signWithdrawal):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # deposit
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = special_ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=special_agent.address)

    # signature
    signature = signWithdrawal(special_agent, special_ai_wallet, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, MAX_UINT256)

    # withdrawal
    assetAmountReceived, vaultTokenAmountBurned, usdValue = special_agent.withdrawTokens(
        special_ai_wallet, lego_id, alpha_token, alpha_token_erc4626_vault.address, MAX_UINT256, True, signature, sender=broadcaster)

    # withdrawal
    log = filter_logs(special_agent, "UserWalletWithdrawal")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert alpha_token.balanceOf(special_ai_wallet) == assetAmountDeposited == assetAmountReceived
    assert alpha_token_erc4626_vault.balanceOf(special_ai_wallet) == 0


def test_rebalance_with_signature(special_ai_wallet, owner, broadcaster, special_agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale, signRebalance):
    # setup
    lego_id = mock_lego_alpha.legoId()
    alt_lego_id = mock_lego_alpha_another.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # deposit
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived, usdValue = special_ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=owner)

    # signature
    signature = signRebalance(special_agent, special_ai_wallet, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, alt_lego_id, alpha_token_erc4626_vault_another.address, MAX_UINT256, True)

    # rebalance
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = special_agent.rebalance(
        special_ai_wallet, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, alt_lego_id, alpha_token_erc4626_vault_another.address, MAX_UINT256, True, signature, sender=broadcaster)
    
    # rebalance
    log = filter_logs(special_agent, "UserWalletWithdrawal")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    log = filter_logs(special_agent, "UserWalletDeposit")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert alpha_token_erc4626_vault.balanceOf(special_ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(special_ai_wallet) == vaultTokenAmountReceived


def test_swap_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signSwap, bravo_token, bravo_token_whale):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # put amount for swap
    bravo_token.transfer(mock_lego_alpha.address, deposit_amount, sender=bravo_token_whale)

    instruction = (
        lego_id,
        deposit_amount,
        0,
        [alpha_token, bravo_token],
        [alpha_token]
    )

    # signature
    signature = signSwap(special_agent, special_ai_wallet, [instruction])

    # swap
    actualSwapAmount, toAmount, usdValue = special_agent.swapTokens(special_ai_wallet, [instruction], signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletSwap")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent

    assert actualSwapAmount == deposit_amount
    assert alpha_token.balanceOf(special_ai_wallet) == 0
    assert bravo_token.balanceOf(special_ai_wallet) == toAmount == deposit_amount


def test_borrow_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, broadcaster, signBorrow):
    lego_id = mock_lego_alpha.legoId()

    # signature
    signature = signBorrow(special_agent, special_ai_wallet, lego_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS)

    # borrow
    special_agent.borrow(special_ai_wallet, lego_id, alpha_token.address, 100 * EIGHTEEN_DECIMALS, signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletBorrow")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_repay_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token_whale, alpha_token, broadcaster, signRepay):
    lego_id = mock_lego_alpha.legoId()
    repay_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, repay_amount, sender=alpha_token_whale)

    # signature
    signature = signRepay(special_agent, special_ai_wallet, lego_id, alpha_token.address, repay_amount)

    # repay
    special_agent.repayDebt(special_ai_wallet, lego_id, alpha_token.address, repay_amount, signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletRepayDebt")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_claim_rewards_with_signature(special_ai_wallet, special_agent, mock_lego_alpha, alpha_token, broadcaster, signClaimRewards):
    lego_id = mock_lego_alpha.legoId()
    data = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # signature
    signature = signClaimRewards(special_agent, special_ai_wallet, lego_id, alpha_token.address, alpha_token.address, 100 * EIGHTEEN_DECIMALS, data)

    # claim rewards
    special_agent.claimRewards(special_ai_wallet, lego_id, alpha_token.address, alpha_token.address, 100 * EIGHTEEN_DECIMALS, data, signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletRewardsClaimed")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_transfer_with_signature(special_ai_wallet, special_agent, owner, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signTransfer):
    # setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # signature
    signature = signTransfer(special_agent, special_ai_wallet, owner, MAX_UINT256, alpha_token.address)

    # transfer
    special_agent.transferFunds(special_ai_wallet, owner, MAX_UINT256, alpha_token.address, signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletFundsTransferred")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_convert_eth_to_weth_with_signature(special_ai_wallet, special_agent, broadcaster, signEthToWeth):
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(special_ai_wallet.address, eth_amount)

    # signature
    signature = signEthToWeth(special_agent, special_ai_wallet, eth_amount, 0, ZERO_ADDRESS)

    # eth to weth
    special_agent.convertEthToWeth(special_ai_wallet, eth_amount, 0, ZERO_ADDRESS, signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletEthConvertedToWeth")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


@pytest.base
def test_weth_to_eth_with_signature(special_ai_wallet, getTokenAndWhale, special_agent, broadcaster, signWethToEth):
    weth, weth_token_whale = getTokenAndWhale("weth")
    weth_amount = 1 * EIGHTEEN_DECIMALS
    weth.transfer(special_ai_wallet, weth_amount, sender=weth_token_whale)

    # signature
    signature = signWethToEth(special_agent, special_ai_wallet, weth_amount, ZERO_ADDRESS, 0, ZERO_ADDRESS)

    # weth to eth
    special_agent.convertWethToEth(special_ai_wallet, weth_amount, ZERO_ADDRESS, 0, ZERO_ADDRESS, signature, sender=broadcaster)
    
    log = filter_logs(special_agent, "UserWalletWethConvertedToEth")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_add_liquidity_with_signature(special_ai_wallet, special_agent, bravo_token, bravo_token_whale, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, signAddLiquidity):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    bravo_token.transfer(special_ai_wallet, deposit_amount, sender=bravo_token_whale)

    # signature
    signature = signAddLiquidity(special_agent, special_ai_wallet, lego_id, alpha_token.address, bravo_token.address)

    # add liquidity
    special_agent.addLiquidity(special_ai_wallet, lego_id, ZERO_ADDRESS, 0, ZERO_ADDRESS, alpha_token.address, bravo_token.address, MAX_UINT256, MAX_UINT256, 1, 1, 1, 1, 1, signature, sender=broadcaster)

    log = filter_logs(special_agent, "UserWalletLiquidityAdded")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_remove_liquidity_with_signature(special_ai_wallet, special_agent, bravo_token, mock_lego_alpha, charlie_token, alpha_token, alpha_token_whale, broadcaster, signRemoveLiquidity):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # signature
    signature = signRemoveLiquidity(special_agent, special_ai_wallet, lego_id, alpha_token.address, bravo_token.address, charlie_token.address)

    # remove liquidity
    special_agent.removeLiquidity(special_ai_wallet, lego_id, ZERO_ADDRESS, 0, alpha_token.address, bravo_token.address, charlie_token.address, MAX_UINT256, 0, 0, signature, sender=broadcaster)

    log = filter_logs(special_agent, "UserWalletLiquidityRemoved")[0]
    assert log.signer == special_agent.address
    assert log.isSignerAgent


def test_signature_expiration_and_reuse(special_agent, special_ai_wallet, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, broadcaster, signDeposit):
    """Test signature expiration and reuse prevention"""
    # Setup
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)

    # Test expired signature
    expired_signature = signDeposit(
        special_agent, 
        special_ai_wallet,
        lego_id, 
        alpha_token.address, 
        alpha_token_erc4626_vault.address,
        MAX_UINT256, 
        1,  # Set expiration to past block
    )

    with boa.reverts("signature expired"):
        special_agent.depositTokens(
            special_ai_wallet,
            lego_id, 
            alpha_token, 
            alpha_token_erc4626_vault, 
            MAX_UINT256, 
            expired_signature, 
            sender=broadcaster
        )

    # Test signature reuse
    valid_signature = signDeposit(
        special_agent, 
        special_ai_wallet,
        lego_id, 
        alpha_token.address, 
        alpha_token_erc4626_vault.address,
        MAX_UINT256, 
    )

    # First use should succeed
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue =  special_agent.depositTokens(
        special_ai_wallet,
        lego_id, 
        alpha_token, 
        alpha_token_erc4626_vault, 
        MAX_UINT256, 
        valid_signature, 
        sender=broadcaster
    )
    assert assetAmountDeposited == deposit_amount

    # Second use should fail
    alpha_token.transfer(special_ai_wallet, deposit_amount, sender=alpha_token_whale)
    with boa.reverts("signature already used"):
        special_agent.depositTokens(
            special_ai_wallet,
            lego_id, 
            alpha_token, 
            alpha_token_erc4626_vault, 
            MAX_UINT256, 
            valid_signature, 
            sender=broadcaster
        )


def test_batch_actions_with_signature(special_ai_wallet, special_agent, createActionInstruction, mock_lego_alpha, alpha_token, alpha_token_whale, broadcaster, alpha_token_erc4626_vault, signBatchAction):
    lego_id = mock_lego_alpha.legoId()
    amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, amount, sender=alpha_token_whale)

    # create instructions
    instructions = [
        createActionInstruction(DEPOSIT_UINT256, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, amount),
        createActionInstruction(WITHDRAWAL_UINT256, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, amount),
    ]

    # signature
    signature = signBatchAction(special_agent, special_ai_wallet, instructions)

    # batch actions
    special_agent.performBatchActions(special_ai_wallet, instructions, signature, sender=broadcaster)

    log1 = filter_logs(special_agent, "UserWalletDeposit")[0]
    log2 = filter_logs(special_agent, "UserWalletWithdrawal")[0]

    assert log1.signer == special_agent.address
    assert log1.isSignerAgent

    assert log2.signer == special_agent.address
    assert log2.isSignerAgent


@pytest.base
def test_batch_action_signature_withdraw_swap(special_ai_wallet, broadcaster, signBatchAction, special_agent, owner, lego_aave_v3, createActionInstruction, oracle_chainlink, getTokenAndWhale, governor, lego_uniswap_v2, lego_uniswap_v3, fork, createSwapActionInstruction):

    # usdc setup
    usdc, usdc_whale = getTokenAndWhale("usdc")
    usdc_amount = 10_000 * (10 ** usdc.decimals())
    usdc.transfer(special_ai_wallet, usdc_amount, sender=usdc_whale)
    assert oracle_chainlink.setChainlinkFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)

    # deposit usdc into aave v3
    aave_usdc = boa.from_etherscan("0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB")
    if lego_aave_v3.vaultToAsset(aave_usdc) == ZERO_ADDRESS:
        lego_aave_v3.addAssetOpportunity(usdc.address, sender=governor)
    special_ai_wallet.depositTokens(lego_aave_v3.legoId(), usdc.address, aave_usdc, usdc_amount, sender=owner)

    # weth setup
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"], name="weth token")
    univ2_weth_usdc_pool = "0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C"

    # virtual setup
    virtual = boa.from_etherscan(CORE_TOKENS[fork]["VIRTUAL"], name="virtual token")
    univ2_weth_virtual_pool = "0xE31c372a7Af875b3B5E0F3713B17ef51556da667"
    univ3_weth_virtual_pool = "0x9c087Eb773291e50CF6c6a90ef0F4500e349B903"

    # cbbtc setup
    cbbtc = boa.from_etherscan(CORE_TOKENS[fork]["CBBTC"], name="cbbtc token")
    weth_cbbtc_pool = "0x8c7080564B5A792A33Ef2FD473fbA6364d5495e5"

    # usdc -> weth -> virtual
    first_instruction = (
        lego_uniswap_v2.legoId(),
        usdc_amount,
        0,
        [usdc, weth, virtual],
        [univ2_weth_usdc_pool, univ2_weth_virtual_pool]
    )

    # virtual -> weth -> cbbtc
    second_instruction = (
        lego_uniswap_v3.legoId(),
        MAX_UINT256,
        0,
        [virtual, weth, cbbtc],
        [univ3_weth_virtual_pool, weth_cbbtc_pool]
    )

    # create instructions
    instructions = [
        createActionInstruction(WITHDRAWAL_UINT256, lego_aave_v3.legoId(), usdc.address, aave_usdc, usdc_amount),
        createSwapActionInstruction([first_instruction, second_instruction]),
    ]

    # signature
    signature = signBatchAction(special_agent, special_ai_wallet, instructions)

    special_agent.performBatchActions(special_ai_wallet, instructions, signature, sender=broadcaster)

    log1 = filter_logs(special_agent, "UserWalletWithdrawal")[0]
    log2 = filter_logs(special_agent, "UserWalletSwap")[0]

    assert log1.signer == special_agent.address
    assert log1.isSignerAgent

    assert log2.signer == special_agent.address
    assert log2.isSignerAgent

    assert cbbtc.balanceOf(special_ai_wallet) != 0
    assert usdc.balanceOf(special_ai_wallet) == 0
    assert aave_usdc.balanceOf(special_ai_wallet) == 0