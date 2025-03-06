# WalletConfig

The WalletConfig contract manages wallet configuration settings, including authorized agents and their permissions, protocol and asset allowlists, and user preferences.

**Source:** `contracts/core/WalletConfig.vy`

## Structs

### AgentInfo

```vyper
struct AgentInfo:
    isActive: bool
    installBlock: uint256
    paidThroughBlock: uint256
    allowedAssets: DynArray[address, MAX_ASSETS]
    allowedLegoIds: DynArray[uint256, MAX_LEGOS]
    allowedActions: AllowedActions
```

Structure containing information about an agent's permissions and subscription status.

### PendingWhitelist

```vyper
struct PendingWhitelist:
    initiatedBlock: uint256
    confirmBlock: uint256
```

Structure containing information about a pending whitelist address.

### CoreData

```vyper
struct CoreData:
    owner: address
    wallet: address
    walletConfig: address
    addyRegistry: address
    legoRegistry: address
    priceSheets: address
    oracleRegistry: address
    trialFundsAsset: address
    trialFundsInitialAmount: uint256
```

Structure containing core contract addresses and data.

### SubPaymentInfo

```vyper
struct SubPaymentInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    didChange: bool
```

Structure containing subscription payment details.

### ProtocolSub

```vyper
struct ProtocolSub:
    installBlock: uint256
    paidThroughBlock: uint256
```

Structure containing protocol subscription information.

### AllowedActions

```vyper
struct AllowedActions:
    isSet: bool
    canDeposit: bool
    canWithdraw: bool
    canRebalance: bool
    canTransfer: bool
    canSwap: bool
    canConvert: bool
    canAddLiq: bool
    canRemoveLiq: bool
    canClaimRewards: bool
    canBorrow: bool
    canRepay: bool
```

Structure containing the actions an agent is allowed to perform.

### ReserveAsset

```vyper
struct ReserveAsset:
    asset: address
    amount: uint256
```

Structure containing information about a reserve asset.

### SubscriptionInfo

```vyper
struct SubscriptionInfo:
    asset: address
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
```

Structure containing subscription pricing information.

### PendingOwner

```vyper
struct PendingOwner:
    newOwner: address
    initiatedBlock: uint256
    confirmBlock: uint256
```

Structure containing information about a pending ownership change.

## Events

### AgentAdded

```vyper
event AgentAdded:
    agent: indexed(address)
    allowedAssets: uint256
    allowedLegoIds: uint256
```

Emitted when an agent is added to the wallet.

### AgentModified

```vyper
event AgentModified:
    agent: indexed(address)
    allowedAssets: uint256
    allowedLegoIds: uint256
```

Emitted when an agent's settings are modified.

### AgentDisabled

```vyper
event AgentDisabled:
    agent: indexed(address)
    prevAllowedAssets: uint256
    prevAllowedLegoIds: uint256
```

Emitted when an agent is disabled.

### LegoIdAddedToAgent

```vyper
event LegoIdAddedToAgent:
    agent: indexed(address)
    legoId: indexed(uint256)
```

Emitted when a lego ID is added to an agent's allowed legos.

### AssetAddedToAgent

```vyper
event AssetAddedToAgent:
    agent: indexed(address)
    asset: indexed(address)
```

Emitted when an asset is added to an agent's allowed assets.

### AllowedActionsModified

```vyper
event AllowedActionsModified:
    agent: indexed(address)
    canDeposit: bool
    canWithdraw: bool
    canRebalance: bool
    canTransfer: bool
    canSwap: bool
    canConvert: bool
    canAddLiq: bool
    canRemoveLiq: bool
    canClaimRewards: bool
    canBorrow: bool
    canRepay: bool
```

Emitted when an agent's allowed actions are modified.

### WhitelistAddrPending

```vyper
event WhitelistAddrPending:
    addr: indexed(address)
    confirmBlock: uint256
```

Emitted when an address is pending addition to the whitelist.

### WhitelistAddrConfirmed

```vyper
event WhitelistAddrConfirmed:
    addr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
```

Emitted when an address is confirmed on the whitelist.

### WhitelistAddrCancelled

```vyper
event WhitelistAddrCancelled:
    addr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
```

Emitted when a pending whitelist address is cancelled.

### WhitelistAddrRemoved

```vyper
event WhitelistAddrRemoved:
    addr: indexed(address)
```

Emitted when an address is removed from the whitelist.

### ReserveAssetSet

```vyper
event ReserveAssetSet:
    asset: indexed(address)
    amount: uint256
```

Emitted when a reserve asset is set.

### OwnershipChangeInitiated

```vyper
event OwnershipChangeInitiated:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    confirmBlock: uint256
```

Emitted when an ownership change is initiated.

### OwnershipChangeConfirmed

```vyper
event OwnershipChangeConfirmed:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
```

