import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, CONVERSION_UINT256


#########
# Tests #
#########


def test_wallet_initialization(ai_wallet, owner, agent, addy_registry, weth):
    assert ai_wallet.owner() == owner
    assert ai_wallet.addyRegistry() == addy_registry.address
    assert ai_wallet.wethAddr() == weth.address
    assert ai_wallet.initialized()
    assert ai_wallet.apiVersion() == "0.0.1"

    # Check initial agent settings
    agent_info = ai_wallet.agentSettings(agent)
    assert agent_info.isActive
    assert len(agent_info.allowedAssets) == 0
    assert len(agent_info.allowedLegoIds) == 0


# agent management


def test_agent_management(ai_wallet, owner, agent, mock_lego_alpha, mock_lego_bravo, bravo_token, alpha_token, sally):
    # Test adding assets and lego ids for agent
    lego_id = mock_lego_alpha.legoId()
    lego_id_another = mock_lego_bravo.legoId()

    # Add asset for agent
    assert ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    log = filter_logs(ai_wallet, "AssetAddedToAgent")[0]
    assert log.agent == agent
    assert log.asset == alpha_token.address

    # Add lego id for agent
    assert ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
    log = filter_logs(ai_wallet, "LegoIdAddedToAgent")[0]
    assert log.agent == agent
    assert log.legoId == lego_id

    # Verify agent settings
    agent_info = ai_wallet.agentSettings(agent)
    assert agent_info.isActive
    assert alpha_token.address in agent_info.allowedAssets
    assert lego_id in agent_info.allowedLegoIds

    # Test modifying agent settings
    new_assets = [alpha_token.address, bravo_token.address]
    new_lego_ids = [lego_id, lego_id_another]
    assert ai_wallet.addOrModifyAgent(agent, new_assets, new_lego_ids, sender=owner)
    log = filter_logs(ai_wallet, "AgentModified")[0]
    assert log.agent == agent
    assert log.allowedAssets == 2
    assert log.allowedLegoIds == 2

    # Verify agent settings
    agent_info = ai_wallet.agentSettings(agent)
    assert agent_info.isActive
    assert alpha_token.address in agent_info.allowedAssets
    assert lego_id in agent_info.allowedLegoIds
    assert bravo_token.address in agent_info.allowedAssets
    assert lego_id_another in agent_info.allowedLegoIds

    # Test adding new agent
    assert ai_wallet.addOrModifyAgent(sally, new_assets, new_lego_ids, sender=owner)
    log = filter_logs(ai_wallet, "AgentAdded")[0]
    assert log.agent == sally
    assert log.allowedAssets == 2
    assert log.allowedLegoIds == 2

    # Verify agent settings
    agent_info = ai_wallet.agentSettings(sally)
    assert agent_info.isActive
    assert alpha_token.address in agent_info.allowedAssets
    assert lego_id in agent_info.allowedLegoIds
    assert bravo_token.address in agent_info.allowedAssets
    assert lego_id_another in agent_info.allowedLegoIds

    # Test disabling agent
    assert ai_wallet.disableAgent(agent, sender=owner)
    log = filter_logs(ai_wallet, "AgentDisabled")[0]
    assert log.agent == agent
    assert log.prevAllowedAssets == 2
    assert log.prevAllowedLegoIds == 2

    # Verify agent is disabled
    agent_info = ai_wallet.agentSettings(agent)
    assert not agent_info.isActive


# agent management permissions


def test_agent_management_permissions(ai_wallet, owner, agent, alpha_token, sally, mock_lego_alpha):
    with boa.reverts(("no perms")):
        ai_wallet.addAssetForAgent(agent, alpha_token, sender=sally)

    with boa.reverts("no perms"):
        ai_wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=sally)

    with boa.reverts("no perms"):
        ai_wallet.addOrModifyAgent(agent, [alpha_token], [mock_lego_alpha.legoId()], sender=sally)

    with boa.reverts("no perms"):
        ai_wallet.disableAgent(agent, sender=sally)

    # Test invalid agent address
    with boa.reverts("invalid agent"):
        ai_wallet.addOrModifyAgent(ZERO_ADDRESS, [], [], sender=owner)

    # Test owner cannot be agent
    with boa.reverts("agent cannot be owner"):
        ai_wallet.addOrModifyAgent(owner, [], [], sender=owner)

    # Test disabling non-active agent
    with boa.reverts("agent not active"):
        ai_wallet.disableAgent(sally, sender=owner)

    # Test adding duplicate asset
    assert ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    with boa.reverts("asset already saved"):
        ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)

    # Test adding duplicate lego id
    assert ai_wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    with boa.reverts("lego id already saved"):
        ai_wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)


