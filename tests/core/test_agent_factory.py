import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS
from contracts.core import AgentFactory


@pytest.fixture(scope="module")
def owner(env):
    return env.generate_address("owner")


@pytest.fixture(scope="module")
def agent(env):
    return env.generate_address("agent")


@pytest.fixture(scope="module")
def new_wallet_template():
    return boa.load("contracts/core/WalletTemplate.vy", name="new_wallet_template")


@pytest.fixture(scope="module")
def new_agent_factory(lego_registry, weth, new_wallet_template):
    return boa.load("contracts/core/AgentFactory.vy", lego_registry, weth, new_wallet_template, name="new_wallet_template")


#########
# Tests #
#########


def test_agent_factory_init(new_agent_factory, lego_registry, weth, new_wallet_template):
    assert new_agent_factory.LEGO_REGISTRY() == lego_registry.address
    assert new_agent_factory.WETH_ADDR() == weth.address
    assert new_agent_factory.isActivated()
    assert new_agent_factory.currentAgentTemplate() == new_wallet_template.address


def test_init_with_zero_address(lego_registry, weth, new_wallet_template):
    with boa.reverts("invalid addrs"):
        AgentFactory.deploy(ZERO_ADDRESS, weth, new_wallet_template)
    
    with boa.reverts("invalid addrs"):
        AgentFactory.deploy(lego_registry.address, ZERO_ADDRESS, new_wallet_template.address)


def test_create_agentic_wallet(new_agent_factory, owner, agent):
    # Test with zero owner
    assert new_agent_factory.createAgenticWallet(ZERO_ADDRESS, agent) == ZERO_ADDRESS

    # success
    wallet_addr = new_agent_factory.createAgenticWallet(owner, agent, sender=owner)
    assert wallet_addr != ZERO_ADDRESS

    log = filter_logs(new_agent_factory, "AgenticWalletCreated")[0]
    assert log.addr == wallet_addr
    assert log.owner == owner
    assert log.agent == agent

    assert new_agent_factory.isAgenticWallet(wallet_addr)


def test_create_wallet_with_defaults(new_agent_factory, owner):
    wallet_addr = new_agent_factory.createAgenticWallet(sender=owner)
    assert wallet_addr != ZERO_ADDRESS
    
    log = filter_logs(new_agent_factory, "AgenticWalletCreated")[0]
    assert log.addr == wallet_addr
    assert log.owner == owner
    assert log.agent == ZERO_ADDRESS
    
    assert new_agent_factory.isAgenticWallet(wallet_addr)


def test_create_wallet_when_deactivated(new_agent_factory, owner, agent, governor):
    new_agent_factory.activate(False, sender=governor)
    
    with boa.reverts("not activated"):
        new_agent_factory.createAgenticWallet(owner, agent)


def test_set_wallet_template(new_agent_factory, governor):
    new_template = boa.load("contracts/core/WalletTemplate.vy", name="new_new_wallet")
    
    assert new_agent_factory.setAgenticWalletTemplate(new_template, sender=governor)
    
    log = filter_logs(new_agent_factory, "AgentTemplateSet")[0]
    assert log.template == new_template.address
    assert log.version == 2
    
    info = new_agent_factory.agentTemplateInfo()
    assert info.addr == new_template.address
    assert info.version == 2
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_set_template_validation(new_agent_factory, governor, agent):
    new_template = boa.load("contracts/core/WalletTemplate.vy", name="new_new_wallet")

    with boa.reverts("no perms"):
        new_agent_factory.setAgenticWalletTemplate(new_template.address, sender=agent)

    # Test with zero address
    assert not new_agent_factory.setAgenticWalletTemplate(ZERO_ADDRESS, sender=governor)
    
    # Test with current template address
    current = new_agent_factory.currentAgentTemplate()
    assert not new_agent_factory.setAgenticWalletTemplate(current, sender=governor)
    
    # Test with non-contract address
    assert not new_agent_factory.setAgenticWalletTemplate(agent, sender=governor)


def test_activation_control(new_agent_factory, governor, bob):
    
    # Test activation by governor
    new_agent_factory.activate(False, sender=governor)
    log = filter_logs(new_agent_factory, "AgentFactoryActivated")[0]
    assert log.isActivated == False
    assert not new_agent_factory.isActivated()
    
    new_agent_factory.activate(True, sender=governor)
    log = filter_logs(new_agent_factory, "AgentFactoryActivated")[0]
    assert log.isActivated == True
    assert new_agent_factory.isActivated()
    
    # Test activation by non-governor
    with boa.reverts("no perms"):
        new_agent_factory.activate(False, sender=bob)
