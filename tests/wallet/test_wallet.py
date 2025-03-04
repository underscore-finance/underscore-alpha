import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, CONVERSION_UINT256
from contracts.core import WalletFunds

#########
# Tests #
#########


def test_wallet_initialization(ai_wallet, ai_wallet_config, addy_registry, weth):
    assert ai_wallet.walletConfig() == ai_wallet_config.address
    assert ai_wallet.addyRegistry() == addy_registry.address
    assert ai_wallet.wethAddr() == weth.address
    assert ai_wallet.initialized()
    assert ai_wallet.apiVersion() == "0.0.1"


def test_deposit_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, bravo_token, bravo_token_erc4626_vault, mock_lego_bravo, alpha_token_erc4626_vault, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup agent permissions
    assert ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    assert ai_wallet_config.addLegoIdForAgent(agent, lego_id, sender=owner)

    # Transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # Test deposit by owner
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)
    log = filter_logs(ai_wallet, "UserWalletDeposit")[0]
    assert log.signer == owner
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address == vaultToken
    assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    assert log.vaultTokenAmountReceived == vaultTokenAmountReceived != 0
    assert log.refundAssetAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert not log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    wallet_bal = alpha_token_erc4626_vault.balanceOf(ai_wallet)
    assert wallet_bal == vaultTokenAmountReceived

    # Test deposit by agent
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=agent)
    log = filter_logs(ai_wallet, "UserWalletDeposit")[0]
    assert log.signer == agent
    assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    assert log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    new_wallet_bal = alpha_token_erc4626_vault.balanceOf(ai_wallet)
    assert new_wallet_bal == wallet_bal + vaultTokenAmountReceived

    # Test deposit permissions
    assert not ai_wallet_config.canAgentAccess(
        agent, DEPOSIT_UINT256, [bravo_token.address], [mock_lego_bravo.legoId()])

    with boa.reverts("agent not allowed"):
        ai_wallet.depositTokens(mock_lego_bravo.legoId(), bravo_token,
                                bravo_token_erc4626_vault, deposit_amount, sender=agent)

    with boa.reverts("no funds available"):
        ai_wallet.depositTokens(mock_lego_bravo.legoId(), bravo_token,
                                bravo_token_erc4626_vault, deposit_amount, sender=owner)


def test_withdrawal_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup agent permissions and initial deposit
    ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet_config.addLegoIdForAgent(agent, lego_id, sender=owner)
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=agent)
    assert assetAmountDeposited == deposit_amount

    # Get vault token balance
    assert alpha_token_erc4626_vault.address == vaultToken
    assert vaultTokenAmountReceived == alpha_token_erc4626_vault.balanceOf(ai_wallet)

    # Test withdrawal by owner
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=owner)
    log = filter_logs(ai_wallet, "UserWalletWithdrawal")[0]
    assert log.signer == owner
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountReceived == assetAmountReceived
    assert log.vaultTokenAmountBurned == vaultTokenAmountBurned
    assert log.refundVaultTokenAmount == 0
    assert log.legoId == lego_id
    assert not log.isSignerAgent

    wallet_bal = alpha_token.balanceOf(ai_wallet)
    assert wallet_bal == assetAmountReceived
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0

    # Setup for agent withdrawal
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=owner)

    # Test withdrawal by agent
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, vaultTokenAmountReceived, sender=agent)
    log = filter_logs(ai_wallet, "UserWalletWithdrawal")[0]
    assert log.signer == agent
    assert log.isSignerAgent
    assert log.vaultTokenAmountBurned == vaultTokenAmountBurned

    assert alpha_token.balanceOf(ai_wallet) == assetAmountReceived + wallet_bal
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0

    # Test withdrawal permissions
    with boa.reverts("agent not allowed"):
        ai_wallet.withdrawTokens(55, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, sender=agent)

    with boa.reverts("no funds available"):
        ai_wallet.withdrawTokens(lego_id, alpha_token, alpha_token_erc4626_vault, 0, sender=owner)


