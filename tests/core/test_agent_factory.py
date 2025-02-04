import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS
from contracts.core import AgentFactory


#########
# Tests #
#########


def test_agent_factory_init(agent_factory, addy_registry, weth, wallet_template):
    assert agent_factory.ADDY_REGISTRY() == addy_registry.address
    assert agent_factory.WETH_ADDR() == weth.address
    assert agent_factory.isActivated()
    assert agent_factory.currentAgentTemplate() == wallet_template.address


def test_init_with_zero_address(lego_registry, weth):
    new_wallet_template = boa.load("contracts/core/WalletTemplate.vy", name="new_wallet_template")

    with boa.reverts("invalid addrs"):
        AgentFactory.deploy(ZERO_ADDRESS, weth, new_wallet_template)
    
    with boa.reverts("invalid addrs"):
        AgentFactory.deploy(lego_registry.address, ZERO_ADDRESS, new_wallet_template.address)


def test_create_agentic_wallet(agent_factory, owner, agent):
    # Test with zero owner
    assert agent_factory.createAgenticWallet(ZERO_ADDRESS, agent) == ZERO_ADDRESS

    # success
    wallet_addr = agent_factory.createAgenticWallet(owner, agent, sender=owner)
    assert wallet_addr != ZERO_ADDRESS

    log = filter_logs(agent_factory, "AgenticWalletCreated")[0]
    assert log.addr == wallet_addr
    assert log.owner == owner
    assert log.agent == agent

    assert agent_factory.isAgenticWallet(wallet_addr)


def test_create_wallet_with_defaults(agent_factory, owner):
    wallet_addr = agent_factory.createAgenticWallet(sender=owner)
    assert wallet_addr != ZERO_ADDRESS
    
    log = filter_logs(agent_factory, "AgenticWalletCreated")[0]
    assert log.addr == wallet_addr
    assert log.owner == owner
    assert log.agent == ZERO_ADDRESS
    
    assert agent_factory.isAgenticWallet(wallet_addr)


def test_create_wallet_when_deactivated(agent_factory, owner, agent, governor):
    agent_factory.activate(False, sender=governor)
    
    with boa.reverts("not activated"):
        agent_factory.createAgenticWallet(owner, agent)


def test_set_wallet_template(agent_factory, governor):
    new_template = boa.load("contracts/core/WalletTemplate.vy", name="new_new_wallet")
    
    assert agent_factory.setAgenticWalletTemplate(new_template, sender=governor)
    
    log = filter_logs(agent_factory, "AgentTemplateSet")[0]
    assert log.template == new_template.address
    assert log.version == 2
    
    info = agent_factory.agentTemplateInfo()
    assert info.addr == new_template.address
    assert info.version == 2
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_set_template_validation(agent_factory, governor, agent):
    new_template = boa.load("contracts/core/WalletTemplate.vy", name="new_new_wallet")

    with boa.reverts("no perms"):
        agent_factory.setAgenticWalletTemplate(new_template.address, sender=agent)

    # Test with zero address
    assert not agent_factory.setAgenticWalletTemplate(ZERO_ADDRESS, sender=governor)
    
    # Test with current template address
    current = agent_factory.currentAgentTemplate()
    assert not agent_factory.setAgenticWalletTemplate(current, sender=governor)
    
    # Test with non-contract address
    assert not agent_factory.setAgenticWalletTemplate(agent, sender=governor)


def test_activation_control(agent_factory, governor, bob):
    
    # Test activation by governor
    agent_factory.activate(False, sender=governor)
    log = filter_logs(agent_factory, "AgentFactoryActivated")[0]
    assert log.isActivated == False
    assert not agent_factory.isActivated()
    
    agent_factory.activate(True, sender=governor)
    log = filter_logs(agent_factory, "AgentFactoryActivated")[0]
    assert log.isActivated == True
    assert agent_factory.isActivated()
    
    # Test activation by non-governor
    with boa.reverts("no perms"):
        agent_factory.activate(False, sender=bob)


def test_whitelist_control(agent_factory, governor, bob):
    # Test setting whitelist by governor
    assert agent_factory.setWhitelist(bob, True, sender=governor)
    
    log = filter_logs(agent_factory, "WhitelistSet")[0]
    assert log.addr == bob
    assert log.shouldWhitelist == True

    assert agent_factory.whitelist(bob)

    # Test removing from whitelist
    assert agent_factory.setWhitelist(bob, False, sender=governor)
    assert not agent_factory.whitelist(bob)
    
    # Test setting whitelist by non-governor
    with boa.reverts("no perms"):
        agent_factory.setWhitelist(bob, True, sender=bob)


def test_whitelist_enforcement(agent_factory, governor, owner, agent, bob):
    # Enable whitelist enforcement
    assert agent_factory.setShouldEnforceWhitelist(True, sender=governor)
    
    log = filter_logs(agent_factory, "ShouldEnforceWhitelistSet")[0]
    assert log.shouldEnforce == True

    assert agent_factory.shouldEnforceWhitelist()

    # Test wallet creation with non-whitelisted creator
    wallet_addr = agent_factory.createAgenticWallet(owner, agent, sender=bob)
    assert wallet_addr == ZERO_ADDRESS
    
    # Whitelist bob and try again
    assert agent_factory.setWhitelist(bob, True, sender=governor)
    wallet_addr = agent_factory.createAgenticWallet(owner, agent, sender=bob)
    assert wallet_addr != ZERO_ADDRESS
    
    # Test setting enforcement by non-governor
    with boa.reverts("no perms"):
        agent_factory.setShouldEnforceWhitelist(False, sender=bob)


def test_wallet_limit_control(agent_factory, governor, bob):
    # Test setting limit by governor
    assert agent_factory.setNumAgenticWalletsAllowed(5, sender=governor)
    
    log = filter_logs(agent_factory, "NumAgenticWalletsAllowedSet")[0]
    assert log.numAllowed == 5

    assert agent_factory.numAgenticWalletsAllowed() == 5

    # Test setting limit by non-governor
    with boa.reverts("no perms"):
        agent_factory.setNumAgenticWalletsAllowed(10, sender=bob)


def test_wallet_limit_enforcement(agent_factory, governor, owner, agent):
    # Set limit to 2 wallets
    assert agent_factory.setNumAgenticWalletsAllowed(2, sender=governor)
    
    # Create first wallet
    wallet1 = agent_factory.createAgenticWallet(owner, agent)
    assert wallet1 != ZERO_ADDRESS
    assert agent_factory.numAgenticWallets() == 1
    
    # Create second wallet
    wallet2 = agent_factory.createAgenticWallet(owner, agent)
    assert wallet2 != ZERO_ADDRESS
    assert agent_factory.numAgenticWallets() == 2
    
    # Try to create third wallet - should fail
    wallet3 = agent_factory.createAgenticWallet(owner, agent)
    assert wallet3 == ZERO_ADDRESS
    assert agent_factory.numAgenticWallets() == 2

