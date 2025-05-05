# AgentFactory API Reference

**Source:** `contracts/core/AgentFactory.vy`

The AgentFactory contract is responsible for creating and managing user wallets and agents in the Underscore system.

## Flags

### AddressTypes

```vyper
flag AddressTypes:
    USER_WALLET_TEMPLATE
    USER_WALLET_CONFIG_TEMPLATE
    AGENT_TEMPLATE
    DEFAULT_AGENT
```

Flag defining the types of address templates that can be managed.

## Data Structures

### AddressInfo

```vyper
struct AddressInfo:
    addr: address
    version: uint256
    lastModified: uint256
```

A struct containing information about a template contract.

### PendingAddress

```vyper
struct PendingAddress:
    newAddr: address
    initiatedBlock: uint256
    confirmBlock: uint256
```

A struct containing information about pending address updates.

### TrialFundsData

```vyper
struct TrialFundsData:
    asset: address
    amount: uint256
```

A struct containing information about trial funds.

### TrialFundsOpp

```vyper
struct TrialFundsOpp:
    legoId: uint256
    vaultToken: address
```

A struct containing information about a trial funds opportunity.

### TrialFundsRecovery

```vyper
struct TrialFundsRecovery:
    wallet: address
    opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]
```

A struct containing information about trial funds recovery.

## Events

### UserWalletCreated

```vyper
event UserWalletCreated:
    mainAddr: indexed(address)
    configAddr: indexed(address)
    owner: indexed(address)
    agent: address
    ambassador: address
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

### AddressUpdateInitiated

```vyper
event AddressUpdateInitiated:
    prevAddr: indexed(address)
    newAddr: indexed(address)
    confirmBlock: uint256
    addressType: AddressTypes
```

Emitted when an address update is initiated.

### AddressUpdateConfirmed

```vyper
event AddressUpdateConfirmed:
    prevAddr: indexed(address)
    newAddr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    addressType: AddressTypes
```

Emitted when an address update is confirmed.

### AddressUpdateCancelled

```vyper
event AddressUpdateCancelled:
    cancelledTemplate: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    addressType: AddressTypes
```

Emitted when an address update is cancelled.

### AddressChangeDelaySet

```vyper
event AddressChangeDelaySet:
    delayBlocks: uint256
```

Emitted when the address change delay is set.

### WhitelistSet

```vyper
event WhitelistSet:
    addr: address
    shouldWhitelist: bool
```

Emitted when an address is whitelisted or de-whitelisted.

### ShouldEnforceWhitelistSet

```vyper
event ShouldEnforceWhitelistSet:
    shouldEnforce: bool
```

Emitted when whitelist enforcement is toggled.

### NumUserWalletsAllowedSet

```vyper
event NumUserWalletsAllowedSet:
    numAllowed: uint256
```

Emitted when the number of allowed user wallets is set.

### NumAgentsAllowedSet

```vyper
event NumAgentsAllowedSet:
    numAllowed: uint256
```

Emitted when the number of allowed agents is set.

### AgentBlacklistSet

```vyper
event AgentBlacklistSet:
    agentAddr: indexed(address)
    shouldBlacklist: bool
```

Emitted when an agent is blacklisted or removed from blacklist.

### CanCriticalCancelSet

```vyper
event CanCriticalCancelSet:
    addr: indexed(address)
    canCancel: bool
```

Emitted when critical cancel permission is set for an address.

### TrialFundsDataSet

```vyper
event TrialFundsDataSet:
    asset: indexed(address)
    amount: uint256
```

Emitted when trial funds data is set.

### AmbassadorYieldBonusPaid

```vyper
event AmbassadorYieldBonusPaid:
    user: indexed(address)
    ambassador: indexed(address)
    asset: indexed(address)
    amount: uint256
    ratio: uint256
```

Emitted when ambassador yield bonus is paid.

### AmbassadorBonusRatioSet

```vyper
event AmbassadorBonusRatioSet:
    ratio: uint256