def test_rebalance_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    alt_lego_id = mock_lego_alpha_another.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup agent permissions
    ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet_config.addLegoIdForAgent(agent, lego_id, sender=owner)
    ai_wallet_config.addLegoIdForAgent(agent, alt_lego_id, sender=owner)

    # Initial deposit
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=owner)
    assert vaultToken == alpha_token_erc4626_vault.address

    # Test rebalance by owner
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.rebalance(
        lego_id, alpha_token, alpha_token_erc4626_vault, alt_lego_id, alpha_token_erc4626_vault_another, MAX_UINT256, sender=owner)
    log_withdrawal = filter_logs(ai_wallet, "UserWalletWithdrawal")[0]
    log_deposit = filter_logs(ai_wallet, "UserWalletDeposit")[0]

    assert log_withdrawal.signer == owner
    assert log_withdrawal.asset == alpha_token.address
    assert log_withdrawal.vaultToken == alpha_token_erc4626_vault.address == vaultToken
    assert log_withdrawal.assetAmountReceived != 0
    assert log_withdrawal.vaultTokenAmountBurned == origVaultTokenAmountReceived
    assert log_withdrawal.refundVaultTokenAmount == 0
    assert log_withdrawal.legoId == lego_id
    assert log_withdrawal.legoAddr == mock_lego_alpha.address
    assert not log_withdrawal.isSignerAgent

    assert log_deposit.signer == owner
    assert log_deposit.asset == alpha_token.address
    assert log_deposit.vaultToken == alpha_token_erc4626_vault_another.address == newVaultToken
    assert log_deposit.assetAmountDeposited == assetAmountDeposited
    assert log_deposit.vaultTokenAmountReceived == vaultTokenAmountReceived != 0
    assert log_deposit.refundAssetAmount == 0
    assert log_deposit.legoId == alt_lego_id
    assert log_deposit.legoAddr == mock_lego_alpha_another.address
    assert not log_deposit.isSignerAgent

    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(ai_wallet) == vaultTokenAmountReceived

    # Test rebalance by agent
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, alpha_token_erc4626_vault, deposit_amount, sender=owner)

    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.rebalance(
        lego_id, alpha_token, alpha_token_erc4626_vault, alt_lego_id, alpha_token_erc4626_vault_another, origVaultTokenAmountReceived, sender=agent)
    log_withdrawal = filter_logs(ai_wallet, "UserWalletWithdrawal")[0]
    log_deposit = filter_logs(ai_wallet, "UserWalletDeposit")[0]

    assert log_withdrawal.signer == agent
    assert log_withdrawal.isSignerAgent
    assert log_withdrawal.vaultTokenAmountBurned == origVaultTokenAmountReceived
    assert log_deposit.signer == agent
    assert log_deposit.isSignerAgent
    assert log_deposit.vaultTokenAmountReceived == vaultTokenAmountReceived

    # Test rebalance permissions
    with boa.reverts("agent not allowed"):
        ai_wallet.rebalance(55, alpha_token, alpha_token_erc4626_vault, alt_lego_id,
                            alpha_token_erc4626_vault_another, vaultTokenAmountReceived, sender=agent)


def test_fund_transfers(ai_wallet, ai_wallet_config, owner, agent, alpha_token, alpha_token_whale, sally, bob):
    transfer_amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup
    ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)
    alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)

    # Test transfer by owner
    assert ai_wallet.transferFunds(sally, MAX_UINT256, alpha_token, sender=owner)
    log = filter_logs(ai_wallet, "UserWalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == alpha_token.address
    assert log.amount == transfer_amount
    assert not log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == transfer_amount

    # Test transfer by agent
    alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)
    assert ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=agent)
    log = filter_logs(ai_wallet, "UserWalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == alpha_token.address
    assert log.amount == transfer_amount
    assert log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == transfer_amount * 2

    # transfer eth
    amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, amount)
    assert ai_wallet.transferFunds(sally, sender=agent)
    log = filter_logs(ai_wallet, "UserWalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == ZERO_ADDRESS
    assert log.amount == amount
    assert log.isSignerAgent

    # Test whitelist functionality
    assert not ai_wallet_config.isRecipientAllowed(bob)
    ai_wallet_config.setWhitelistAddr(bob, True, sender=owner)
    assert ai_wallet_config.isRecipientAllowed(bob)

    # Test transfer restrictions
    with boa.reverts("recipient not allowed"):
        ai_wallet.transferFunds(alpha_token_whale, transfer_amount, alpha_token, sender=owner)

    with boa.reverts("no funds available"):
        ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=owner)


# Base WETH tests


