# @version 0.3.10

interface AgenticWallet:
    def initialize(_legoRegistry: address, _owner: address, _agent: address) -> bool: nonpayable

interface LegoRegistry:
    def governor() -> address: view

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

event AgentFactoryActivated:
    isActivated: bool

# core
agentTemplateInfo: public(TemplateInfo)
isAgenticWallet: public(HashMap[address, bool])
isActivated: public(bool)

LEGO_REGISTRY: immutable(address)


@external
def __init__(_legoRegistry: address, _walletTemplate: address):
    assert _legoRegistry != empty(address) # dev: invalid addrs
    LEGO_REGISTRY = _legoRegistry

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
    assert msg.sender == LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
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


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AgentFactoryActivated(_shouldActivate)