```

Emitted when ambassador bonus ratio is set.

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

### isUserWalletLocal

```vyper
isUserWalletLocal: public(HashMap[address, bool])
```

Mapping to track if an address is a user wallet created by this factory.

### numUserWallets

```vyper
numUserWallets: public(uint256)
```

The total number of user wallets created by this factory.

### isAgentLocal

```vyper
isAgentLocal: public(HashMap[address, bool])
```

Mapping to track if an address is an agent created by this factory.

### numAgents

```vyper
numAgents: public(uint256)
```

The total number of agents created by this factory.

### addressInfo

```vyper
addressInfo: public(HashMap[AddressTypes, AddressInfo])
```

Information about template addresses.

### pendingAddress

```vyper
pendingAddress: public(HashMap[AddressTypes, PendingAddress])
```

Information about pending address updates.

### addressChangeDelay

```vyper
addressChangeDelay: public(uint256)
```

The delay period for address changes, in blocks.

### ambassadorBonusRatio

```vyper
ambassadorBonusRatio: public(uint256)
```

The ratio for ambassador bonuses.

### trialFundsData

```vyper
trialFundsData: public(TrialFundsData)
```

Information about the trial funds asset and amount for new user wallets.

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

### agentBlacklist

```vyper
agentBlacklist: public(HashMap[address, bool])
```

Mapping to track if an agent is blacklisted.

### canCriticalCancel

```vyper
canCriticalCancel: public(HashMap[address, bool])
```

Mapping to track addresses that can cancel critical updates.

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

### MIN_OWNER_CHANGE_DELAY

```vyper
MIN_OWNER_CHANGE_DELAY: public(immutable(uint256))
```

The minimum delay for owner changes, in blocks.

### MAX_OWNER_CHANGE_DELAY

```vyper
MAX_OWNER_CHANGE_DELAY: public(immutable(uint256))
```

The maximum delay for owner changes, in blocks.

### MIN_ADDRESS_CHANGE_DELAY

```vyper
MIN_ADDRESS_CHANGE_DELAY: public(immutable(uint256))
```

The minimum delay for address changes, in blocks.

### MAX_ADDRESS_CHANGE_DELAY

```vyper
MAX_ADDRESS_CHANGE_DELAY: public(immutable(uint256))
```

The maximum delay for address changes, in blocks.

## Constants

### HUNDRED_PERCENT

```vyper
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
```

Represents 100.00% in basis points.

### MAX_RECOVERIES

```vyper
MAX_RECOVERIES: constant(uint256) = 100
```

Maximum number of recovery operations.

### MAX_LEGOS

```vyper
MAX_LEGOS: constant(uint256) = 20
```

Maximum number of legos.

## External Functions

### isUserWallet

```vyper
@view
@external
def isUserWallet(_addr: address) -> bool:
```

Checks if a given address is a user wallet within Underscore Protocol.

**Parameters:**

- `_addr`: The address to check

**Returns:**

- True if the address is a user wallet, False otherwise

### createUserWallet

```vyper
@external
def createUserWallet(
    _owner: address = msg.sender,
    _ambassador: address = empty(address),
    _shouldUseTrialFunds: bool = True,
) -> address:
```

Creates a new User Wallet with specified owner and optional ambassador.

**Parameters:**

- `_owner`: The address that will own the wallet (defaults to msg.sender)
- `_ambassador`: The address of the ambassador who invited the user (defaults to empty address)
- `_shouldUseTrialFunds`: Whether to use trial funds (defaults to True)

**Returns:**

- The address of the newly created wallet, or empty address if setup is invalid

**Requirements:**

- The factory must be activated
- Valid wallet setup (templates must be set, valid owner address)
- If whitelist is enforced, msg.sender must be whitelisted
- Number of user wallets must be less than the allowed limit

### isAgent

```vyper
@view
@external
def isAgent(_addr: address) -> bool:
```

Checks if a given address is an agent within Underscore Protocol.

**Parameters:**

- `_addr`: The address to check

**Returns:**

- True if the address is an agent, False otherwise

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

**Requirements:**

- The factory must be activated
- Valid agent setup (template must be set, valid owner address)
- If whitelist is enforced, msg.sender must be whitelisted
- Number of agents must be less than the allowed limit

### initiateUserWalletTemplateUpdate

```vyper
@external
def initiateUserWalletTemplateUpdate(_newAddr: address) -> bool:
```

Initiates an update to the user wallet template.

**Parameters:**

- `_newAddr`: The new template address

**Returns:**

- True if the update was initiated successfully

**Requirements:**

- Caller must be authorized to govern
- New address must be valid and different from current template

### confirmUserWalletTemplateUpdate

```vyper
@external
def confirmUserWalletTemplateUpdate() -> bool:
```

Confirms a pending user wallet template update.

**Returns:**

- True if the update was confirmed successfully

**Requirements:**

- Caller must be authorized to govern
- A pending update must exist
- The confirmation delay must have passed

### cancelUserWalletTemplateUpdate

```vyper
@external
def cancelUserWalletTemplateUpdate() -> bool:
```

Cancels a pending user wallet template update.

**Returns:**

- True if the update was cancelled successfully

**Requirements:**

- Caller must be authorized to govern
- A pending update must exist

### getUserWalletTemplateAddr

```vyper
@view
@external
def getUserWalletTemplateAddr() -> address:
```

Gets the current user wallet template address.

**Returns:**

- The current user wallet template address

### getUserWalletTemplateInfo

```vyper
@view
@external
def getUserWalletTemplateInfo() -> AddressInfo:
```

Gets information about the current user wallet template.

**Returns:**

- Information about the current user wallet template

### getPendingUserWalletTemplateUpdate

```vyper
@view
@external
def getPendingUserWalletTemplateUpdate() -> PendingAddress:
```

Gets information about a pending user wallet template update.

**Returns:**

- Information about the pending update, if any

### hasPendingUserWalletTemplateUpdate

```vyper
@view
@external
def hasPendingUserWalletTemplateUpdate() -> bool:
```

Checks if there is a pending user wallet template update.

**Returns:**

- True if there is a pending update, False otherwise

### initiateUserWalletConfigTemplateUpdate

```vyper
@external
def initiateUserWalletConfigTemplateUpdate(_newAddr: address) -> bool:
```

Initiates an update to the user wallet config template.

**Parameters:**

- `_newAddr`: The new template address

**Returns:**

- True if the update was initiated successfully

**Requirements:**

- Caller must be authorized to govern
- New address must be valid and different from current template

### confirmUserWalletConfigTemplateUpdate

```vyper
@external
def confirmUserWalletConfigTemplateUpdate() -> bool:
```

Confirms a pending user wallet config template update.

**Returns:**

- True if the update was confirmed successfully

**Requirements:**

- Caller must be authorized to govern
- A pending update must exist
- The confirmation delay must have passed

### cancelUserWalletConfigTemplateUpdate

```vyper
@external
def cancelUserWalletConfigTemplateUpdate() -> bool:
```

Cancels a pending user wallet config template update.

**Returns:**

- True if the update was cancelled successfully

**Requirements:**

- Caller must be authorized to govern
- A pending update must exist

### getUserWalletConfigTemplateAddr

```vyper
@view
@external
def getUserWalletConfigTemplateAddr() -> address:
```

Gets the current user wallet config template address.

**Returns:**

- The current user wallet config template address

### getUserWalletConfigTemplateInfo

```vyper
@view
@external
def getUserWalletConfigTemplateInfo() -> AddressInfo:
```

Gets information about the current user wallet config template.

**Returns:**

- Information about the current user wallet config template

### getPendingUserWalletConfigTemplateUpdate

```vyper
@view
@external
def getPendingUserWalletConfigTemplateUpdate() -> PendingAddress:
```

Gets information about a pending user wallet config template update.

**Returns:**

- Information about the pending update, if any

### hasPendingUserWalletConfigTemplateUpdate

```vyper
@view
@external
def hasPendingUserWalletConfigTemplateUpdate() -> bool:
```

Checks if there is a pending user wallet config template update.

**Returns:**

- True if there is a pending update, False otherwise

### initiateAgentTemplateUpdate

```vyper
@external
def initiateAgentTemplateUpdate(_newAddr: address) -> bool:
```

Initiates an update to the agent template.

**Parameters:**

- `_newAddr`: The new template address

**Returns:**

- True if the update was initiated successfully

**Requirements:**

- Caller must be authorized to govern
- New address must be valid and different from current template

### confirmAgentTemplateUpdate

```vyper
@external
def confirmAgentTemplateUpdate() -> bool:
```

Confirms a pending agent template update.

**Returns:**

- True if the update was confirmed successfully

**Requirements:**

- Caller must be authorized to govern
- A pending update must exist
- The confirmation delay must have passed

### cancelAgentTemplateUpdate

```vyper
@external
def cancelAgentTemplateUpdate() -> bool:
```

Cancels a pending agent template update.

**Returns:**

- True if the update was cancelled successfully

**Requirements:**

- Caller must be authorized to govern
- A pending update must exist

### getAgentTemplateAddr

```vyper
@view
@external
def getAgentTemplateAddr() -> address:
```

Gets the current agent template address.

**Returns:**

- The current agent template address

### getAgentTemplateInfo

```vyper
@view
@external
def getAgentTemplateInfo() -> AddressInfo:
```

Gets information about the current agent template.

**Returns:**

- Information about the current agent template

### getPendingAgentTemplateUpdate

```vyper
@view
@external
def getPendingAgentTemplateUpdate() -> PendingAddress:
```

Gets information about a pending agent template update.

**Returns:**

- Information about the pending update, if any

### hasPendingAgentTemplateUpdate

```vyper
@view
@external
def hasPendingAgentTemplateUpdate() -> bool:
```

Checks if there is a pending agent template update.

**Returns:**

- True if there is a pending update, False otherwise

### payAmbassadorYieldBonus

```vyper
@external
def payAmbassadorYieldBonus(_ambassador: address, _asset: address, _amount: uint256) -> bool:
```

Pays yield bonus to an ambassador.

**Parameters:**

- `_ambassador`: The ambassador address
- `_asset`: The asset to pay
- `_amount`: The amount to pay

**Returns:**

- True if the payment was successful

### setTrialFundsData

```vyper
@external
def setTrialFundsData(_asset: address, _amount: uint256) -> bool:
```

Sets the trial funds data.

**Parameters:**

- `_asset`: The trial funds asset
- `_amount`: The trial funds amount

**Returns:**

- True if the data was set successfully

**Requirements:**

- Caller must be authorized to govern

### setAddressChangeDelay

```vyper
@external
def setAddressChangeDelay(_delayBlocks: uint256) -> bool:
```

Sets the delay period for address changes.

**Parameters:**

- `_delayBlocks`: The delay period in blocks

**Returns:**

- True if the delay was set successfully

**Requirements:**

- Caller must be authorized to govern
- Delay must be within allowed range

### setAmbassadorBonusRatio

```vyper
@external
def setAmbassadorBonusRatio(_ratio: uint256) -> bool:
```

Sets the ambassador bonus ratio.

**Parameters:**

- `_ratio`: The ratio value

**Returns:**

- True if the ratio was set successfully

**Requirements:**

- Caller must be authorized to govern
- Ratio must be valid

### recoverFunds

```vyper
@external
def recoverFunds(_asset: address, _recipient: address = empty(address)) -> bool:
```

Recovers funds from the factory.

**Parameters:**

- `_asset`: The asset to recover
- `_recipient`: The recipient address (defaults to governance)

**Returns:**

- True if the recovery was successful

**Requirements:**

- Caller must be authorized to govern
- Valid asset and recipient

### setAgentFactoryActivated

```vyper
@external
def setAgentFactoryActivated(_isActivated: bool) -> bool:
```

Activates or deactivates the factory.

**Parameters:**

- `_isActivated`: Whether to activate the factory

**Returns:**

- True if the activation state was changed successfully

**Requirements:**

- Caller must be authorized to govern

### setNumUserWalletsAllowed

```vyper
@external
def setNumUserWalletsAllowed(_numAllowed: uint256) -> bool:
```

Sets the maximum number of user wallets allowed.

**Parameters:**

- `_numAllowed`: The maximum number allowed

**Returns:**

- True if the limit was set successfully

**Requirements:**

- Caller must be authorized to govern

### setNumAgentsAllowed

```vyper
@external
def setNumAgentsAllowed(_numAllowed: uint256) -> bool:
```

Sets the maximum number of agents allowed.

**Parameters:**

- `_numAllowed`: The maximum number allowed

**Returns:**

- True if the limit was set successfully

**Requirements:**

- Caller must be authorized to govern

### setWhitelist

```vyper
@external
def setWhitelist(_addr: address, _shouldWhitelist: bool) -> bool:
```

Adds or removes an address from the whitelist.

**Parameters:**

- `_addr`: The address to whitelist or de-whitelist
- `_shouldWhitelist`: Whether to whitelist the address

**Returns:**

- True if the whitelist was updated successfully

**Requirements:**

- Caller must be authorized to govern

### setShouldEnforceWhitelist

```vyper
@external
def setShouldEnforceWhitelist(_shouldEnforce: bool) -> bool:
```

Sets whether to enforce the whitelist.

**Parameters:**

- `_shouldEnforce`: Whether to enforce the whitelist

**Returns:**

- True if the setting was changed successfully

**Requirements:**

- Caller must be authorized to govern

### setAgentBlacklist

```vyper
@external
def setAgentBlacklist(_agentAddr: address, _shouldBlacklist: bool) -> bool:
```

Adds or removes an agent from the blacklist.

**Parameters:**

- `_agentAddr`: The agent address
- `_shouldBlacklist`: Whether to blacklist the agent

**Returns:**

- True if the blacklist was updated successfully

**Requirements:**

- Caller must be authorized to govern

### setCanCriticalCancel

```vyper
@external
def setCanCriticalCancel(_addr: address, _canCancel: bool) -> bool:
```

Sets whether an address can cancel critical updates.

**Parameters:**

- `_addr`: The address
- `_canCancel`: Whether the address can cancel critical updates

**Returns:**

- True if the setting was changed successfully

**Requirements:**

- Caller must be authorized to govern