Emitted when an ownership change is confirmed.

### OwnershipChangeCancelled

```vyper
event OwnershipChangeCancelled:
    cancelledOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
```

Emitted when an ownership change is cancelled.

### OwnershipChangeDelaySet

```vyper
event OwnershipChangeDelaySet:
    delayBlocks: uint256
```

Emitted when the ownership change delay is set.

### FundsRecovered

```vyper
event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256
```

Emitted when funds are recovered from the contract.

## Storage Variables

### wallet

```vyper
wallet: public(address)
```

The address of the associated wallet.

### owner

```vyper
owner: public(address)
```

The address of the wallet owner.

### pendingOwner

```vyper
pendingOwner: public(PendingOwner)
```

Information about a pending ownership change.

### ownershipChangeDelay

```vyper
ownershipChangeDelay: public(uint256)
```

Number of blocks to wait before ownership can be changed.

### protocolSub

```vyper
protocolSub: public(ProtocolSub)
```

Protocol subscription information.

### reserveAssets

```vyper
reserveAssets: public(HashMap[address, uint256])
```

Mapping from asset address to reserve amount.

### agentSettings

```vyper
agentSettings: public(HashMap[address, AgentInfo])
```

Mapping from agent address to agent information.

### isRecipientAllowed

```vyper
isRecipientAllowed: public(HashMap[address, bool])
```

Mapping from recipient address to whether it is allowed.

### pendingWhitelist

```vyper
pendingWhitelist: public(HashMap[address, PendingWhitelist])
```

Mapping from address to pending whitelist information.

### addyRegistry

```vyper
addyRegistry: public(address)
```

The address of the address registry.

### initialized

```vyper
initialized: public(bool)
```

Whether the contract has been initialized.

### MIN_OWNER_CHANGE_DELAY

```vyper
MIN_OWNER_CHANGE_DELAY: public(immutable(uint256))
```

Minimum allowed ownership change delay in blocks.

### MAX_OWNER_CHANGE_DELAY

```vyper
MAX_OWNER_CHANGE_DELAY: public(immutable(uint256))
```

Maximum allowed ownership change delay in blocks.

## Constants

### AGENT_FACTORY_ID

```vyper
AGENT_FACTORY_ID: constant(uint256) = 1
```

ID of the agent factory in the address registry.

### LEGO_REGISTRY_ID

```vyper
LEGO_REGISTRY_ID: constant(uint256) = 2
```

ID of the lego registry in the address registry.

### PRICE_SHEETS_ID

```vyper
PRICE_SHEETS_ID: constant(uint256) = 3
```

ID of the price sheets in the address registry.

### ORACLE_REGISTRY_ID

```vyper
ORACLE_REGISTRY_ID: constant(uint256) = 4
```

ID of the oracle registry in the address registry.

### MAX_ASSETS

```vyper
MAX_ASSETS: constant(uint256) = 25
```

Maximum number of assets an agent can have.

### MAX_LEGOS

```vyper
MAX_LEGOS: constant(uint256) = 20
```

Maximum number of legos an agent can have.

### API_VERSION

```vyper
API_VERSION: constant(String[28]) = "0.0.1"
```

API version of the contract.

## External Functions

### initialize

```vyper
@external
def initialize(_wallet: address, _addyRegistry: address, _owner: address, _initialAgent: address) -> bool:
```

Initializes a new wallet configuration.

**Parameters:**
- `_wallet`: The address of the associated wallet
- `_addyRegistry`: The address of the address registry
- `_owner`: The address of the wallet owner
- `_initialAgent`: The address of the initial agent (can be empty)

**Returns:**
- True if initialization was successful

**Requirements:**
- Contract must not be already initialized
- Valid wallet, address registry, and owner addresses
- Initial agent cannot be the owner

### apiVersion

```vyper
@pure
@external
def apiVersion() -> String[28]:
```

Returns the current API version of the contract.

**Returns:**
- The API version string

### isAgentActive

```vyper
@view
@external
def isAgentActive(_agent: address) -> bool:
```

Checks if an agent is active.

**Parameters:**
- `_agent`: The address of the agent to check

**Returns:**
- True if the agent is active, False otherwise

### canAgentAccess

```vyper
@view
@external
def canAgentAccess(_agent: address, _action: ActionType, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS]) -> bool:
```

Checks if an agent can access specific actions, assets, and lego IDs.

**Parameters:**
- `_agent`: The address of the agent
- `_action`: The action to check
- `_assets`: The assets to check
- `_legoIds`: The lego IDs to check

**Returns:**
- True if the agent can access the specified actions, assets, and lego IDs, False otherwise

### getAgentSubscriptionStatus

```vyper
@view
@external
def getAgentSubscriptionStatus(_agent: address) -> SubPaymentInfo:
```

Gets the subscription status for an agent.

