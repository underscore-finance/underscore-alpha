# AgentFactory API Reference

**File:** `contracts/core/AgentFactory.vy`

The AgentFactory contract is responsible for creating and managing user wallets and agents in the Underscore system.

## Data Structures

### TemplateInfo

```vyper
struct TemplateInfo:
    addr: address
    version: uint256
    lastModified: uint256
```

A struct containing information about a template contract:
- `addr`: The address of the template contract
- `version`: The version number, incremented on updates
- `lastModified`: Timestamp of the last modification

### TrialFundsData

```vyper
struct TrialFundsData:
    asset: address
    amount: uint256
```

A struct containing information about trial funds:
- `asset`: The address of the trial funds asset
- `amount`: The amount of trial funds to provide

### TrialFundsOpp

```vyper
struct TrialFundsOpp:
    legoId: uint256
    vaultToken: address
```

A struct containing information about a trial funds opportunity:
- `legoId`: The ID of the lego (protocol)
- `vaultToken`: The address of the vault token

## Events

### UserWalletCreated

```vyper
event UserWalletCreated:
    mainAddr: indexed(address)
    configAddr: indexed(address)
    owner: indexed(address)
    agent: address
    creator: address
```

Emitted when a new user wallet is created.

### AgentCreated

```vyper
event AgentCreated:
    agent: indexed(address)
    owner: indexed(address)
    creator: address
```

Emitted when a new agent is created.

### UserWalletTemplateSet

```vyper
event UserWalletTemplateSet:
    template: indexed(address)
    version: uint256
```

Emitted when the user wallet template is updated.

### UserWalletConfigTemplateSet

```vyper
event UserWalletConfigTemplateSet:
    template: indexed(address)
    version: uint256
```

Emitted when the user wallet config template is updated.

### AgentTemplateSet

```vyper
event AgentTemplateSet:
    template: indexed(address)
    version: uint256
```

Emitted when the agent template is updated.

### TrialFundsDataSet

```vyper
event TrialFundsDataSet:
    asset: indexed(address)
    amount: uint256
```

Emitted when the trial funds data is updated.

### WhitelistSet

```vyper
event WhitelistSet:
    addr: address
    shouldWhitelist: bool
```

Emitted when an address is added to or removed from the whitelist.

### NumUserWalletsAllowedSet

```vyper
event NumUserWalletsAllowedSet:
    numAllowed: uint256
```

Emitted when the maximum number of user wallets allowed is updated.

### NumAgentsAllowedSet

```vyper
event NumAgentsAllowedSet:
    numAllowed: uint256
```

Emitted when the maximum number of agents allowed is updated.

### ShouldEnforceWhitelistSet

```vyper
event ShouldEnforceWhitelistSet:
    shouldEnforce: bool
```

Emitted when the whitelist enforcement setting is updated.

### AgentBlacklistSet

```vyper
event AgentBlacklistSet:
    agentAddr: indexed(address)
    shouldBlacklist: bool
```

Emitted when an agent is added to or removed from the blacklist.

### AgentFactoryFundsRecovered

```vyper
event AgentFactoryFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256
```

Emitted when funds are recovered from the factory.

### AgentFactoryActivated

```vyper
event AgentFactoryActivated:
    isActivated: bool
```

Emitted when the factory is activated or deactivated.

## State Variables

### trialFundsData

```vyper
trialFundsData: public(TrialFundsData)
```

Information about the trial funds asset and amount for new user wallets.

### userWalletTemplate

```vyper
userWalletTemplate: public(TemplateInfo)
```

Information about the current user wallet template.

### userWalletConfig

```vyper
userWalletConfig: public(TemplateInfo)
```

Information about the current user wallet config template.

### isUserWallet

```vyper
isUserWallet: public(HashMap[address, bool])
```

Mapping to track if an address is a user wallet created by this factory.

### numUserWallets

```vyper
numUserWallets: public(uint256)
```

The total number of user wallets created by this factory.

### agentTemplateInfo

```vyper
agentTemplateInfo: public(TemplateInfo)
```

Information about the current agent template.

### isAgent

```vyper
isAgent: public(HashMap[address, bool])
```

Mapping to track if an address is an agent created by this factory.

### numAgents

```vyper
numAgents: public(uint256)
```

The total number of agents created by this factory.

### agentBlacklist

```vyper
agentBlacklist: public(HashMap[address, bool])
```

Mapping to track if an agent is blacklisted.

### numUserWalletsAllowed

```vyper
numUserWalletsAllowed: public(uint256)
```

The maximum number of user wallets allowed to be created.

### numAgentsAllowed

```vyper
numAgentsAllowed: public(uint256)
```

The maximum number of agents allowed to be created.

### whitelist

```vyper
whitelist: public(HashMap[address, bool])
```

Mapping to track if an address is whitelisted for creating wallets and agents.

### shouldEnforceWhitelist

```vyper
shouldEnforceWhitelist: public(bool)
```