def test_deposit_operations(ai_wallet, owner, agent, mock_lego_alpha, alpha_token, bravo_token, bravo_token_whale, bravo_token_erc4626_vault, mock_lego_bravo, alpha_token_erc4626_vault, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup agent permissions
    assert ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    assert ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)

    # Transfer tokens to wallet
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assert alpha_token.balanceOf(ai_wallet) == deposit_amount

    # Test deposit by owner
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=owner)
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
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
        lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.signer == agent
    assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    assert log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    new_wallet_bal = alpha_token_erc4626_vault.balanceOf(ai_wallet)
    assert new_wallet_bal == wallet_bal + vaultTokenAmountReceived

    # Test deposit with transfer
    alpha_token.approve(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokensWithTransfer(
        lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=alpha_token_whale)
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.signer == alpha_token_whale
    assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    assert not log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == new_wallet_bal + vaultTokenAmountReceived

    # Test deposit permissions
    assert not ai_wallet.canAgentAccess(agent, DEPOSIT_UINT256, [bravo_token.address], [mock_lego_bravo.legoId()])

    with boa.reverts("agent not allowed"):
        ai_wallet.depositTokens(mock_lego_bravo.legoId(), bravo_token, deposit_amount,
                                bravo_token_erc4626_vault, sender=agent)

    with boa.reverts("nothing to transfer"):
        ai_wallet.depositTokens(mock_lego_bravo.legoId(), bravo_token, deposit_amount,
                                bravo_token_erc4626_vault, sender=owner)


def test_withdrawal_operations(ai_wallet, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup agent permissions and initial deposit
    ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == deposit_amount

    # Get vault token balance
    assert alpha_token_erc4626_vault.address == vaultToken
    assert vaultTokenAmountReceived == alpha_token_erc4626_vault.balanceOf(ai_wallet)

    # Test withdrawal by owner
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=owner)
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
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
        lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)

    # Test withdrawal by agent
    assetAmountReceived, vaultTokenAmountBurned, usdValue = ai_wallet.withdrawTokens(
        lego_id, alpha_token, vaultTokenAmountReceived, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.signer == agent
    assert log.isSignerAgent
    assert log.vaultTokenAmountBurned == vaultTokenAmountBurned

    assert alpha_token.balanceOf(ai_wallet) == assetAmountReceived + wallet_bal
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0

    # Test withdrawal permissions
    with boa.reverts("agent not allowed"):
        ai_wallet.withdrawTokens(55, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=agent)

    with boa.reverts("nothing to withdraw"):
        ai_wallet.withdrawTokens(lego_id, alpha_token, 0, alpha_token_erc4626_vault, sender=owner)


def test_rebalance_operations(ai_wallet, owner, agent, mock_lego_alpha, mock_lego_alpha_another, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    alt_lego_id = mock_lego_alpha_another.legoId()
    deposit_amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup agent permissions
    ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
    ai_wallet.addLegoIdForAgent(agent, alt_lego_id, sender=owner)

    # Initial deposit
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived, usdValue = ai_wallet.depositTokens(
        lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)
    assert vaultToken == alpha_token_erc4626_vault.address

    # Test rebalance by owner
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.rebalance(
        lego_id, alt_lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, sender=owner)
    log_withdrawal = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    log_deposit = filter_logs(ai_wallet, "AgenticDeposit")[0]

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
        lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)

    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = ai_wallet.rebalance(
        lego_id, alt_lego_id, alpha_token, origVaultTokenAmountReceived, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, sender=agent)
    log_withdrawal = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    log_deposit = filter_logs(ai_wallet, "AgenticDeposit")[0]

    assert log_withdrawal.signer == agent
    assert log_withdrawal.isSignerAgent
    assert log_withdrawal.vaultTokenAmountBurned == origVaultTokenAmountReceived
    assert log_deposit.signer == agent
    assert log_deposit.isSignerAgent
    assert log_deposit.vaultTokenAmountReceived == vaultTokenAmountReceived

    # Test rebalance permissions
    with boa.reverts("agent not allowed"):
        ai_wallet.rebalance(55, alt_lego_id, alpha_token, vaultTokenAmountReceived,
                            alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, sender=agent)


def test_fund_transfers(ai_wallet, owner, agent, alpha_token, alpha_token_whale, sally, bob):
    transfer_amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup
    ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet.setWhitelistAddr(sally, True, sender=owner)
    alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)

    # Test transfer by owner
    assert ai_wallet.transferFunds(sally, MAX_UINT256, alpha_token, sender=owner)
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == alpha_token.address
    assert log.amount == transfer_amount
    assert not log.isSignerAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == transfer_amount

    # Test transfer by agent
    alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)
    assert ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=agent)
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
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
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == ZERO_ADDRESS
    assert log.amount == amount
    assert log.isSignerAgent

    # Test whitelist functionality
    assert not ai_wallet.isRecipientAllowed(bob)
    ai_wallet.setWhitelistAddr(bob, True, sender=owner)
    assert ai_wallet.isRecipientAllowed(bob)

    # Test transfer restrictions
    with boa.reverts("recipient not allowed"):
        ai_wallet.transferFunds(alpha_token_whale, transfer_amount, alpha_token, sender=owner)

    with boa.reverts("nothing to transfer"):
        ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=owner)


