import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256


#########
# Tests #
#########


def test_wallet_config_initialization(ai_wallet, ai_wallet_config, owner, agent):
    assert ai_wallet_config.wallet() == ai_wallet.address
    assert ai_wallet_config.owner() == owner
    assert ai_wallet_config.apiVersion() == "0.0.3"

    # Check initial agent settings
    agent_info = ai_wallet_config.agentSettings(agent)
    assert agent_info.isActive
    assert len(agent_info.allowedAssets) == 0
    assert len(agent_info.allowedLegoIds) == 0


# agent management


def test_agent_management(ai_wallet_config, owner, agent, mock_lego_alpha, mock_lego_bravo, bravo_token, alpha_token, sally):
    # Test adding assets and lego ids for agent
    lego_id = mock_lego_alpha.legoId()
    lego_id_another = mock_lego_bravo.legoId()

    # Add asset for agent
    assert ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    log = filter_logs(ai_wallet_config, "AssetAddedToAgent")[0]
    assert log.agent == agent
    assert log.asset == alpha_token.address

    # Add lego id for agent
    assert ai_wallet_config.addLegoIdForAgent(agent, lego_id, sender=owner)
    log = filter_logs(ai_wallet_config, "LegoIdAddedToAgent")[0]
    assert log.agent == agent
    assert log.legoId == lego_id

    # Verify agent settings
    agent_info = ai_wallet_config.agentSettings(agent)
    assert agent_info.isActive
    assert alpha_token.address in agent_info.allowedAssets
    assert lego_id in agent_info.allowedLegoIds

    # Test modifying agent settings
    new_assets = [alpha_token.address, bravo_token.address]
    new_lego_ids = [lego_id, lego_id_another]
    assert ai_wallet_config.addOrModifyAgent(agent, new_assets, new_lego_ids, sender=owner)
    log = filter_logs(ai_wallet_config, "AgentModified")[0]
    assert log.agent == agent
    assert log.allowedAssets == 2
    assert log.allowedLegoIds == 2

    # Verify agent settings
    agent_info = ai_wallet_config.agentSettings(agent)
    assert agent_info.isActive
    assert alpha_token.address in agent_info.allowedAssets
    assert lego_id in agent_info.allowedLegoIds
    assert bravo_token.address in agent_info.allowedAssets
    assert lego_id_another in agent_info.allowedLegoIds

    # Test adding new agent
    assert ai_wallet_config.addOrModifyAgent(sally, new_assets, new_lego_ids, sender=owner)
    log = filter_logs(ai_wallet_config, "AgentAdded")[0]
    assert log.agent == sally
    assert log.allowedAssets == 2
    assert log.allowedLegoIds == 2

    # Verify agent settings
    agent_info = ai_wallet_config.agentSettings(sally)
    assert agent_info.isActive
    assert alpha_token.address in agent_info.allowedAssets
    assert lego_id in agent_info.allowedLegoIds
    assert bravo_token.address in agent_info.allowedAssets
    assert lego_id_another in agent_info.allowedLegoIds

    # Test disabling agent
    assert ai_wallet_config.disableAgent(agent, sender=owner)
    log = filter_logs(ai_wallet_config, "AgentDisabled")[0]
    assert log.agent == agent
    assert log.prevAllowedAssets == 2
    assert log.prevAllowedLegoIds == 2

    # Verify agent is disabled
    agent_info = ai_wallet_config.agentSettings(agent)
    assert not agent_info.isActive


# agent management permissions


def test_agent_management_permissions(ai_wallet_config, owner, agent, alpha_token, sally, mock_lego_alpha):
    with boa.reverts(("no perms")):
        ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=sally)

    with boa.reverts("no perms"):
        ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=sally)

    with boa.reverts("no perms"):
        ai_wallet_config.addOrModifyAgent(agent, [alpha_token], [mock_lego_alpha.legoId()], sender=sally)

    with boa.reverts("no perms"):
        ai_wallet_config.disableAgent(agent, sender=sally)

    # Test invalid agent address
    with boa.reverts("invalid agent"):
        ai_wallet_config.addOrModifyAgent(ZERO_ADDRESS, [], [], sender=owner)

    # Test owner cannot be agent
    with boa.reverts("agent cannot be owner"):
        ai_wallet_config.addOrModifyAgent(owner, [], [], sender=owner)

    # Test disabling non-active agent
    with boa.reverts("agent not active"):
        ai_wallet_config.disableAgent(sally, sender=owner)

    # Test adding duplicate asset
    assert ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
    with boa.reverts("asset already saved"):
        ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)

    # Test adding duplicate lego id
    assert ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
    with boa.reverts("lego id already saved"):
        ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)


