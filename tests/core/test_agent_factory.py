import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from contracts.core.templates import UserWalletTemplate, UserWalletConfigTemplate
from contracts.core import AgentFactory
from utils.BluePrint import PARAMS


#########
# Tests #
#########


def test_agent_factory_init(agent_factory, addy_registry, weth, wallet_funds_template, wallet_config_template, agent_template):
    assert agent_factory.ADDY_REGISTRY() == addy_registry.address
    assert agent_factory.WETH_ADDR() == weth.address
    assert agent_factory.isActivated()
    assert agent_factory.currentUserWalletTemplate() == wallet_funds_template.address
    assert agent_factory.currentUserWalletConfigTemplate() == wallet_config_template.address
    assert agent_factory.currentAgentTemplate() == agent_template.address


def test_init_with_zero_address(lego_registry, weth):
    new_wallet_template = boa.load_partial("contracts/core/templates/UserWalletTemplate.vy").deploy_as_blueprint()
    new_wallet_config_template = boa.load_partial("contracts/core/templates/UserWalletConfigTemplate.vy").deploy_as_blueprint()
    new_agent_template = boa.load_partial("contracts/core/templates/AgentTemplate.vy").deploy_as_blueprint()

    with boa.reverts("invalid addrs"):
        AgentFactory.deploy(ZERO_ADDRESS, weth, new_wallet_template, new_wallet_config_template, new_agent_template, 1, 2, [])
    
    with boa.reverts("invalid addrs"):
        AgentFactory.deploy(lego_registry.address, ZERO_ADDRESS, new_wallet_template, new_wallet_config_template, new_agent_template, 1, 2, [])


def test_create_user_wallet(agent_factory, owner, agent):
    # Test with zero owner
    assert agent_factory.createUserWallet(ZERO_ADDRESS, agent) == ZERO_ADDRESS

    # success
    wallet_addr = agent_factory.createUserWallet(owner, agent, sender=owner)
    assert wallet_addr != ZERO_ADDRESS

    log = filter_logs(agent_factory, "UserWalletCreated")[0]
    assert log.mainAddr == wallet_addr
    assert log.configAddr == UserWalletTemplate.at(wallet_addr).walletConfig()
    assert log.owner == owner
    assert log.agent == agent

    assert agent_factory.isUserWallet(wallet_addr)


def test_create_wallet_with_defaults(agent_factory, owner):
    wallet_addr = agent_factory.createUserWallet(sender=owner)
    assert wallet_addr != ZERO_ADDRESS
    
    log = filter_logs(agent_factory, "UserWalletCreated")[0]
    assert log.owner == owner
    assert log.agent == ZERO_ADDRESS
    
    assert agent_factory.isUserWallet(wallet_addr)


def test_create_wallet_when_deactivated(agent_factory, owner, agent, governor):
    agent_factory.activate(False, sender=governor)
    
    with boa.reverts("not activated"):
        agent_factory.createUserWallet(owner, agent)


