# @version 0.3.10

interface AgenticWallet:
    def initialize(_legoRegistry: address, _owner: address, _agent: address) -> bool: nonpayable

struct TemplateInfo:
    addr: address
    version: uint256
    lastModified: uint256

event AgenticWalletCreated:
    addr: indexed(address)
    owner: indexed(address)
    agent: indexed(address)

event AgentTemplateSet:
    template: indexed(address)
    version: uint256

event AgentFactoryGovernorSet:
    governor: indexed(address)

event AgentFactoryActivated:
    isActivated: bool

# core
agentTemplateInfo: public(TemplateInfo)
isAgenticWallet: public(HashMap[address, bool])

# config
governor: public(address)
isActivated: public(bool)

LEGO_REGISTRY: immutable(address)


@external
def __init__(_legoRegistry: address, _governor: address, _walletTemplate: address):
    assert empty(address) not in [_legoRegistry, _governor] # dev: invalid addrs
    LEGO_REGISTRY = _legoRegistry

    self.governor = _governor
    self.isActivated = True

    # set agent template
    if self._isValidWalletTemplate(_walletTemplate):
        self._setAgenticWalletTemplate(_walletTemplate)


#########################
# Create Agentic Wallet #
#########################


@view
@external 
def isValidWalletSetup(_owner: address, _agent: address) -> bool:
    return self._isValidWalletSetup(self.agentTemplateInfo.addr, _owner, _agent)


@view
@internal 
def _isValidWalletSetup(_template: address, _owner: address, _agent: address) -> bool:
    if _template == empty(address):
        return False
    return _owner != empty(address) and _agent != empty(address) 


@external
def createAgenticWallet(_owner: address = msg.sender, _agent: address = msg.sender) -> address:
    assert self.isActivated # dev: not activated

    agentTemplate: address = self.agentTemplateInfo.addr
    if not self._isValidWalletSetup(agentTemplate, _owner, _agent):
        return empty(address)

    # create agentic wallet
    newAgentAddr: address = create_minimal_proxy_to(agentTemplate)
    assert AgenticWallet(newAgentAddr).initialize(LEGO_REGISTRY, _owner, _agent)
    self.isAgenticWallet[newAgentAddr] = True

    log AgenticWalletCreated(newAgentAddr, _owner, _agent)
    return newAgentAddr


#######################
# Set Wallet Template #
#######################


@view
@external 
def isValidWalletTemplate(_newAddr: address) -> bool:
    return self._isValidWalletTemplate(_newAddr)


@view
@internal 
def _isValidWalletTemplate(_newAddr: address) -> bool:
    if not _newAddr.is_contract or _newAddr == empty(address):
        return False
    return _newAddr != self.agentTemplateInfo.addr


@external
def setAgenticWalletTemplate(_addr: address) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms
    if not self._isValidWalletTemplate(_addr):
        return False
    return self._setAgenticWalletTemplate(_addr)


@internal
def _setAgenticWalletTemplate(_addr: address) -> bool:   
    prevData: TemplateInfo = self.agentTemplateInfo
    newData: TemplateInfo = TemplateInfo({
        addr: _addr,
        version: prevData.version + 1,
        lastModified: block.timestamp,
    })
    self.agentTemplateInfo = newData
    log AgentTemplateSet(_addr, newData.version)
    return True


################
# Set Governor #
################


@view
@external 
def isValidGovernor(_newGovernor: address) -> bool:
    return self._isValidGovernor(_newGovernor)


@view
@internal 
def _isValidGovernor(_newGovernor: address) -> bool:
    if not _newGovernor.is_contract or _newGovernor == empty(address):
        return False
    return _newGovernor != self.governor


@external
def setGovernor(_newGovernor: address) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms
    if not self._isValidGovernor(_newGovernor):
        return False
    self.governor = _newGovernor
    log AgentFactoryGovernorSet(_newGovernor)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == self.governor # dev: no perms
    self.isActivated = _shouldActivate
    log AgentFactoryActivated(_shouldActivate)