def test_reserve_assets(ai_wallet, ai_wallet_config, owner, agent, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale):
    """Test reserve asset functionality"""
    amount = 1_000 * EIGHTEEN_DECIMALS
    reserve_amount = 100 * EIGHTEEN_DECIMALS

    # Fund wallet
    alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)
    bravo_token.transfer(ai_wallet, amount, sender=bravo_token_whale)

    # Set reserve amounts
    assert ai_wallet_config.setReserveAsset(alpha_token, reserve_amount, sender=owner)
    log = filter_logs(ai_wallet_config, "ReserveAssetSet")[0]
    assert log.asset == alpha_token.address
    assert log.amount == reserve_amount

    assert ai_wallet_config.setReserveAsset(bravo_token, reserve_amount, sender=owner)

    # Verify reserve amounts
    assert ai_wallet_config.reserveAssets(alpha_token) == reserve_amount
    assert ai_wallet_config.reserveAssets(bravo_token) == reserve_amount

    # Test successful transfer respecting reserve
    assert ai_wallet.transferFunds(owner, MAX_UINT256, alpha_token, sender=agent)
    assert alpha_token.balanceOf(ai_wallet) == reserve_amount

    # Test removing reserve
    assert ai_wallet_config.setReserveAsset(alpha_token, 0, sender=owner)
    log = filter_logs(ai_wallet_config, "ReserveAssetSet")[0]
    assert log.asset == alpha_token.address
    assert log.amount == 0

    # Test transfer after removing reserve
    assert ai_wallet.transferFunds(owner, reserve_amount, alpha_token, sender=agent)
    assert alpha_token.balanceOf(ai_wallet) == 0

    # Test non-owner cannot set reserve
    with boa.reverts("no perms"):
        ai_wallet_config.setReserveAsset(alpha_token, reserve_amount, sender=agent)


def test_cancel_pending_whitelist_critical(ai_wallet_config, owner, agent_factory, governor, sally, bob):
    """Test canceling pending whitelist with critical cancel permissions"""
    # Add sally to pending whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    
    # Set sally as critical canceler
    agent_factory.setCanCriticalCancel(bob, True, sender=governor)
    
    # Sally can cancel pending whitelist
    ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=bob)
    log = filter_logs(ai_wallet_config, "WhitelistAddrCancelled")[0]
    assert log.addr == sally
    assert log.initiatedBlock != 0
    assert log.confirmBlock != 0
    assert log.cancelledBy == bob


def test_cancel_ownership_change_critical(ai_wallet_config, owner, agent_factory, governor, sally, bob):
    """Test canceling ownership change with critical cancel permissions"""
    # Initiate ownership change
    ai_wallet_config.changeOwnership(sally, sender=owner)
    
    # Set sally as critical canceler
    agent_factory.setCanCriticalCancel(bob, True, sender=governor)
    
    # Sally can cancel ownership change
    ai_wallet_config.cancelOwnershipChange(sender=bob)
    log = filter_logs(ai_wallet_config, "OwnershipChangeCancelled")[0]
    assert log.cancelledOwner == sally
    assert log.initiatedBlock != 0
    assert log.confirmBlock != 0
    assert log.cancelledBy == bob


def test_cancel_pending_whitelist_no_perms(ai_wallet_config, owner, sally):
    """Test canceling pending whitelist without permissions"""
    # Add sally to pending whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    
    # Sally cannot cancel without permissions
    with boa.reverts("no perms (only owner or governance)"):
        ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=sally)


def test_cancel_ownership_change_no_perms(ai_wallet_config, owner, sally):
    """Test canceling ownership change without permissions"""
    # Initiate ownership change
    ai_wallet_config.changeOwnership(sally, sender=owner)
    
    # Sally cannot cancel without permissions
    with boa.reverts("no perms (only owner or governance)"):
        ai_wallet_config.cancelOwnershipChange(sender=sally)


