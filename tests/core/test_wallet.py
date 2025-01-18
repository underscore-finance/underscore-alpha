import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS
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


def test_agent_management(ai_wallet, owner, agent, mock_lego, mock_lego_another, bravo_token, alpha_token, sally):
    # Test adding assets and lego ids for agent
    lego_id = mock_lego.legoId()
    lego_id_another = mock_lego_another.legoId()
    
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


def test_agent_management_permissions(ai_wallet, owner, agent, alpha_token, sally, mock_lego):
    # with boa.reverts(("no perms")):
    ai_wallet.addAssetForAgent(agent, alpha_token.address, sender=sally)

    # with boa.reverts("no perms"):
    #     ai_wallet.addLegoIdForAgent(agent, mock_lego.legoId(), sender=sally)

    # with boa.reverts("no perms"):
    #     ai_wallet.addOrModifyAgent(agent, [alpha_token], [mock_lego.legoId()], sender=sally)

    # with boa.reverts("no perms"):
    #     ai_wallet.disableAgent(agent, sender=sally)

    # # Test invalid agent address
    # with boa.reverts("invalid agent"):
    #     ai_wallet.addOrModifyAgent(ZERO_ADDRESS, [], [], sender=owner)

    # # Test owner cannot be agent
    # with boa.reverts("agent cannot be owner"):
    #     ai_wallet.addOrModifyAgent(owner, [], [], sender=owner)

    # # Test disabling non-active agent
    # with boa.reverts("agent not active"):
    #     ai_wallet.disableAgent(sally, sender=owner)

    # # Test adding duplicate asset
    # assert ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
    # with boa.reverts("asset already saved"):
    #     ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)

    # # Test adding duplicate lego id
    # assert ai_wallet.addLegoIdForAgent(agent, mock_lego.legoId(), sender=owner)
    # with boa.reverts("lego id already saved"):
    #     ai_wallet.addLegoIdForAgent(agent, mock_lego.legoId(), sender=owner)


# def test_deposit_operations(ai_wallet, owner, agent, mock_lego, alpha_token, alpha_token_erc4626_vault, alpha_token_whale):
#     """Test deposit operations"""
#     lego_id = 1  # Assuming mock_lego is registered with ID 1
#     deposit_amount = 1000 * 10**18

#     # Setup agent permissions
#     ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)

#     # Transfer tokens to wallet
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     assert alpha_token.balanceOf(ai_wallet) == deposit_amount

#     # Test deposit by owner
#     tx = ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)
#     logs = filter_logs(tx, "AgenticDeposit")
#     assert len(logs) == 1
#     assert logs[0].user == owner
#     assert logs[0].asset == alpha_token
#     assert logs[0].vaultToken == alpha_token_erc4626_vault
#     assert logs[0].assetAmountDeposited == deposit_amount
#     assert logs[0].vaultTokenAmountReceived > 0
#     assert logs[0].refundAssetAmount == 0
#     assert logs[0].legoId == lego_id
#     assert not logs[0].isAgent

#     # Test deposit by agent
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     tx = ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=agent)
#     logs = filter_logs(tx, "AgenticDeposit")
#     assert len(logs) == 1
#     assert logs[0].user == agent
#     assert logs[0].isAgent

#     # Test deposit with transfer
#     tx = ai_wallet.depositTokensWithTransfer(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=alpha_token_whale)
#     logs = filter_logs(tx, "AgenticDeposit")
#     assert len(logs) == 1
#     assert logs[0].user == alpha_token_whale
#     assert logs[0].assetAmountDeposited == deposit_amount

#     # Test deposit permissions
#     with boa.reverts("dev: agent not allowed"):
#         ai_wallet.depositTokens(2, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=agent)

#     with boa.reverts("dev: nothing to transfer"):
#         ai_wallet.depositTokens(lego_id, alpha_token, 0, alpha_token_erc4626_vault, sender=owner)