Flag to determine if the whitelist should be enforced.

### isActivated

```vyper
isActivated: public(bool)
```

Flag to determine if the factory is activated and can create wallets and agents.

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

The address of the AddyRegistry contract.

### WETH_ADDR

```vyper
WETH_ADDR: public(immutable(address))
```

The address of the WETH contract.

## External Functions

### currentUserWalletTemplate

```vyper
@view
@external
def currentUserWalletTemplate() -> address:
```

Gets the current wallet template address being used by the factory.

**Returns:**
- The address of the current wallet template

### currentUserWalletConfigTemplate

```vyper
@view
@external
def currentUserWalletConfigTemplate() -> address:
```

Gets the current wallet config template address being used by the factory.

**Returns:**
- The address of the current wallet config template

### currentAgentTemplate

```vyper
@view
@external
def currentAgentTemplate() -> address:
```

Gets the current agent template address being used by the factory.

**Returns:**
- The address of the current agent template

### isValidUserWalletSetup

```vyper
@view
@external 
def isValidUserWalletSetup(_owner: address, _agent: address) -> bool:
```

Checks if the provided owner and agent addresses form a valid wallet setup.

**Parameters:**
- `_owner`: The address that will own the wallet
- `_agent`: The address that will be the agent (can be empty)

**Returns:**
- True if the setup is valid, False otherwise

### createUserWallet

```vyper
@external
def createUserWallet(_owner: address = msg.sender, _agent: address = empty(address)) -> address:
```

Creates a new User Wallet with specified owner and optional agent.

**Parameters:**
- `_owner`: The address that will own the wallet (defaults to msg.sender)
- `_agent`: The address that will be the agent (defaults to empty address, can add this later)

**Returns:**
- The address of the newly created wallet, or empty address if setup is invalid

**Events Emitted:**
- `UserWalletCreated(mainAddr, configAddr, owner, agent, creator)`

**Requirements:**
- The factory must be activated
- Valid wallet setup (owner != empty address, owner != agent)
- If whitelist is enforced, msg.sender must be whitelisted
- Number of user wallets must be less than the allowed limit

### isValidUserWalletTemplate

```vyper
@view
@external 
def isValidUserWalletTemplate(_newAddr: address) -> bool:
```

Checks if a given address is valid to be used as a new user wallet template.

**Parameters:**
- `_newAddr`: The address to validate as a potential new template

**Returns:**
- True if the address can be used as a template, False otherwise

### setUserWalletTemplate

```vyper
@external
def setUserWalletTemplate(_addr: address) -> bool:
```

Sets a new main wallet template address for future wallet deployments.

**Parameters:**
- `_addr`: The address of the new template to use

**Returns:**
- True if template was successfully updated, False if invalid address

**Events Emitted:**
- `UserWalletTemplateSet(template, version)`

**Requirements:**
- Caller must be the governor
- Template address must be a valid contract and different from current template

### isValidUserWalletConfigTemplate

```vyper
@view
@external 
def isValidUserWalletConfigTemplate(_newAddr: address) -> bool:
```

Checks if a given address is valid to be used as a new user wallet config template.

**Parameters:**
- `_newAddr`: The address to validate as a potential new template

**Returns:**
- True if the address can be used as a template, False otherwise

### setUserWalletConfigTemplate

```vyper
@external
def setUserWalletConfigTemplate(_addr: address) -> bool:
```

Sets a new wallet config template address for future wallet deployments.

**Parameters:**
- `_addr`: The address of the new template to use

**Returns:**
- True if template was successfully updated, False if invalid address

**Events Emitted:**
- `UserWalletConfigTemplateSet(template, version)`

**Requirements:**
- Caller must be the governor
- Template address must be a valid contract and different from current template

### isValidAgentSetup

```vyper
@view
@external 
def isValidAgentSetup(_owner: address) -> bool:
```

Checks if the provided owner address forms a valid agent setup.

**Parameters:**
- `_owner`: The address that will own the agent

**Returns:**
- True if the setup is valid, False otherwise

### createAgent

```vyper
@external
def createAgent(_owner: address = msg.sender) -> address:
```

Creates a new Agent with specified owner.

**Parameters:**
- `_owner`: The address that will own the agent (defaults to msg.sender)

**Returns:**
- The address of the newly created agent, or empty address if setup is invalid

**Events Emitted:**
- `AgentCreated(agent, owner, creator)`

**Requirements:**
- The factory must be activated
- Valid agent setup (owner != empty address)
- If whitelist is enforced, msg.sender must be whitelisted
- Number of agents must be less than the allowed limit

### isValidAgentTemplate

```vyper
@view
@external 
def isValidAgentTemplate(_newAddr: address) -> bool:
```

Checks if a given address is valid to be used as a new agent template.

**Parameters:**
- `_newAddr`: The address to validate as a potential new template

**Returns:**
- True if the address can be used as a template, False otherwise

### setAgentTemplate

```vyper
@external
def setAgentTemplate(_addr: address) -> bool:
```