def test_set_main_wallet_template(agent_factory, governor):
    new_template = boa.load_partial("contracts/core/templates/UserWalletTemplate.vy").deploy_as_blueprint()

    assert agent_factory.setUserWalletTemplate(new_template, sender=governor)

    log = filter_logs(agent_factory, "UserWalletTemplateSet")[0]
    assert log.template == new_template.address
    assert log.version == 2

    info = agent_factory.userWalletTemplate()
    assert info.addr == new_template.address
    assert info.version == 2
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_set_wallet_config_template(agent_factory, governor, fork):
    new_template = boa.load_partial("contracts/core/templates/UserWalletConfigTemplate.vy").deploy_as_blueprint()

    assert agent_factory.setUserWalletConfigTemplate(new_template, sender=governor)

    log = filter_logs(agent_factory, "UserWalletConfigTemplateSet")[0]
    assert log.template == new_template.address
    assert log.version == 2

    info = agent_factory.userWalletConfig()
    assert info.addr == new_template.address
    assert info.version == 2
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_set_template_validation(agent_factory, governor, agent):
    new_template = boa.load_partial("contracts/core/templates/UserWalletTemplate.vy").deploy_as_blueprint()

    with boa.reverts("no perms"):
        agent_factory.setUserWalletTemplate(new_template.address, sender=agent)

    # Test with zero address
    assert not agent_factory.setUserWalletTemplate(ZERO_ADDRESS, sender=governor)
    
    # Test with current template address
    current = agent_factory.currentUserWalletTemplate()
    assert not agent_factory.setUserWalletTemplate(current, sender=governor)
    
    # Test with non-contract address
    assert not agent_factory.setUserWalletTemplate(agent, sender=governor)


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
    wallet_addr = agent_factory.createUserWallet(owner, agent, sender=bob)
    assert wallet_addr == ZERO_ADDRESS
    
    # Whitelist bob and try again
    assert agent_factory.setWhitelist(bob, True, sender=governor)
    wallet_addr = agent_factory.createUserWallet(owner, agent, sender=bob)
    assert wallet_addr != ZERO_ADDRESS
    
    # Test setting enforcement by non-governor
    with boa.reverts("no perms"):
        agent_factory.setShouldEnforceWhitelist(False, sender=bob)


def test_wallet_limit_control(agent_factory, governor, bob):
    # Test setting limit by governor
    assert agent_factory.setNumUserWalletsAllowed(5, sender=governor)
    
    log = filter_logs(agent_factory, "NumUserWalletsAllowedSet")[0]
    assert log.numAllowed == 5

    assert agent_factory.numUserWalletsAllowed() == 5

    # Test setting limit by non-governor
    with boa.reverts("no perms"):
        agent_factory.setNumUserWalletsAllowed(10, sender=bob)


def test_wallet_limit_enforcement(agent_factory, governor, owner, agent):
    # Set limit to 2 wallets
    assert agent_factory.setNumUserWalletsAllowed(2, sender=governor)
    
    # Create first wallet
    wallet1 = agent_factory.createUserWallet(owner, agent)
    assert wallet1 != ZERO_ADDRESS
    assert agent_factory.numUserWallets() == 1
    
    # Create second wallet
    wallet2 = agent_factory.createUserWallet(owner, agent)
    assert wallet2 != ZERO_ADDRESS
    assert agent_factory.numUserWallets() == 2
    
    # Try to create third wallet - should fail
    wallet3 = agent_factory.createUserWallet(owner, agent)
    assert wallet3 == ZERO_ADDRESS
    assert agent_factory.numUserWallets() == 2


def test_create_agent(agent_factory, owner):
    # Test with zero owner
    assert agent_factory.createAgent(ZERO_ADDRESS) == ZERO_ADDRESS

    # success
    agent_addr = agent_factory.createAgent(owner, sender=owner)
    assert agent_addr != ZERO_ADDRESS

    log = filter_logs(agent_factory, "AgentCreated")[0]
    assert log.agent == agent_addr
    assert log.owner == owner
    assert log.creator == owner

    assert agent_factory.isAgent(agent_addr)


def test_create_agent_with_defaults(agent_factory, bob):
    agent_addr = agent_factory.createAgent(sender=bob)
    assert agent_addr != ZERO_ADDRESS
    
    log = filter_logs(agent_factory, "AgentCreated")[0]
    assert log.owner == bob
    assert log.creator == bob
    
    assert agent_factory.isAgent(agent_addr)


def test_create_agent_when_deactivated(agent_factory, owner, governor):
    agent_factory.activate(False, sender=governor)
    
    with boa.reverts("not activated"):
        agent_factory.createAgent(owner)


def test_set_agent_template(agent_factory, governor):
    new_template = boa.load_partial("contracts/core/templates/AgentTemplate.vy").deploy_as_blueprint()

    assert agent_factory.setAgentTemplate(new_template, sender=governor)

    log = filter_logs(agent_factory, "AgentTemplateSet")[0]
    assert log.template == new_template.address
    assert log.version == 2

    info = agent_factory.agentTemplateInfo()
    assert info.addr == new_template.address
    assert info.version == 2
    assert info.lastModified == boa.env.evm.patch.timestamp