**Parameters:**
- `_agent`: The address of the agent

**Returns:**
- Subscription payment information for the agent

### getProtocolSubscriptionStatus

```vyper
@view
@external
def getProtocolSubscriptionStatus() -> SubPaymentInfo:
```

Gets the subscription status for the protocol.

**Returns:**
- Subscription payment information for the protocol

### canMakeSubscriptionPayments

```vyper
@view
@external
def canMakeSubscriptionPayments(_agent: address) -> (bool, bool):
```

Checks if subscription payments can be made for the protocol and agent.

**Parameters:**
- `_agent`: The address of the agent

**Returns:**
- Tuple containing whether protocol and agent subscription payments can be made

### handleSubscriptionsAndPermissions

```vyper
@external
def handleSubscriptionsAndPermissions(_agent: address, _action: ActionType, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS], _cd: CoreData) -> (SubPaymentInfo, SubPaymentInfo):
```

Handles the subscription and permission data for the given agent and action.

**Parameters:**
- `_agent`: The address of the agent
- `_action`: The action to handle
- `_assets`: The assets to check
- `_legoIds`: The legos to check
- `_cd`: The core data

**Returns:**
- Tuple containing subscription payment information for protocol and agent

**Requirements:**
- Caller must be the wallet
- Agent must be allowed to perform the action with the specified assets and legos
- Sufficient balance for protocol and agent subscription payments

### getAvailableTxAmount

```vyper
@view
@external
def getAvailableTxAmount(_asset: address, _wantedAmount: uint256, _shouldCheckTrialFunds: bool, _cd: CoreData = empty(CoreData)) -> uint256:
```

Returns the maximum amount that can be sent from the wallet.

**Parameters:**
- `_asset`: The address of the asset to check
- `_wantedAmount`: The amount of the asset to send
- `_shouldCheckTrialFunds`: Whether to check if the asset is a trial funds asset
- `_cd`: The core data

**Returns:**
- The maximum amount that can be sent

**Requirements:**
- Available amount must be greater than zero

### addOrModifyAgent

```vyper
@nonreentrant
@external
def addOrModifyAgent(_agent: address, _allowedAssets: DynArray[address, MAX_ASSETS] = [], _allowedLegoIds: DynArray[uint256, MAX_LEGOS] = [], _allowedActions: AllowedActions = empty(AllowedActions)) -> bool:
```

Adds a new agent or modifies an existing agent's permissions.

**Parameters:**
- `_agent`: The address of the agent to add or modify
- `_allowedAssets`: List of assets the agent can interact with
- `_allowedLegoIds`: List of lego IDs the agent can use
- `_allowedActions`: The actions the agent can perform

**Returns:**
- True if the agent was successfully added or modified

**Events Emitted:**
- `AgentAdded` or `AgentModified`

**Requirements:**
- Caller must be the owner
- Agent cannot be the owner
- Agent address must be valid

### disableAgent

```vyper
@nonreentrant
@external
def disableAgent(_agent: address) -> bool:
```

Disables an existing agent.

**Parameters:**
- `_agent`: The address of the agent to disable

**Returns:**
- True if the agent was successfully disabled

**Events Emitted:**
- `AgentDisabled`

**Requirements:**
- Caller must be the owner
- Agent must be active

### addLegoIdForAgent

```vyper
@nonreentrant
@external
def addLegoIdForAgent(_agent: address, _legoId: uint256) -> bool:
```

Adds a lego ID to an agent's allowed legos.

**Parameters:**
- `_agent`: The address of the agent
- `_legoId`: The lego ID to add

**Returns:**
- True if the lego ID was successfully added

**Events Emitted:**
- `LegoIdAddedToAgent`

**Requirements:**
- Caller must be the owner
- Agent must be active
- Lego ID must be valid
- Lego ID must not already be in the agent's allowed legos

### addAssetForAgent

```vyper
@nonreentrant
@external
def addAssetForAgent(_agent: address, _asset: address) -> bool:
```

Adds an asset to an agent's allowed assets.

**Parameters:**
- `_agent`: The address of the agent
- `_asset`: The asset address to add

**Returns:**
- True if the asset was successfully added

**Events Emitted:**
- `AssetAddedToAgent`

**Requirements:**
- Caller must be the owner
- Agent must be active
- Asset address must be valid
- Asset must not already be in the agent's allowed assets

### modifyAllowedActions

```vyper
@nonreentrant
@external
def modifyAllowedActions(_agent: address, _allowedActions: AllowedActions = empty(AllowedActions)) -> bool:
```

Modifies the allowed actions for an agent.

**Parameters:**
- `_agent`: The address of the agent to modify
- `_allowedActions`: The new allowed actions

**Returns:**
- True if the allowed actions were successfully modified

**Events Emitted:**
- `AllowedActionsModified`

