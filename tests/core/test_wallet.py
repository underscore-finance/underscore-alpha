import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256
from contracts.core import WalletTemplate


@pytest.fixture(scope="module")
def owner(env):
    return env.generate_address("owner")


@pytest.fixture(scope="module")
def agent(env):
    return env.generate_address("agent")


@pytest.fixture(scope="module")
def ai_wallet(agent_factory, owner, agent):
    w = agent_factory.createAgenticWallet(owner, agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isAgenticWallet(w)
    return WalletTemplate.at(w)


#########
# Tests #
#########


def test_wallet_initialization(ai_wallet, owner, agent, lego_registry, weth):
    assert ai_wallet.owner() == owner
    assert ai_wallet.legoRegistry() == lego_registry.address
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
    assert len(agent_info.allowedAssets) == 0
    assert len(agent_info.allowedLegoIds) == 0


# agent management permissions


# TODO: add back in, check vyper/boa issues

# def test_agent_management_permissions(ai_wallet, owner, agent, alpha_token, sally, mock_lego_alpha):
#     with boa.reverts(("no perms")):
#         ai_wallet.addAssetForAgent(agent, alpha_token, sender=sally)

#     with boa.reverts("no perms"):
#         ai_wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=sally)

#     with boa.reverts("no perms"):
#         ai_wallet.addOrModifyAgent(agent, [alpha_token], [mock_lego_alpha.legoId()], sender=sally)

#     with boa.reverts("no perms"):
#         ai_wallet.disableAgent(agent, sender=sally)

#     # Test invalid agent address
#     with boa.reverts("invalid agent"):
#         ai_wallet.addOrModifyAgent(ZERO_ADDRESS, [], [], sender=owner)

#     # Test owner cannot be agent
#     with boa.reverts("agent cannot be owner"):
#         ai_wallet.addOrModifyAgent(owner, [], [], sender=owner)

#     # Test disabling non-active agent
#     with boa.reverts("agent not active"):
#         ai_wallet.disableAgent(sally, sender=owner)

#     # Test adding duplicate asset
#     assert ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
#     with boa.reverts("asset already saved"):
#         ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)

#     # Test adding duplicate lego id
#     assert ai_wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
#     with boa.reverts("lego id already saved"):
#         ai_wallet.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)


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
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokens(lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=owner)
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.user == owner
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address == vaultToken
    assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    assert log.vaultTokenAmountReceived == vaultTokenAmountReceived != 0
    assert log.refundAssetAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert not log.isAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    wallet_bal = alpha_token_erc4626_vault.balanceOf(ai_wallet)
    assert wallet_bal == vaultTokenAmountReceived

    # Test deposit by agent
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.user == agent
    assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    assert log.isAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    new_wallet_bal = alpha_token_erc4626_vault.balanceOf(ai_wallet)
    assert new_wallet_bal == wallet_bal + vaultTokenAmountReceived

    # # Test deposit with transfer
    # alpha_token.approve(ai_wallet, deposit_amount, sender=alpha_token_whale)
    # assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokensWithTransfer(lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=alpha_token_whale)
    # log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    # assert log.user == alpha_token_whale
    # assert log.assetAmountDeposited == deposit_amount == assetAmountDeposited
    # assert not log.isAgent

    # assert alpha_token.balanceOf(ai_wallet) == 0
    # assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == new_wallet_bal + vaultTokenAmountReceived

    # # Test deposit permissions
    # assert not ai_wallet.canAgentAccess(agent, [bravo_token.address], [mock_lego_bravo.legoId()])
    
    # TODO: add back in, check vyper/boa issues

    # with boa.reverts("agent not allowed"):
    #     ai_wallet.depositTokens(mock_lego_bravo.legoId(), bravo_token, deposit_amount, bravo_token_erc4626_vault, sender=agent)

    # with boa.reverts("nothing to transfer"):
    #     ai_wallet.depositTokens(mock_lego_bravo.legoId(), bravo_token, deposit_amount, bravo_token_erc4626_vault, sender=owner)


def test_withdrawal_operations(ai_wallet, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale):
    lego_id = mock_lego_alpha.legoId()
    deposit_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup agent permissions and initial deposit
    ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokens(lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=agent)
    assert assetAmountDeposited == deposit_amount

    # Get vault token balance
    assert alpha_token_erc4626_vault.address == vaultToken
    assert vaultTokenAmountReceived == alpha_token_erc4626_vault.balanceOf(ai_wallet)

    # Test withdrawal by owner
    assetAmountReceived, vaultTokenAmountBurned = ai_wallet.withdrawTokens(lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, sender=owner)
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.user == owner
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountReceived == assetAmountReceived
    assert log.vaultTokenAmountBurned == vaultTokenAmountBurned
    assert log.refundVaultTokenAmount == 0
    assert log.legoId == lego_id
    assert not log.isAgent

    wallet_bal = alpha_token.balanceOf(ai_wallet)
    assert wallet_bal == assetAmountReceived
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0

    # Setup for agent withdrawal
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)

    # Test withdrawal by agent
    assetAmountReceived, vaultTokenAmountBurned = ai_wallet.withdrawTokens(lego_id, alpha_token, vaultTokenAmountReceived, alpha_token_erc4626_vault, sender=agent)
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.user == agent
    assert log.isAgent
    assert log.vaultTokenAmountBurned == vaultTokenAmountBurned

    assert alpha_token.balanceOf(ai_wallet) == assetAmountReceived + wallet_bal
    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0

    # TODO: add back in, check vyper/boa issues

    # # Test withdrawal permissions
    # with boa.reverts("dev: agent not allowed"):
    #     ai_wallet.withdrawTokens(2, alpha_token, vault_token_balance, alpha_token_erc4626_vault, sender=agent)

    # with boa.reverts("dev: nothing to withdraw"):
    #     ai_wallet.withdrawTokens(lego_id, alpha_token, 0, alpha_token_erc4626_vault, sender=owner)


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
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived = ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)
    assert vaultToken == alpha_token_erc4626_vault.address

    # Test rebalance by owner
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived = ai_wallet.rebalance(lego_id, alt_lego_id, alpha_token, MAX_UINT256, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, sender=owner)
    log_withdrawal = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    log_deposit = filter_logs(ai_wallet, "AgenticDeposit")[0]

    assert log_withdrawal.user == owner
    assert log_withdrawal.asset == alpha_token.address
    assert log_withdrawal.vaultToken == alpha_token_erc4626_vault.address == vaultToken
    assert log_withdrawal.assetAmountReceived != 0
    assert log_withdrawal.vaultTokenAmountBurned == origVaultTokenAmountReceived
    assert log_withdrawal.refundVaultTokenAmount == 0
    assert log_withdrawal.legoId == lego_id
    assert log_withdrawal.legoAddr == mock_lego_alpha.address
    assert not log_withdrawal.isAgent

    assert log_deposit.user == owner
    assert log_deposit.asset == alpha_token.address
    assert log_deposit.vaultToken == alpha_token_erc4626_vault_another.address == newVaultToken
    assert log_deposit.assetAmountDeposited == assetAmountDeposited
    assert log_deposit.vaultTokenAmountReceived == vaultTokenAmountReceived != 0
    assert log_deposit.refundAssetAmount == 0
    assert log_deposit.legoId == alt_lego_id
    assert log_deposit.legoAddr == mock_lego_alpha_another.address
    assert not log_deposit.isAgent

    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(ai_wallet) == vaultTokenAmountReceived

    # Test rebalance by agent
    alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
    assetAmountDeposited, vaultToken, origVaultTokenAmountReceived = ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)

    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived = ai_wallet.rebalance(lego_id, alt_lego_id, alpha_token, origVaultTokenAmountReceived, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, sender=agent)
    log_withdrawal = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    log_deposit = filter_logs(ai_wallet, "AgenticDeposit")[0]

    assert log_withdrawal.user == agent
    assert log_withdrawal.isAgent
    assert log_withdrawal.vaultTokenAmountBurned == origVaultTokenAmountReceived
    assert log_deposit.user == agent
    assert log_deposit.isAgent
    assert log_deposit.vaultTokenAmountReceived == vaultTokenAmountReceived

    # TODO: add back in, check vyper/boa issues

    # # Test rebalance permissions
    # with boa.reverts("agent not allowed"):
    #     ai_wallet.rebalance(3, alt_lego_id, alpha_token, vaultTokenAmountReceived, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, sender=agent)


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
    assert not log.isAgent

    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == transfer_amount

    # Test transfer by agent
    alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)
    assert ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=agent)
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == alpha_token.address
    assert log.amount == transfer_amount
    assert log.isAgent

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
    assert log.isAgent

    # Test whitelist functionality
    assert not ai_wallet.isRecipientAllowed(bob)
    ai_wallet.setWhitelistAddr(bob, True, sender=owner)
    assert ai_wallet.isRecipientAllowed(bob)

    # TODO: add back in, check vyper/boa issues

    # # Test transfer restrictions
    # with boa.reverts("recipient not allowed"):
    #     ai_wallet.transferFunds(alpha_token_whale, transfer_amount, alpha_token, sender=owner)

    # with boa.reverts("nothing to transfer"):
    #     ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=owner)