def test_set_agent_template_validation(agent_factory, governor, bob):
    new_template = boa.load_partial("contracts/core/templates/AgentTemplate.vy").deploy_as_blueprint()

    with boa.reverts("no perms"):
        agent_factory.setAgentTemplate(new_template.address, sender=bob)

    # Test with zero address
    assert not agent_factory.setAgentTemplate(ZERO_ADDRESS, sender=governor)
    
    # Test with current template address
    current = agent_factory.currentAgentTemplate()
    assert not agent_factory.setAgentTemplate(current, sender=governor)
    
    # Test with non-contract address
    assert not agent_factory.setAgentTemplate(bob, sender=governor)


def test_agent_limit_control(agent_factory, governor, bob):
    # Test setting limit by governor
    assert agent_factory.setNumAgentsAllowed(5, sender=governor)
    
    log = filter_logs(agent_factory, "NumAgentsAllowedSet")[0]
    assert log.numAllowed == 5

    assert agent_factory.numAgentsAllowed() == 5

    # Test setting limit by non-governor
    with boa.reverts("no perms"):
        agent_factory.setNumAgentsAllowed(10, sender=bob)


def test_agent_limit_enforcement(agent_factory, governor, owner):
    # Set limit to 2 agents
    assert agent_factory.setNumAgentsAllowed(2, sender=governor)
    
    # Create first agent
    agent1 = agent_factory.createAgent(owner)
    assert agent1 != ZERO_ADDRESS
    assert agent_factory.numAgents() == 1
    
    # Create second agent
    agent2 = agent_factory.createAgent(owner)
    assert agent2 != ZERO_ADDRESS
    assert agent_factory.numAgents() == 2
    
    # Try to create third agent - should fail
    agent3 = agent_factory.createAgent(owner)
    assert agent3 == ZERO_ADDRESS
    assert agent_factory.numAgents() == 2


def test_agent_blacklist_control(agent_factory, governor, bob):
    # Test setting blacklist by governor
    assert agent_factory.setAgentBlacklist(bob, True, sender=governor)
    
    log = filter_logs(agent_factory, "AgentBlacklistSet")[0]
    assert log.agentAddr == bob
    assert log.shouldBlacklist == True

    assert agent_factory.agentBlacklist(bob)

    # Test removing from blacklist
    assert agent_factory.setAgentBlacklist(bob, False, sender=governor)
    assert not agent_factory.agentBlacklist(bob)
    
    # Test setting blacklist by non-governor
    with boa.reverts("no perms"):
        agent_factory.setAgentBlacklist(bob, True, sender=bob)


def test_critical_cancel_control(agent_factory, governor, bob):
    """Test setting critical cancel permissions"""
    # Test setting by governor
    assert agent_factory.setCanCriticalCancel(bob, True, sender=governor)
    
    log = filter_logs(agent_factory, "CanCriticalCancelSet")[0]
    assert log.addr == bob
    assert log.canCancel == True

    assert agent_factory.canCriticalCancel(bob)

    # Test removing permissions
    assert agent_factory.setCanCriticalCancel(bob, False, sender=governor)
    assert not agent_factory.canCriticalCancel(bob)
    
    # Test setting by non-governor
    with boa.reverts("no perms"):
        agent_factory.setCanCriticalCancel(bob, True, sender=bob)


def test_critical_cancel_validation(agent_factory, governor, bob):
    """Test critical cancel validation"""
    # Test with zero address
    assert not agent_factory.setCanCriticalCancel(ZERO_ADDRESS, True, sender=governor)
    
    # Test with governor address
    assert not agent_factory.setCanCriticalCancel(governor, True, sender=governor)
    
    # Test with same value
    agent_factory.setCanCriticalCancel(bob, True, sender=governor)
    assert not agent_factory.setCanCriticalCancel(bob, True, sender=governor)