Sets a new agent template address for future agent deployments.

**Parameters:**
- `_addr`: The address of the new template to use

**Returns:**
- True if template was successfully updated, False if invalid address

**Events Emitted:**
- `AgentTemplateSet(template, version)`

**Requirements:**
- Caller must be the governor
- Template address must be a valid contract and different from current template

### isValidTrialFundsData

```vyper
@view
@external 
def isValidTrialFundsData(_asset: address, _amount: uint256) -> bool:
```

Checks if the provided asset and amount form a valid trial funds setup.

**Parameters:**
- `_asset`: The address of the asset to validate
- `_amount`: The amount of the asset to validate

**Returns:**
- True if the setup is valid, False otherwise

### setTrialFundsData

```vyper
@external
def setTrialFundsData(_asset: address, _amount: uint256) -> bool:
```

Sets the trial funds asset and amount for new user wallets.

**Parameters:**
- `_asset`: The address of the trial funds asset
- `_amount`: The amount of trial funds to provide

**Returns:**
- True if trial funds data was successfully updated

**Events Emitted:**
- `TrialFundsDataSet(asset, amount)`

**Requirements:**
- Caller must be the governor

### setWhitelist

```vyper
@external
def setWhitelist(_addr: address, _shouldWhitelist: bool) -> bool:
```

Sets the whitelist status for a given address.

**Parameters:**
- `_addr`: The address to set the whitelist status for
- `_shouldWhitelist`: True to whitelist, False to unwhitelist

**Returns:**
- True if the whitelist status was successfully updated

**Events Emitted:**
- `WhitelistSet(addr, shouldWhitelist)`

**Requirements:**
- Caller must be the governor

### setShouldEnforceWhitelist

```vyper
@external
def setShouldEnforceWhitelist(_shouldEnforce: bool) -> bool:
```

Sets whether to enforce the whitelist for agent/wallet creation.

**Parameters:**
- `_shouldEnforce`: True to enforce whitelist, False to disable

**Returns:**
- True if the whitelist enforcement state was successfully updated

**Events Emitted:**
- `ShouldEnforceWhitelistSet(shouldEnforce)`

**Requirements:**
- Caller must be the governor

### setNumUserWalletsAllowed

```vyper
@external
def setNumUserWalletsAllowed(_numAllowed: uint256 = max_value(uint256)) -> bool:
```

Sets the maximum number of user wallets allowed.

**Parameters:**
- `_numAllowed`: The new maximum number of user wallets allowed

**Returns:**
- True if the maximum number was successfully updated

**Events Emitted:**
- `NumUserWalletsAllowedSet(numAllowed)`

**Requirements:**
- Caller must be the governor

### setNumAgentsAllowed

```vyper
@external
def setNumAgentsAllowed(_numAllowed: uint256 = max_value(uint256)) -> bool:
```

Sets the maximum number of agents allowed.

**Parameters:**
- `_numAllowed`: The new maximum number of agents allowed

**Returns:**
- True if the maximum number was successfully updated

**Events Emitted:**
- `NumAgentsAllowedSet(numAllowed)`

**Requirements:**
- Caller must be the governor

### setAgentBlacklist

```vyper
@external
def setAgentBlacklist(_agentAddr: address, _shouldBlacklist: bool) -> bool:
```

Sets the blacklist status for a given agent address.

**Parameters:**
- `_agentAddr`: The address to set the blacklist status for
- `_shouldBlacklist`: True to blacklist, False to unblacklist

**Returns:**
- True if the blacklist status was successfully updated

**Events Emitted:**
- `AgentBlacklistSet(agentAddr, shouldBlacklist)`

**Requirements:**
- Caller must be the governor

### recoverFunds

```vyper
@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
```

Recovers funds from the factory.

**Parameters:**
- `_asset`: The address of the asset to recover
- `_recipient`: The address to send the funds to

**Returns:**
- True if the funds were successfully recovered

**Events Emitted:**
- `AgentFactoryFundsRecovered(asset, recipient, balance)`

**Requirements:**
- Caller must be the governor
- Asset and recipient addresses must not be empty
- Balance must be greater than zero

### recoverTrialFunds

```vyper
@external
def recoverTrialFunds(_wallet: address, _opportunities: DynArray[TrialFundsOpp, MAX_LEGOS] = []) -> bool:
```

Recovers trial funds from a wallet.

**Parameters:**
- `_wallet`: The address of the wallet to recover funds from
- `_opportunities`: The list of opportunities to recover funds for

**Returns:**
- True if the funds were successfully recovered

**Requirements:**
- Caller must be the governor

### activate

```vyper
@external
def activate(_shouldActivate: bool):
```

Enables or disables the factory's ability to create new wallets.

**Parameters:**
- `_shouldActivate`: True to activate the factory, False to deactivate

**Events Emitted:**
- `AgentFactoryActivated(isActivated)`

**Requirements:**
- Caller must be the governor 