# TODO: add back in, check vyper/boa issues
# def test_eth_weth_operations(ai_wallet, owner, agent, weth, mock_lego_alpha, alpha_token_erc4626_vault):
#     eth_amount = 1 * EIGHTEEN_DECIMALS
#     boa.env.set_balance(owner, eth_amount)

#     lego_id = mock_lego_alpha.legoId()

#     # Setup agent permissions
#     ai_wallet.addAssetForAgent(agent, weth, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)

#     # Test ETH to WETH conversion by owner
#     assetAmountDeposited, vaultToken, vaultTokenAmountReceived = ai_wallet.convertEthToWeth(MAX_UINT256, lego_id, alpha_token_erc4626_vault, value=eth_amount, sender=owner)
#     log = filter_logs(ai_wallet, "EthConvertedToWeth")[0]

#     assert log.sender == owner
#     assert log.amount == eth_amount
#     assert log.paidEth == eth_amount
#     assert log.weth == weth
#     assert not log.isAgent

#     assert assetAmountDeposited == eth_amount
#     assert vaultToken == alpha_token_erc4626_vault.address
#     assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == vaultTokenAmountReceived

#     # Test WETH to ETH conversion
#     amount = ai_wallet.convertWethToEth(MAX_UINT256, ZERO_ADDRESS, lego_id, alpha_token_erc4626_vault, sender=owner)
#     log = filter_logs(ai_wallet, "WethConvertedToEth")[0]
#     assert log.sender == owner
#     assert log.amount == eth_amount == amount
#     assert log.weth == weth
#     assert not log.isAgent