@pytest.base
def test_eth_to_weth_deposit(ai_wallet, ai_wallet_config, agent, lego_aave_v3, getTokenAndWhale, governor):
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, eth_amount)

    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    weth, _ = getTokenAndWhale("weth")
    if lego_aave_v3.vaultToAsset(vault_token) != weth.address:
        assert lego_aave_v3.addAssetOpportunity(weth, sender=governor)

    assert ai_wallet.wethAddr() == weth.address
    assert ai_wallet_config.canAgentAccess(agent, CONVERSION_UINT256, [weth.address], [lego_id])

    # Test ETH to WETH conversion by agent
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(
        MAX_UINT256, lego_id, vault_token, sender=agent)

    log = filter_logs(ai_wallet, "UserWalletEthConvertedToWeth")[0]
    assert log.signer == agent
    assert log.amount == eth_amount
    assert log.paidEth == 0
    assert log.weth == weth.address
    assert log.isSignerAgent

    assert assetAmountDeposited == eth_amount
    assert vaultToken == vault_token.address
    assert vault_token.balanceOf(ai_wallet.address) == vaultTokenAmountReceived


@pytest.base
def test_payable_eth_to_weth_deposit(owner, ai_wallet, lego_aave_v3, getTokenAndWhale, governor):
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(owner, eth_amount + EIGHTEEN_DECIMALS)

    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    weth, _ = getTokenAndWhale("weth")
    if lego_aave_v3.vaultToAsset(vault_token) != weth.address:
        assert lego_aave_v3.addAssetOpportunity(weth, sender=governor)

    # Test ETH to WETH conversion by owner, and payable
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(
        MAX_UINT256, lego_id, vault_token, value=eth_amount, sender=owner)

    log = filter_logs(ai_wallet, "UserWalletEthConvertedToWeth")[0]
    assert log.signer == owner
    assert log.amount == eth_amount
    assert log.paidEth == eth_amount
    assert log.weth == weth.address
    assert not log.isSignerAgent

    assert assetAmountDeposited == eth_amount
    assert vaultToken == vault_token.address
    assert vault_token.balanceOf(ai_wallet.address) == vaultTokenAmountReceived


@pytest.base
def test_weth_to_eth_withdraw(
    getTokenAndWhale,
    ai_wallet,
    ai_wallet_config,
    agent,
    lego_aave_v3,
    _test,
    owner,
    governor,
):
    # setup
    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    asset, whale = getTokenAndWhale("weth")
    asset.transfer(ai_wallet.address, 5 * (10 ** asset.decimals()), sender=whale)
    if lego_aave_v3.vaultToAsset(vault_token) != asset.address:
        assert lego_aave_v3.addAssetOpportunity(asset, sender=governor)

    deposit_amount, _, vault_tokens_received, usd_value = ai_wallet.depositTokens(
        lego_id, asset, vault_token, MAX_UINT256, sender=agent)
    assert deposit_amount != 0 and vault_tokens_received != 0

    assert ai_wallet.wethAddr() == asset.address
    assert ai_wallet_config.canAgentAccess(agent, CONVERSION_UINT256, [asset.address], [lego_id])

    # convert weth to eth
    amount = ai_wallet.convertWethToEth(MAX_UINT256, owner, lego_id, vault_token, sender=agent)
    assert amount != 0

    log = filter_logs(ai_wallet, "UserWalletWethConvertedToEth")[0]
    assert log.signer == agent
    assert log.amount == amount
    assert log.weth == asset.address
    assert log.isSignerAgent

    # ai wallet is zero
    assert asset.balanceOf(ai_wallet.address) == 0
    assert boa.env.get_balance(ai_wallet.address) == 0

    # check owner
    _test(boa.env.get_balance(owner), amount)
    _test(deposit_amount, amount)