def test_cancel_pending_whitelist_owner(ai_wallet_config, owner, sally):
    """Test canceling pending whitelist as owner"""
    # Add sally to pending whitelist
    ai_wallet_config.addWhitelistAddr(sally, sender=owner)
    
    # Owner can cancel pending whitelist
    ai_wallet_config.cancelPendingWhitelistAddr(sally, sender=owner)
    log = filter_logs(ai_wallet_config, "WhitelistAddrCancelled")[0]
    assert log.addr == sally
    assert log.initiatedBlock != 0
    assert log.confirmBlock != 0
    assert log.cancelledBy == owner


def test_cancel_ownership_change_owner(ai_wallet_config, owner, sally):
    """Test canceling ownership change as owner"""
    # Initiate ownership change
    ai_wallet_config.changeOwnership(sally, sender=owner)
    
    # Owner can cancel ownership change
    ai_wallet_config.cancelOwnershipChange(sender=owner)
    log = filter_logs(ai_wallet_config, "OwnershipChangeCancelled")[0]
    assert log.cancelledOwner == sally
    assert log.initiatedBlock != 0
    assert log.confirmBlock != 0
    assert log.cancelledBy == owner


def test_ambassador_settings(ai_wallet_config, owner, sally):
    """Test ambassador settings functionality"""
    # Test initial state
    assert ai_wallet_config.canWalletBeAmbassador() == True
    assert ai_wallet_config.ambassadorForwarder() == ZERO_ADDRESS

    # Test setting canWalletBeAmbassador
    assert ai_wallet_config.setCanWalletBeAmbassador(False, sender=owner)
    log = filter_logs(ai_wallet_config, "CanWalletBeAmbassadorSet")[0]
    assert log.canWalletBeAmbassador == False
    assert ai_wallet_config.canWalletBeAmbassador() == False

    # Test setting back to True
    assert ai_wallet_config.setCanWalletBeAmbassador(True, sender=owner)
    log = filter_logs(ai_wallet_config, "CanWalletBeAmbassadorSet")[0]
    assert log.canWalletBeAmbassador == True
    assert ai_wallet_config.canWalletBeAmbassador() == True

    # Test non-owner cannot set
    with boa.reverts("no perms"):
        ai_wallet_config.setCanWalletBeAmbassador(False, sender=sally)

    # Test setting same value returns False
    assert not ai_wallet_config.setCanWalletBeAmbassador(True, sender=owner)


def test_ambassador_forwarder(ai_wallet_config, owner, sally, bob_ai_wallet):
    """Test ambassador forwarder functionality"""
    # Test initial state
    assert ai_wallet_config.ambassadorForwarder() == ZERO_ADDRESS

    # Test setting forwarder to non-underscore wallet
    with boa.reverts():
        ai_wallet_config.setAmbassadorForwarder(sally, sender=owner)

    # Test setting valid forwarder (bob_ai_wallet should be able to be ambassador by default)
    assert ai_wallet_config.setAmbassadorForwarder(bob_ai_wallet.address, sender=owner)
    log = filter_logs(ai_wallet_config, "AmbassadorForwarderSet")[0]
    assert log.addr == bob_ai_wallet.address
    assert ai_wallet_config.ambassadorForwarder() == bob_ai_wallet.address

    # Test setting same forwarder returns False
    assert not ai_wallet_config.setAmbassadorForwarder(bob_ai_wallet.address, sender=owner)

    # Test non-owner cannot set
    with boa.reverts("no perms"):
        ai_wallet_config.setAmbassadorForwarder(bob_ai_wallet.address, sender=sally)


def test_get_proceeds_addr(ai_wallet_config, owner, bob_ai_wallet):
    """Test getProceedsAddr functionality"""
    # Test when cannot be ambassador
    ai_wallet_config.setCanWalletBeAmbassador(False, sender=owner)
    assert ai_wallet_config.getProceedsAddr() == ZERO_ADDRESS

    # Test when can be ambassador but no forwarder
    ai_wallet_config.setCanWalletBeAmbassador(True, sender=owner)
    assert ai_wallet_config.getProceedsAddr() == ai_wallet_config.wallet()

    # Test when forwarder is set
    assert ai_wallet_config.setAmbassadorForwarder(bob_ai_wallet.address, sender=owner)
    assert ai_wallet_config.getProceedsAddr() == bob_ai_wallet.address