#     assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
#     assert weth.balanceOf(ai_wallet) == amount


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
        (DEPOSIT_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS, 0, ZERO_ADDRESS),  # ActionType.DEPOSIT = 0
        # Withdrawal
        (WITHDRAWAL_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, amount // 2, ZERO_ADDRESS, 0, ZERO_ADDRESS),  # ActionType.WITHDRAWAL = 1
        # Rebalance
        (REBALANCE_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS, alt_lego_id, alpha_token_erc4626_vault_another),  # ActionType.REBALANCE = 2
        # Transfer
        (TRANSFER_UINT256, 0, alpha_token, ZERO_ADDRESS, MAX_UINT256, sally, 0, ZERO_ADDRESS),  # ActionType.TRANSFER = 3
    ]

    # Test batch actions by owner
    assert ai_wallet.performManyActions(instructions, sender=agent)

    # deposit
    log = filter_logs(ai_wallet, "AgenticDeposit")[0]
    assert log.user == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountDeposited == amount
    assert log.vaultTokenAmountReceived == amount
    assert log.refundAssetAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert log.isAgent

    # withdrawal
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[0]
    assert log.user == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountReceived == amount // 2
    assert log.vaultTokenAmountBurned == amount // 2
    assert log.refundVaultTokenAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert log.isAgent

    # rebalance
    log = filter_logs(ai_wallet, "AgenticWithdrawal")[1]
    assert log.user == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    assert log.assetAmountReceived == amount // 2
    assert log.vaultTokenAmountBurned == amount // 2
    assert log.refundVaultTokenAmount == 0
    assert log.legoId == lego_id
    assert log.legoAddr == mock_lego_alpha.address
    assert log.isAgent

    log = filter_logs(ai_wallet, "AgenticDeposit")[1]
    assert log.user == agent
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault_another.address
    assert log.assetAmountDeposited == amount // 2
    assert log.vaultTokenAmountReceived == amount // 2
    assert log.refundAssetAmount == 0
    assert log.legoId == alt_lego_id
    assert log.legoAddr == mock_lego_alpha_another.address
    assert log.isAgent

    # transfer
    log = filter_logs(ai_wallet, "WalletFundsTransferred")[0]
    assert log.recipient == sally
    assert log.asset == alpha_token.address
    assert log.amount == amount // 2
    assert log.isAgent

    # data
    assert alpha_token.balanceOf(ai_wallet) == 0
    assert alpha_token.balanceOf(sally) == amount // 2

    assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
    assert alpha_token_erc4626_vault_another.balanceOf(ai_wallet) == amount // 2