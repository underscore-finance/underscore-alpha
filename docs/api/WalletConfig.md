# UserWalletConfigTemplate (WalletConfig)

The UserWalletConfigTemplate contract manages wallet configuration settings, including authorized agents and their permissions, protocol and asset allowlists, and user preferences.

**Source:** `contracts/core/templates/UserWalletConfigTemplate.vy`

## Flags

### ActionType

```vyper
flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP
    CONVERSION
    ADD_LIQ
    REMOVE_LIQ
    CLAIM_REWARDS
    BORROW
    REPAY
```

Flag defining types of actions that agents can perform.

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
    agentFactory: address
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

### CanTransferToAltOwnerWalletsSet

```vyper
event CanTransferToAltOwnerWalletsSet:
    canTransfer: bool
```

Emitted when the ability to transfer to alternate owner wallets is set.

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
    cancelledBy: indexed(address)
```

Emitted when a pending whitelist address is cancelled.

### WhitelistAddrRemoved

```vyper
event WhitelistAddrRemoved:
    addr: indexed(address)
```

Emitted when an address is removed from the whitelist.

### WhitelistAddrSetViaMigration

```vyper
event WhitelistAddrSetViaMigration:
    addr: indexed(address)
```

Emitted when a whitelist address is set via migration.

### ReserveAssetSet

```vyper
event ReserveAssetSet:
    asset: indexed(address)
    amount: uint256
```

Emitted when a reserve asset is set.

### CanWalletBeAmbassadorSet

```vyper
event CanWalletBeAmbassadorSet:
    canWalletBeAmbassador: bool
```

Emitted when the ability for wallet to be an ambassador is set.

### AmbassadorForwarderSet

```vyper
event AmbassadorForwarderSet:
    addr: indexed(address)
```

Emitted when the ambassador forwarder address is set.

### FundsRecovered

```vyper
event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256
```

Emitted when funds are recovered from the contract.

### UserWalletStartMigration

```vyper
event UserWalletStartMigration:
    newWallet: indexed(address)
    numAssetsToMigrate: uint256
    numWhitelistToMigrate: uint256
```

Emitted when a wallet migration is started.

### UserWalletFinishMigration

```vyper
event UserWalletFinishMigration:
    oldWallet: indexed(address)
    numWhitelistMigrated: uint256
    numVaultTokensMigrated: uint256
    numAssetsMigrated: uint256
```

Emitted when a wallet migration is finished.

## Storage Variables

### wallet

```vyper
wallet: public(address)
```

The address of the associated wallet.

### didSetWallet

```vyper
didSetWallet: public(bool)
```

Whether the wallet address has been set.

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

Mapping from recipient address to whether it is allowed for transfers.

### pendingWhitelist

```vyper
pendingWhitelist: public(HashMap[address, PendingWhitelist])
```

Mapping from address to pending whitelist information.

### canTransferToAltOwnerWallets

```vyper
canTransferToAltOwnerWallets: public(bool)
```

Whether transfers to other wallets owned by the same owner are allowed.

### canWalletBeAmbassador

```vyper
canWalletBeAmbassador: public(bool)
```

Whether this wallet can serve as an ambassador.

### ambassadorForwarder

```vyper
ambassadorForwarder: public(address)
```

Address to forward ambassador rewards to.

### myAmbassador

```vyper
myAmbassador: public(address)
```

Address of the ambassador who invited this wallet's owner.

### didMigrateIn

```vyper
didMigrateIn: public(bool)
```

Whether this wallet migrated in from another wallet.

### didMigrateOut

```vyper
didMigrateOut: public(bool)
```

Whether this wallet migrated out to another wallet.

### isVaultToken

```vyper
isVaultToken: public(HashMap[address, bool])
```

Mapping from asset address to whether it is a vault token.

### vaultTokenAmounts

```vyper
vaultTokenAmounts: public(HashMap[address, uint256])
```

Mapping from vault token to amount.

### depositedAmounts

```vyper
depositedAmounts: public(HashMap[address, uint256])
```

Mapping from vault token to deposited underlying asset amount.

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

Address of the address registry.

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

### MAX_MIGRATION_ASSETS

```vyper
MAX_MIGRATION_ASSETS: constant(uint256) = 40
```

Maximum number of assets that can be migrated.

### MAX_MIGRATION_WHITELIST

```vyper
MAX_MIGRATION_WHITELIST: constant(uint256) = 20
```

Maximum number of whitelist addresses that can be migrated.

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
API_VERSION: constant(String[28]) = "0.0.3"
```

API version of the contract.

## External Functions

### setWallet

```vyper
@external
def setWallet(_wallet: address) -> bool:
```

Sets the associated wallet address for this config contract.

**Parameters:**

- `_wallet`: The address of the wallet contract to be associated with this config

**Returns:**

- True if the wallet was successfully set

**Requirements:**