# def test_withdrawal_operations(ai_wallet, owner, agent, mock_lego, alpha_token, alpha_token_erc4626_vault, alpha_token_whale):
#     """Test withdrawal operations"""
#     lego_id = 1  # Assuming mock_lego is registered with ID 1
#     deposit_amount = 1000 * 10**18

#     # Setup agent permissions and initial deposit
#     ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)

#     # Get vault token balance
#     vault_token_balance = alpha_token_erc4626_vault.balanceOf(ai_wallet)
#     assert vault_token_balance > 0

#     # Test withdrawal by owner
#     tx = ai_wallet.withdrawTokens(lego_id, alpha_token, vault_token_balance, alpha_token_erc4626_vault, sender=owner)
#     logs = filter_logs(tx, "AgenticWithdrawal")
#     assert len(logs) == 1
#     assert logs[0].user == owner
#     assert logs[0].asset == alpha_token
#     assert logs[0].vaultToken == alpha_token_erc4626_vault
#     assert logs[0].assetAmountReceived > 0
#     assert logs[0].vaultTokenAmountBurned == vault_token_balance
#     assert logs[0].refundVaultTokenAmount == 0
#     assert logs[0].legoId == lego_id
#     assert not logs[0].isAgent

#     # Setup for agent withdrawal
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)
#     vault_token_balance = alpha_token_erc4626_vault.balanceOf(ai_wallet)

#     # Test withdrawal by agent
#     tx = ai_wallet.withdrawTokens(lego_id, alpha_token, vault_token_balance, alpha_token_erc4626_vault, sender=agent)
#     logs = filter_logs(tx, "AgenticWithdrawal")
#     assert len(logs) == 1
#     assert logs[0].user == agent
#     assert logs[0].isAgent

#     # Test withdrawal permissions
#     with boa.reverts("dev: agent not allowed"):
#         ai_wallet.withdrawTokens(2, alpha_token, vault_token_balance, alpha_token_erc4626_vault, sender=agent)

#     with boa.reverts("dev: nothing to withdraw"):
#         ai_wallet.withdrawTokens(lego_id, alpha_token, 0, alpha_token_erc4626_vault, sender=owner)


# def test_rebalance_operations(ai_wallet, owner, agent, mock_lego, alpha_token, alpha_token_erc4626_vault, alpha_token_comp_vault, alpha_token_whale):
#     """Test rebalance operations"""
#     lego_id = 1  # Assuming mock_lego is registered with ID 1
#     alt_lego_id = 2  # Another mock lego for rebalancing
#     deposit_amount = 1000 * 10**18

#     # Setup agent permissions
#     ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, alt_lego_id, sender=owner)

#     # Initial deposit
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)
#     vault_token_balance = alpha_token_erc4626_vault.balanceOf(ai_wallet)

#     # Test rebalance by owner
#     tx = ai_wallet.rebalance(lego_id, alt_lego_id, alpha_token, vault_token_balance, alpha_token_erc4626_vault, alpha_token_comp_vault, sender=owner)
#     logs = filter_logs(tx, ["AgenticWithdrawal", "AgenticDeposit"])
#     assert len(logs) == 2
    
#     withdrawal = logs[0]
#     assert withdrawal.user == owner
#     assert withdrawal.asset == alpha_token
#     assert withdrawal.vaultToken == alpha_token_erc4626_vault
#     assert not withdrawal.isAgent

#     deposit = logs[1]
#     assert deposit.user == owner
#     assert deposit.asset == alpha_token
#     assert deposit.vaultToken == alpha_token_comp_vault
#     assert not deposit.isAgent

#     # Test rebalance by agent
#     alpha_token.transfer(ai_wallet, deposit_amount, sender=alpha_token_whale)
#     ai_wallet.depositTokens(lego_id, alpha_token, deposit_amount, alpha_token_erc4626_vault, sender=owner)
#     vault_token_balance = alpha_token_erc4626_vault.balanceOf(ai_wallet)