@pytest.base
def test_eth_weth_conversion_edge_cases(ai_wallet, ai_wallet_config, owner, agent, lego_aave_v3, getTokenAndWhale, sally, governor):
    """Test edge cases for ETH/WETH conversion operations"""
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, eth_amount)

    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    weth, weth_whale = getTokenAndWhale("weth")
    if lego_aave_v3.vaultToAsset(vault_token) != weth.address:
        assert lego_aave_v3.addAssetOpportunity(weth, sender=governor)

    assert ai_wallet.wethAddr() == weth.address
    assert ai_wallet_config.canAgentAccess(agent, CONVERSION_UINT256, [weth.address], [lego_id])

    # Test converting 0 ETH
    # print("agent settings 1: ", ai_wallet.agentSettings(agent))
    # assert ai_wallet.canAgentPerformAction(agent, CONVERSION_UINT256)
    with boa.reverts("nothing to convert"):
        ai_wallet.convertEthToWeth(0, sender=agent)

    # Test converting more than available balance
    amount, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(eth_amount * 2, sender=agent)
    assert amount == eth_amount  # Should only convert available balance

    # Test non-agent cannot convert when agent permissions set
    allowed_actions = (True, True, False, False, True, False, False, False, False, False, False, False)  # No conversion permission
    ai_wallet_config.modifyAllowedActions(agent, allowed_actions, sender=owner)
    with boa.reverts("agent not allowed"):
        ai_wallet.convertEthToWeth(eth_amount, sender=agent)

    # Test WETH to ETH with zero amount
    ai_wallet_config.modifyAllowedActions(agent, sender=owner)
    # print("agent settings 2: ", ai_wallet.agentSettings(agent))
    # assert not ai_wallet.canAgentPerformAction(agent, CONVERSION_UINT256)
    with boa.reverts("nothing to convert"):
        ai_wallet.convertWethToEth(0, sender=agent)

    # Test WETH to ETH with more than balance
    amount = ai_wallet.convertWethToEth(eth_amount * 2, sender=agent)
    assert amount == eth_amount  # Should only convert available balance

    # Test WETH to ETH with invalid recipient
    weth.transfer(ai_wallet, eth_amount, sender=weth_whale)
    with boa.reverts("recipient not allowed"):
        ai_wallet.convertWethToEth(eth_amount, sally, sender=agent)

    # Test WETH to ETH with withdrawal from vault
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, weth, vault_token, eth_amount, sender=agent)

    amount = ai_wallet.convertWethToEth(MAX_UINT256, owner, lego_id, vault_token, sender=agent)
    assert amount == eth_amount
    assert weth.balanceOf(ai_wallet) == 0
    assert vault_token.balanceOf(ai_wallet) == 0


@pytest.base
def test_eth_weth_conversion_with_fees(ai_wallet, owner, agent, lego_aave_v3, getTokenAndWhale, price_sheets, governor, oracle_registry, oracle_chainlink):
    """Test ETH/WETH conversion with transaction fees"""
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, eth_amount)

    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    weth, _ = getTokenAndWhale("weth")
    if lego_aave_v3.vaultToAsset(vault_token) != weth.address:
        assert lego_aave_v3.addAssetOpportunity(weth, sender=governor)

    usdc, usdc_whale = getTokenAndWhale("usdc")
    usdc.transfer(ai_wallet, 1000 * (10 ** usdc.decimals()), sender=usdc_whale)
    oracle_chainlink.setChainlinkFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)
    assert oracle_registry.getPrice(usdc.address) != 0

    # Set conversion fees
    assert price_sheets.setProtocolTxPriceSheet(
        50,     # depositFee (0.50%)
        100,    # withdrawalFee (1.00%)
        150,    # rebalanceFee (1.50%)
        200,    # transferFee (2.00%)
        250,    # swapFee (2.50%)
        300,    # addLiqFee (3.00%)
        350,    # removeLiqFee (3.50%)
        400,    # claimRewardsFee (4.00%)
        450,    # borrowFee (4.50%)
        500,    # repayFee (5.00%)
        sender=governor
    )

    weth, weth_whale = getTokenAndWhale("weth")

    # Test ETH to WETH conversion with deposit fees
    amount, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(
        eth_amount, lego_id, vault_token, sender=agent)

    log = filter_logs(ai_wallet, "UserWalletTransactionFeePaid")[0]
    assert log.action == DEPOSIT_UINT256
    assert log.asset == vault_token.address
    assert log.amount != 0

    # Test WETH to ETH conversion with withdrawal and transfer fees
    amount = ai_wallet.convertWethToEth(MAX_UINT256, owner, lego_id, vault_token, sender=agent)

    logs = filter_logs(ai_wallet, "UserWalletTransactionFeePaid")
    assert len(logs) == 1  # Should have withdrawal and transfer fees
    assert logs[0].action == WITHDRAWAL_UINT256