- Wallet has not been set yet
- Wallet address is valid
- Caller must be the agent factory

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
def canAgentAccess(
    _agent: address,
    _action: ActionType,
    _assets: DynArray[address, MAX_ASSETS],
    _legoIds: DynArray[uint256, MAX_LEGOS],
) -> bool:
```

Checks if an agent has permission to perform a specific action with given assets and lego IDs.

**Parameters:**

- `_agent`: The address of the agent
- `_action`: The type of action being attempted
- `_assets`: Array of asset addresses involved in the action
- `_legoIds`: Array of lego IDs involved in the action

**Returns:**

- True if the agent has permission to perform the action, False otherwise

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

Gets the protocol subscription status.

**Returns:**

- Subscription payment information for the protocol

### canMakeSubscriptionPayments

```vyper
@view
@external
def canMakeSubscriptionPayments(_agent: address) -> (bool, bool):
```

Checks if the wallet has sufficient funds for protocol and agent subscriptions.

**Parameters:**

- `_agent`: The address of the agent

**Returns:**

- Tuple of (canPayProtocolSub, canPayAgentSub)

### handleSubscriptionsAndPermissions

```vyper
@external
def handleSubscriptionsAndPermissions(
    _agent: address,
    _action: ActionType,
    _assets: DynArray[address, MAX_ASSETS],
    _legoIds: DynArray[uint256, MAX_LEGOS],
    _cd: CoreData,
) -> (SubPaymentInfo, SubPaymentInfo):
```

Handles subscription payments and permission checks for an agent action.

**Parameters:**

- `_agent`: The address of the agent
- `_action`: The type of action being attempted
- `_assets`: Array of asset addresses involved in the action
- `_legoIds`: Array of lego IDs involved in the action
- `_cd`: Core data structure with system addresses

**Returns:**

- Tuple of (protocolSub, agentSub) payment information

**Requirements:**

- Caller must be the wallet contract
- Agent must have permission for the action, assets, and legos

### addAgent

```vyper
@external
def addAgent(_agent: address) -> bool:
```

Adds a new agent to the wallet.

**Parameters:**

- `_agent`: The address of the agent to add

**Returns:**

- True if the agent was successfully added

**Requirements:**

- Caller must be the owner
- Agent address must be valid and not already active

### disableAgent

```vyper
@external
def disableAgent(_agent: address) -> bool:
```

Disables an agent, removing its permissions.

**Parameters:**

- `_agent`: The address of the agent to disable

**Returns:**

- True if the agent was successfully disabled

**Requirements:**

- Caller must be the owner
- Agent must be active

### setAgentAllowedAssets

```vyper
@external
def setAgentAllowedAssets(_agent: address, _assets: DynArray[address, MAX_ASSETS]) -> bool:
```

Sets the allowed assets for an agent.

**Parameters:**

- `_agent`: The address of the agent
- `_assets`: Array of asset addresses to allow

**Returns:**

- True if assets were successfully set

**Requirements:**

- Caller must be the owner
- Agent must be active
- Assets must be valid

### setAgentAllowedLegoIds

```vyper
@external
def setAgentAllowedLegoIds(_agent: address, _legoIds: DynArray[uint256, MAX_LEGOS]) -> bool:
```

Sets the allowed lego IDs for an agent.

**Parameters:**

- `_agent`: The address of the agent
- `_legoIds`: Array of lego IDs to allow

**Returns:**

- True if lego IDs were successfully set

**Requirements:**

- Caller must be the owner
- Agent must be active
- Lego IDs must be valid

### setAgentAllowedActions

```vyper
@external
def setAgentAllowedActions(
    _agent: address,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canRebalance: bool,
    _canTransfer: bool,
    _canSwap: bool,
    _canConvert: bool,
    _canAddLiq: bool,
    _canRemoveLiq: bool,
    _canClaimRewards: bool,
    _canBorrow: bool,
    _canRepay: bool
) -> bool:
```

Sets the allowed actions for an agent.

**Parameters:**

- `_agent`: The address of the agent
- Action permission parameters for each action type

**Returns:**

- True if actions were successfully set

**Requirements:**

- Caller must be the owner
- Agent must be active

### addAddressToWhitelist

```vyper
@external
def addAddressToWhitelist(_addr: address) -> bool:
```

Initiates adding an address to the whitelist.

**Parameters:**

- `_addr`: The address to add to the whitelist

**Returns:**

- True if the process was successfully initiated

**Requirements:**

- Caller must be the owner
- Address must be valid and not already on the whitelist

### confirmAddressToWhitelist

```vyper
@external
def confirmAddressToWhitelist(_addr: address) -> bool:
```

Confirms adding an address to the whitelist after the required delay.

**Parameters:**

- `_addr`: The address to confirm

**Returns:**

- True if the address was successfully confirmed

**Requirements:**

- Caller must be the owner
- Address must have a pending whitelist entry
- Required delay period has passed

### removeAddressFromWhitelist

```vyper
@external
def removeAddressFromWhitelist(_addr: address) -> bool:
```

Removes an address from the whitelist.

**Parameters:**

- `_addr`: The address to remove

**Returns:**

- True if the address was successfully removed

**Requirements:**

- Caller must be the owner
- Address must be on the whitelist

### cancelPendingWhitelist

```vyper
@external
def cancelPendingWhitelist(_addr: address) -> bool:
```

Cancels a pending whitelist addition.

**Parameters:**

- `_addr`: The address to cancel

**Returns:**

- True if the pending whitelist was successfully cancelled

**Requirements:**

- Caller must be the owner or have cancellation rights
- Address must have a pending whitelist entry

### setCanTransferToAltOwnerWallets

```vyper
@external
def setCanTransferToAltOwnerWallets(_canTransfer: bool) -> bool:
```

Sets whether transfers to other wallets owned by the same owner are allowed.

**Parameters:**

- `_canTransfer`: Whether to allow transfers to other owner wallets

**Returns:**

- True if the setting was successfully updated

**Requirements:**

- Caller must be the owner

### setReserveAsset

```vyper
@external
def setReserveAsset(_asset: address, _amount: uint256) -> bool:
```

Sets a reserve amount for an asset.

**Parameters:**

- `_asset`: The address of the asset
- `_amount`: The reserve amount

**Returns:**

- True if the reserve asset was successfully set

**Requirements:**

- Caller must be the owner
- Asset address must be valid

### setCanWalletBeAmbassador

```vyper
@external
def setCanWalletBeAmbassador(_canWalletBeAmbassador: bool) -> bool:
```

Sets whether this wallet can be an ambassador.

**Parameters:**

- `_canWalletBeAmbassador`: Whether the wallet can be an ambassador

**Returns:**

- True if the setting was successfully updated

**Requirements:**

- Caller must be the owner

### setAmbassadorForwarder

```vyper
@external
def setAmbassadorForwarder(_addr: address) -> bool:
```

Sets the address to forward ambassador rewards to.

**Parameters:**

- `_addr`: The address to forward rewards to

**Returns:**

- True if the forwarder was successfully set

**Requirements:**

- Caller must be the owner
- Address must be valid

### trackVaultTokenPosition

```vyper
@external
def trackVaultTokenPosition(_vaultToken: address, _vaultTokenDelta: int256, _depositedDelta: int256) -> bool:
```

Tracks changes in vault token positions.

**Parameters:**

- `_vaultToken`: The address of the vault token
- `_vaultTokenDelta`: The change in vault token amount (positive or negative)
- `_depositedDelta`: The change in deposited underlying amount (positive or negative)

**Returns:**

- True if the position was successfully tracked

**Requirements:**

- Caller must be the wallet contract
- Vault token must be valid
- Resulting balances must be non-negative

### migrateIn

```vyper
@external
def migrateIn(_prevWallet: address, _newOwner: address, _addrsToWhitelist: DynArray[address, MAX_MIGRATION_WHITELIST]) -> bool:
```

Migrates data from a previous wallet.

**Parameters:**

- `_prevWallet`: The address of the previous wallet
- `_newOwner`: The address of the new owner
- `_addrsToWhitelist`: Addresses to add to the whitelist

**Returns:**

- True if the migration was successful

**Requirements:**

- Caller must be the agent factory
- Previous wallet must be valid
- Has not already migrated in

### startMigrateOut

```vyper
@external
def startMigrateOut(_newWallet: address, _assetsToMigrate: DynArray[address, MAX_MIGRATION_ASSETS], _whitelistToMigrate: DynArray[address, MAX_MIGRATION_WHITELIST]) -> bool:
```

Starts migrating out to a new wallet.

**Parameters:**

- `_newWallet`: The address of the new wallet
- `_assetsToMigrate`: Assets to migrate
- `_whitelistToMigrate`: Whitelist addresses to migrate

**Returns:**

- True if the migration was successfully started

**Requirements:**

- Caller must be the owner
- New wallet must be valid
- Has not already migrated out

### recoveryGetVaultTokens

```vyper
@view
@external
def recoveryGetVaultTokens() -> DynArray[address, MAX_MIGRATION_ASSETS]:
```

Gets the list of vault tokens for recovery.

**Returns:**

- Array of vault token addresses

### recoveryGetVaultTokenAmount

```vyper
@view
@external
def recoveryGetVaultTokenAmount(_vaultToken: address) -> (uint256, uint256):
```

Gets the amount of a vault token and its deposited amount.

**Parameters:**

- `_vaultToken`: The address of the vault token

**Returns:**

- Tuple of (vaultTokenAmount, depositedAmount)

### recoverFunds

```vyper
@external
def recoverFunds(_asset: address, _to: address) -> uint256:
```

Recovers funds stuck in the contract.

**Parameters:**

- `_asset`: The address of the asset to recover
- `_to`: The address to send the funds to

**Returns:**

- The amount of funds recovered

**Requirements:**

- Caller must be the owner
- Asset and recipient addresses must be valid