#     tx = ai_wallet.rebalance(lego_id, alt_lego_id, alpha_token, vault_token_balance, alpha_token_erc4626_vault, alpha_token_comp_vault, sender=agent)
#     logs = filter_logs(tx, ["AgenticWithdrawal", "AgenticDeposit"])
#     assert len(logs) == 2
#     assert logs[0].isAgent and logs[1].isAgent

#     # Test rebalance permissions
#     with boa.reverts("dev: agent not allowed"):
#         ai_wallet.rebalance(3, alt_lego_id, alpha_token, vault_token_balance, alpha_token_erc4626_vault, alpha_token_comp_vault, sender=agent)


# def test_fund_transfers(ai_wallet, owner, agent, alpha_token, alpha_token_whale, sally):
#     """Test fund transfer operations"""
#     transfer_amount = 1000 * 10**18

#     # Setup
#     ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
#     alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)
    
#     # Test transfer by owner
#     tx = ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=owner)
#     logs = filter_logs(tx, "WalletFundsTransferred")
#     assert len(logs) == 1
#     assert logs[0].recipient == sally
#     assert logs[0].asset == alpha_token
#     assert logs[0].amount == transfer_amount
#     assert not logs[0].isAgent

#     # Test transfer by agent
#     alpha_token.transfer(ai_wallet, transfer_amount, sender=alpha_token_whale)
#     tx = ai_wallet.transferFunds(sally, transfer_amount, alpha_token, sender=agent)
#     logs = filter_logs(tx, "WalletFundsTransferred")
#     assert len(logs) == 1
#     assert logs[0].isAgent

#     # Test whitelist functionality
#     ai_wallet.setWhitelistAddr(sally, True, sender=owner)
#     assert ai_wallet.isRecipientAllowed(sally)

#     # Test transfer restrictions
#     with boa.reverts("dev: recipient not allowed"):
#         ai_wallet.transferFunds(alpha_token_whale, transfer_amount, alpha_token, sender=owner)

#     with boa.reverts("dev: nothing to transfer"):
#         ai_wallet.transferFunds(sally, transfer_amount * 2, alpha_token, sender=owner)


# def test_eth_weth_operations(ai_wallet, owner, agent, mock_weth, mock_lego, alpha_token_erc4626_vault):
#     """Test ETH/WETH conversion operations"""
#     eth_amount = 1 * 10**18
#     lego_id = 1

#     # Setup agent permissions
#     ai_wallet.addAssetForAgent(agent, mock_weth, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)

#     # Test ETH to WETH conversion by owner
#     tx = ai_wallet.convertEthToWeth(eth_amount, lego_id, alpha_token_erc4626_vault, value=eth_amount, sender=owner)
#     logs = filter_logs(tx, ["EthConvertedToWeth", "AgenticDeposit"])
#     assert len(logs) == 2
    
#     eth_log = logs[0]
#     assert eth_log.sender == owner
#     assert eth_log.amount == eth_amount
#     assert eth_log.paidEth == eth_amount
#     assert eth_log.weth == mock_weth
#     assert not eth_log.isAgent

#     deposit_log = logs[1]
#     assert deposit_log.asset == mock_weth
#     assert not deposit_log.isAgent

#     # Test ETH to WETH conversion by agent
#     tx = ai_wallet.convertEthToWeth(eth_amount, lego_id, alpha_token_erc4626_vault, value=eth_amount, sender=agent)
#     logs = filter_logs(tx, "EthConvertedToWeth")
#     assert len(logs) == 1
#     assert logs[0].isAgent

#     # Test WETH to ETH conversion
#     weth_balance = mock_weth.balanceOf(ai_wallet)
#     tx = ai_wallet.convertWethToEth(weth_balance, sender=owner)
#     logs = filter_logs(tx, "WethConvertedToEth")
#     assert len(logs) == 1
#     assert logs[0].sender == owner
#     assert logs[0].amount == weth_balance
#     assert logs[0].weth == mock_weth
#     assert not logs[0].isAgent

#     # Test WETH to ETH with recipient
#     mock_weth.deposit(value=eth_amount, sender=owner)
#     mock_weth.transfer(ai_wallet, eth_amount, sender=owner)
#     ai_wallet.setWhitelistAddr(agent, True, sender=owner)
    