def test_critical_cancel_permissions(agent_factory, governor, bob, sally):
    """Test critical cancel permissions in action"""
    # Set bob as critical canceler
    agent_factory.setCanCriticalCancel(bob, True, sender=governor)
    
    # Bob can cancel critical actions
    assert agent_factory.canCancelCriticalAction(bob)
    
    # Sally cannot cancel critical actions
    assert not agent_factory.canCancelCriticalAction(sally)
    
    # Governor can always cancel critical actions
    assert agent_factory.canCancelCriticalAction(governor)


def test_create_wallet_with_ambassador(agent_factory, owner, agent, bob_ai_wallet):
    """Test creating a wallet with a valid ambassador"""
    # Create wallet with ambassador
    wallet_addr = agent_factory.createUserWallet(owner, agent, bob_ai_wallet.address, sender=owner)
    assert wallet_addr != ZERO_ADDRESS

    # Verify ambassador was set in config
    wallet = UserWalletTemplate.at(wallet_addr)
    wallet_config = UserWalletConfigTemplate.at(wallet.walletConfig())
    assert wallet_config.myAmbassador() == bob_ai_wallet.address

    log = filter_logs(agent_factory, "UserWalletCreated")[0]
    assert log.mainAddr == wallet_addr
    assert log.owner == owner
    assert log.agent == agent
    assert log.creator == owner


def test_create_wallet_with_non_underscore_ambassador(agent_factory, owner, agent, sally):
    """Test creating a wallet with an invalid ambassador (non-underscore wallet)"""
    # Try to create wallet with non-underscore wallet as ambassador
    with boa.reverts("ambassador must be Underscore wallet"):
        agent_factory.createUserWallet(owner, agent, sally)


def test_create_wallet_with_non_ambassador_wallet(agent_factory, owner, agent, bob_ai_wallet, bob):
    """Test creating a wallet with a wallet that cannot be ambassador"""
    # Set bob_ai_wallet to not be able to be ambassador
    bob_config = UserWalletConfigTemplate.at(bob_ai_wallet.walletConfig())
    bob_config.setCanWalletBeAmbassador(False, sender=bob)
    assert not bob_ai_wallet.canBeAmbassador()

    # Create wallet - should succeed but ambassador should be empty since canBeAmbassador is false
    wallet_addr = agent_factory.createUserWallet(owner, agent, bob_ai_wallet.address, sender=owner)
    assert wallet_addr != ZERO_ADDRESS

    # Verify ambassador was NOT set in config
    wallet = UserWalletTemplate.at(wallet_addr)
    wallet_config = UserWalletConfigTemplate.at(wallet.walletConfig())
    assert wallet_config.myAmbassador() == ZERO_ADDRESS

    log = filter_logs(agent_factory, "UserWalletCreated")[0]
    assert log.mainAddr == wallet_addr
    assert log.owner == owner
    assert log.agent == agent
    assert log.creator == owner
    assert log.ambassador == ZERO_ADDRESS  # Ambassador should be empty since canBeAmbassador is false


def test_set_ambassador_bonus_ratio(agent_factory, governor, bob):
    """Test setting ambassador bonus ratio"""
    # Test setting by governor
    assert agent_factory.setAmbassadorBonusRatio(10_00, sender=governor)  # 10%
    
    log = filter_logs(agent_factory, "AmbassadorBonusRatioSet")[0]
    assert log.ratio == 10_00

    assert agent_factory.ambassadorBonusRatio() == 10_00

    # Test setting by non-governor
    with boa.reverts("no perms"):
        agent_factory.setAmbassadorBonusRatio(20_00, sender=bob)

    # Test setting invalid ratio (over 100%)
    with boa.reverts("invalid ratio"):
        agent_factory.setAmbassadorBonusRatio(100_01, sender=governor)