def test_batch_actions(ai_wallet, owner, agent, mock_lego_alpha, alpha_token, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale, sally):
    lego_id = mock_lego_alpha.legoId()
    alt_lego_id = mock_lego_alpha_another.legoId()
    amount = 1_000 * EIGHTEEN_DECIMALS

    # Setup agent permissions
    ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
    ai_wallet.addLegoIdForAgent(agent, alt_lego_id, sender=owner)
    ai_wallet.setWhitelistAddr(sally, True, sender=owner)

    # Transfer tokens to wallet
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)

    # Create batch instructions
    instructions = [
        # Deposit
        (DEPOSIT_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),  # ActionType.DEPOSIT = 0
        # Withdrawal
        (WITHDRAWAL_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, amount // 2, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),  # ActionType.WITHDRAWAL = 1
        # Rebalance
        (REBALANCE_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS, alt_lego_id, alpha_token_erc4626_vault_another, ZERO_ADDRESS, 0),  # ActionType.REBALANCE = 2
        # Transfer
        (TRANSFER_UINT256, 0, alpha_token, ZERO_ADDRESS, MAX_UINT256, sally, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0),  # ActionType.TRANSFER = 3
    ]

    # Test batch actions by owner
    assert ai_wallet.performManyActions(instructions, sender=agent)

    # deposit
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.signer == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountDeposited == amount
    assert log.vaultTokenAmountReceived == amount
    assert log.refundAssetAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert log.isSignerAgent

    # withdrawal
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.signer == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountReceived == amount // 2
    assert log.vaultTokenAmountBurned == amount // 2
    assert log.refundVaultTokenAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert log.isSignerAgent

    # rebalance
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[1]
    assert log.signer == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountReceived == amount // 2
    assert log.vaultTokenAmountBurned == amount // 2
    assert log.refundVaultTokenAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert log.isSignerAgent

    log = filter_logs(ai_wallet, "AgenticDeposit")[1]
    assert log.signer == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault_another.address
    assert log.assetAmountDeposited == amount // 2
    assert log.vaultTokenAmountReceived == amount // 2
    assert log.refundAssetAmount == 0
    assert log.legoId == alt_lego_id
    assert log.legoAddr == mock_lego_alpha_another.address
    assert log.isSignerAgent

    # transfer
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == alpha_token.address
    assert log.amount == amount // 2
    assert log.isSignerAgent

    # data
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == amount // 2

    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(ai_wallet) == amount // 2


# Base WETH tests


@pytest.base
def test_eth_to_weth_deposit(ai_wallet, agent, lego_aave_v3, getTokenAndWhale):
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(ai_wallet.address, eth_amount)

    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    weth, _ = getTokenAndWhale("weth")

    assert ai_wallet.wethAddr() == weth.address
    assert ai_wallet.canAgentAccess(agent, CONVERSION_UINT256, [weth.address], [lego_id])

    # Test ETH to WETH conversion by agent
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(
        MAX_UINT256, lego_id, vault_token, sender=agent)

    log = filter_logs(ai_wallet, "EthConvertedToWeth")[0]
    assert log.signer == agent
    assert log.amount == eth_amount
    assert log.paidEth == 0
    assert log.weth == weth.address
    assert log.isSignerAgent

    assert assetAmountDeposited == eth_amount
    assert vaultToken == vault_token.address
    assert vault_token.balanceOf(ai_wallet.address) == vaultTokenAmountReceived


@pytest.base
def test_payable_eth_to_weth_deposit(owner, ai_wallet, lego_aave_v3, getTokenAndWhale):
    eth_amount = 5 * EIGHTEEN_DECIMALS
    boa.env.set_balance(owner, eth_amount + EIGHTEEN_DECIMALS)

    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    weth, _ = getTokenAndWhale("weth")

    # Test ETH to WETH conversion by owner, and payable
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(
        MAX_UINT256, lego_id, vault_token, value=eth_amount, sender=owner)

    log = filter_logs(ai_wallet, "EthConvertedToWeth")[0]
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
    agent,
    lego_aave_v3,
    _test,
    owner,
):
    # setup
    lego_id = lego_aave_v3.legoId()
    vault_token = boa.from_etherscan("0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", name="base_weth_aave_v3_vault")
    asset, whale = getTokenAndWhale("weth")
    asset.transfer(ai_wallet.address, 5 * (10 ** asset.decimals()), sender=whale)

    deposit_amount, _, vault_tokens_received, usd_value = ai_wallet.depositTokens(
        lego_id, asset, MAX_UINT256, vault_token, sender=agent)
    assert deposit_amount != 0 and vault_tokens_received != 0

    assert ai_wallet.wethAddr() == asset.address
    assert ai_wallet.canAgentAccess(agent, CONVERSION_UINT256, [asset.address], [lego_id])

    # convert weth to eth
    amount = ai_wallet.convertWethToEth(MAX_UINT256, owner, lego_id, vault_token, sender=agent)
    assert amount != 0

    log = filter_logs(ai_wallet, "WethConvertedToEth")[0]
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