**Requirements:**
- Caller must be the owner
- Agent must be active

### canTransferToRecipient

```vyper
@view
@external
def canTransferToRecipient(_recipient: address) -> bool:
```

Checks if a transfer to a recipient is allowed.

**Parameters:**
- `_recipient`: The address of the recipient

**Returns:**
- True if the transfer is allowed, False otherwise

### addWhitelistAddr

```vyper
@nonreentrant
@external
def addWhitelistAddr(_addr: address):
```

Adds an address to the whitelist.

**Parameters:**
- `_addr`: The address to add to the whitelist

**Events Emitted:**
- `WhitelistAddrPending`

**Requirements:**
- Caller must be the owner
- Address must be valid
- Address cannot be the owner or the wallet
- Address must not already be whitelisted
- No pending whitelist must exist for the address

### confirmWhitelistAddr

```vyper
@nonreentrant
@external
def confirmWhitelistAddr(_addr: address):
```

Confirms a whitelist address.

**Parameters:**
- `_addr`: The address to confirm

**Events Emitted:**
- `WhitelistAddrConfirmed`

**Requirements:**
- Caller must be the owner
- Pending whitelist must exist for the address
- Confirmation block must have been reached

### cancelPendingWhitelistAddr

```vyper
@nonreentrant
@external
def cancelPendingWhitelistAddr(_addr: address):
```

Cancels a pending whitelist address.

**Parameters:**
- `_addr`: The address to cancel

**Events Emitted:**
- `WhitelistAddrCancelled`

**Requirements:**
- Caller must be the owner
- Pending whitelist must exist for the address

### removeWhitelistAddr

```vyper
@nonreentrant
@external
def removeWhitelistAddr(_addr: address):
```

Removes an address from the whitelist.

**Parameters:**
- `_addr`: The address to remove from the whitelist

**Events Emitted:**
- `WhitelistAddrRemoved`

**Requirements:**
- Caller must be the owner
- Address must be on the whitelist

### setReserveAsset

```vyper
@nonreentrant
@external
def setReserveAsset(_asset: address, _amount: uint256) -> bool:
```

Sets a reserve asset.

**Parameters:**
- `_asset`: The address of the asset to set
- `_amount`: The amount of the asset to set

**Returns:**
- True if the reserve asset was successfully set

**Events Emitted:**
- `ReserveAssetSet`

**Requirements:**
- Caller must be the owner
- Asset address must be valid

### setManyReserveAssets

```vyper
@nonreentrant
@external
def setManyReserveAssets(_assets: DynArray[ReserveAsset, MAX_ASSETS]) -> bool:
```

Sets multiple reserve assets.

**Parameters:**
- `_assets`: The array of reserve assets to set

**Returns:**
- True if the reserve assets were successfully set

**Events Emitted:**
- `ReserveAssetSet` for each asset

**Requirements:**
- Caller must be the owner
- Assets array must not be empty
- Each asset address must be valid

### hasPendingOwnerChange

```vyper
@view
@external
def hasPendingOwnerChange() -> bool:
```

Checks if there is a pending ownership change.

**Returns:**
- True if there is a pending ownership change, False otherwise

### changeOwnership

```vyper
@external
def changeOwnership(_newOwner: address):
```

Initiates a new ownership change.

**Parameters:**
- `_newOwner`: The address of the new owner

**Events Emitted:**
- `OwnershipChangeInitiated`

**Requirements:**
- Caller must be the current owner
- New owner address must be valid and different from the current owner

### confirmOwnershipChange

```vyper
@external
def confirmOwnershipChange():
```

Confirms the ownership change.

**Events Emitted:**
- `OwnershipChangeConfirmed`

**Requirements:**
- Pending owner must exist
- Confirmation block must have been reached
- Caller must be the new owner

### cancelOwnershipChange

```vyper
@external
def cancelOwnershipChange():
```

Cancels the ownership change.

**Events Emitted:**
- `OwnershipChangeCancelled`

**Requirements:**
- Caller must be the current owner
- Pending ownership change must exist

### setOwnershipChangeDelay

```vyper
@external
def setOwnershipChangeDelay(_numBlocks: uint256):
```

Sets the ownership change delay.

**Parameters:**
- `_numBlocks`: The number of blocks to wait before ownership can be changed

**Events Emitted:**
- `OwnershipChangeDelaySet`

**Requirements:**
- Caller must be the owner
- Delay must be within allowed range

### recoverFunds

```vyper
@external
def recoverFunds(_asset: address) -> bool:
```

Transfers funds from the config contract to the main wallet.

**Parameters:**
- `_asset`: The address of the asset to recover

**Returns:**
- True if the funds were recovered successfully

**Events Emitted:**
- `FundsRecovered`

**Requirements:**
- Wallet and asset addresses must be valid
- Balance must be greater than zero 