def test_pay_ambassador_yield_bonus(agent_factory, owner, governor, bob_ai_wallet, alpha_token, alpha_token_whale):
    """Test paying ambassador yield bonus with valid inputs"""
    # Set up ambassador bonus ratio
    agent_factory.setAmbassadorBonusRatio(10_00, sender=governor)  # 10%
    
    # Create wallet with ambassador
    wallet_addr = agent_factory.createUserWallet(owner, ZERO_ADDRESS, bob_ai_wallet.address, sender=owner)
    
    # Transfer alpha tokens to factory
    alpha_token.transfer(agent_factory.address, 200 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Pay ambassador bonus
    assert agent_factory.payAmbassadorYieldBonus(bob_ai_wallet.address, alpha_token.address, 200 * EIGHTEEN_DECIMALS, sender=wallet_addr)
    
    # Verify bonus was paid (10% of 200 = 20)
    assert alpha_token.balanceOf(bob_ai_wallet.address) == 20 * EIGHTEEN_DECIMALS
    
    log = filter_logs(agent_factory, "AmbassadorYieldBonusPaid")[0]
    assert log.user == wallet_addr
    assert log.ambassador == bob_ai_wallet.address
    assert log.asset == alpha_token.address
    assert log.amount == 20 * EIGHTEEN_DECIMALS
    assert log.ratio == 10_00


def test_pay_ambassador_yield_bonus_failures(agent_factory, owner, governor, bob_ai_wallet, alpha_token, alpha_token_whale):
    """Test various failure cases for paying ambassador yield bonus"""
    # Set up ambassador bonus ratio
    agent_factory.setAmbassadorBonusRatio(10_00, sender=governor)  # 10%
    
    # Create wallet with ambassador
    wallet_addr = agent_factory.createUserWallet(owner, ZERO_ADDRESS, bob_ai_wallet.address, sender=owner)
    
    # Test with zero ambassador address
    assert not agent_factory.payAmbassadorYieldBonus(ZERO_ADDRESS, alpha_token.address, 100 * EIGHTEEN_DECIMALS, sender=wallet_addr)
    
    # Test with zero asset address
    assert not agent_factory.payAmbassadorYieldBonus(bob_ai_wallet.address, ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS, sender=wallet_addr)
    
    # Test with zero amount
    assert not agent_factory.payAmbassadorYieldBonus(bob_ai_wallet.address, alpha_token.address, 0, sender=wallet_addr)
    
    # Test with non-wallet caller
    assert not agent_factory.payAmbassadorYieldBonus(bob_ai_wallet.address, alpha_token.address, 100 * EIGHTEEN_DECIMALS, sender=owner)
    
    # Test with zero bonus ratio
    agent_factory.setAmbassadorBonusRatio(0, sender=governor)
    assert not agent_factory.payAmbassadorYieldBonus(bob_ai_wallet.address, alpha_token.address, 100 * EIGHTEEN_DECIMALS, sender=wallet_addr)


def test_pay_ambassador_yield_bonus_insufficient_balance(agent_factory, owner, governor, bob_ai_wallet, alpha_token, alpha_token_whale):
    """Test paying ambassador yield bonus with insufficient balance"""
    # Set up ambassador bonus ratio
    agent_factory.setAmbassadorBonusRatio(10_00, sender=governor)  # 10%
    
    # Create wallet with ambassador
    wallet_addr = agent_factory.createUserWallet(owner, ZERO_ADDRESS, bob_ai_wallet.address, sender=owner)
    
    # Transfer small amount of alpha tokens
    alpha_token.transfer(agent_factory.address, 5 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Try to pay bonus larger than available balance
    assert agent_factory.payAmbassadorYieldBonus(bob_ai_wallet.address, alpha_token.address, 100 * EIGHTEEN_DECIMALS, sender=wallet_addr)
    
    # Verify only available balance was paid (50 tokens)
    assert alpha_token.balanceOf(bob_ai_wallet.address) == 5 * EIGHTEEN_DECIMALS
    
    log = filter_logs(agent_factory, "AmbassadorYieldBonusPaid")[0]
    assert log.amount == 5 * EIGHTEEN_DECIMALS