#     tx = ai_wallet.convertWethToEth(eth_amount, agent, sender=owner)
#     logs = filter_logs(tx, ["WethConvertedToEth", "WalletFundsTransferred"])
#     assert len(logs) == 2
#     assert logs[0].amount == eth_amount
#     assert logs[1].recipient == agent
#     assert logs[1].asset == empty(address)  # ETH transfer


# def test_batch_actions(ai_wallet, owner, agent, mock_lego, alpha_token, alpha_token_erc4626_vault, alpha_token_comp_vault, alpha_token_whale, sally):
#     """Test batch action operations"""
#     lego_id = 1  # Assuming mock_lego is registered with ID 1
#     alt_lego_id = 2  # Another mock lego for rebalancing
#     amount = 1000 * 10**18

#     # Setup agent permissions
#     ai_wallet.addAssetForAgent(agent, alpha_token, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, lego_id, sender=owner)
#     ai_wallet.addLegoIdForAgent(agent, alt_lego_id, sender=owner)
#     ai_wallet.setWhitelistAddr(sally, True, sender=owner)

#     # Transfer tokens to wallet
#     alpha_token.transfer(ai_wallet, amount * 3, sender=alpha_token_whale)  # Need extra for multiple operations

#     # Create batch instructions
#     instructions = [
#         # Deposit
#         (0, lego_id, alpha_token, alpha_token_erc4626_vault, amount, empty(address), 0, empty(address)),  # ActionType.DEPOSIT = 0
#         # Withdrawal
#         (1, lego_id, alpha_token, alpha_token_erc4626_vault, amount, empty(address), 0, empty(address)),  # ActionType.WITHDRAWAL = 1
#         # Rebalance
#         (2, lego_id, alpha_token, alpha_token_erc4626_vault, amount, empty(address), alt_lego_id, alpha_token_comp_vault),  # ActionType.REBALANCE = 2
#         # Transfer
#         (3, 0, alpha_token, empty(address), amount, sally, 0, empty(address)),  # ActionType.TRANSFER = 3
#     ]

#     # Test batch actions by owner
#     tx = ai_wallet.performManyActions(instructions, sender=owner)
#     logs = filter_logs(tx, ["AgenticDeposit", "AgenticWithdrawal", "WalletFundsTransferred"])
#     assert len(logs) >= 4  # Should have at least 4 events (deposit, withdrawal, rebalance generates 2 events, transfer)
    
#     # Verify some key events
#     deposit_logs = [log for log in logs if "AgenticDeposit" in str(log)]
#     withdrawal_logs = [log for log in logs if "AgenticWithdrawal" in str(log)]
#     transfer_logs = [log for log in logs if "WalletFundsTransferred" in str(log)]
    
#     assert len(deposit_logs) >= 1
#     assert len(withdrawal_logs) >= 1
#     assert len(transfer_logs) >= 1
    
#     for log in deposit_logs + withdrawal_logs + transfer_logs:
#         assert not log.isAgent  # Owner operations

#     # Test batch actions by agent
#     alpha_token.transfer(ai_wallet, amount * 3, sender=alpha_token_whale)
#     tx = ai_wallet.performManyActions(instructions, sender=agent)
#     logs = filter_logs(tx, ["AgenticDeposit", "AgenticWithdrawal", "WalletFundsTransferred"])
    
#     for log in logs:
#         assert log.isAgent  # Agent operations

#     # Test batch action permissions
#     invalid_instructions = [
#         # Try to use unauthorized lego
#         (0, 3, alpha_token, alpha_token_erc4626_vault, amount, empty(address), 0, empty(address)),
#     ]
    
#     with boa.reverts("dev: agent not allowed"):
#         ai_wallet.performManyActions(invalid_instructions, sender=agent)

#     # Test empty instructions
#     with boa.reverts("dev: no instructions"):
#         ai_wallet.performManyActions([], sender=owner)