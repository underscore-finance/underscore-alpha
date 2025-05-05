# LegoRegistry

The LegoRegistry contract maintains a registry of all available "legos" (DeFi protocol integrations) in the system.

**Source:** `contracts/core/registries/LegoRegistry.vy`

## Flags

### LegoType

```vyper
flag LegoType:
    YIELD_OPP
    DEX
```

Flag defining the types of legos that can be registered.

## Structs

### VaultTokenInfo

```vyper
struct VaultTokenInfo:
    legoId: uint256
    vaultToken: address
```

Structure containing information about a vault token and its associated lego.

## Events

### LegoHelperSet

```vyper
event LegoHelperSet:
    helperAddr: indexed(address)
```

Emitted when the lego helper address is set.

## Storage Variables

### pendingLegoType

```vyper
pendingLegoType: public(HashMap[address, LegoType])
```

Mapping from lego address to its pending lego type during registration.

### legoIdToType

```vyper
legoIdToType: public(HashMap[uint256, LegoType])
```

Mapping from lego ID to lego type.

### legoHelper

```vyper
legoHelper: public(address)
```

Address of the lego helper contract.

## Constants

### MAX_VAULTS

```vyper
MAX_VAULTS: constant(uint256) = 15
```

Maximum number of vaults that can be associated with a lego.

### MAX_VAULTS_FOR_USER

```vyper
MAX_VAULTS_FOR_USER: constant(uint256) = 30
```

Maximum number of vault tokens a user can have across all legos.

## External Functions

### isYieldLego

```vyper
@view
@external
def isYieldLego(_legoId: uint256) -> bool:
```

Checks if a lego is a yield opportunity lego.

**Parameters:**

- `_legoId`: The ID of the lego to check

**Returns:**

- True if the lego is a yield opportunity lego, False otherwise

### isValidNewLegoAddr

```vyper
@view
@external
def isValidNewLegoAddr(_addr: address) -> bool:
```

Checks if an address can be registered as a new lego.

**Parameters:**

- `_addr`: The address to validate

**Returns:**

- True if the address can be registered as a new lego, False otherwise

### registerNewLego

```vyper
@external
def registerNewLego(_addr: address, _description: String[64], _legoType: LegoType) -> bool:
```

Initiates the registration process for a new Lego.

**Parameters:**

- `_addr`: The address of the Lego to register
- `_description`: A short description of the Lego (max 64 characters)
- `_legoType`: The type of Lego (YIELD_OPP or DEX)

**Returns:**

- True if the registration was successfully initiated, False if the Lego is invalid

**Requirements:**

- Caller must be the governor

### confirmNewLegoRegistration

```vyper
@external
def confirmNewLegoRegistration(_addr: address) -> uint256:
```

Confirms a pending Lego registration after the required delay period.

**Parameters:**

- `_addr`: The address of the Lego to confirm registration for

**Returns:**

- The assigned ID for the registered Lego, or 0 if confirmation fails

**Requirements:**

- Caller must be the governor
- Registration must be past the required delay period

### cancelPendingNewLego

```vyper
@external
def cancelPendingNewLego(_addr: address) -> bool:
```

Cancels a pending Lego registration.

**Parameters:**

- `_addr`: The address of the Lego whose pending registration should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governor
- A pending registration must exist for the address

### isValidLegoUpdate

```vyper
@view
@external
def isValidLegoUpdate(_legoId: uint256, _newAddr: address) -> bool:
```

Checks if a lego update operation would be valid.

**Parameters:**

- `_legoId`: The ID of the lego to update
- `_newAddr`: The proposed new address for the lego

**Returns:**

- True if the update would be valid, False otherwise

### updateLegoAddr

```vyper
@external
def updateLegoAddr(_legoId: uint256, _newAddr: address) -> bool:
```

Initiates an address update for an existing registered Lego.

**Parameters:**

- `_legoId`: The ID of the Lego to update
- `_newAddr`: The new address to set for the Lego

**Returns:**

- True if the update was successfully initiated, False if the update is invalid

**Requirements:**

- Caller must be the governor

### confirmLegoUpdate

```vyper
@external
def confirmLegoUpdate(_legoId: uint256) -> bool:
```

Confirms a pending Lego address update after the required delay period.

**Parameters:**

- `_legoId`: The ID of the Lego to confirm update for

**Returns:**

- True if the update was successfully confirmed, False if confirmation fails

**Requirements:**

- Caller must be the governor
- Update must be past the required delay period

### cancelPendingLegoUpdate

```vyper
@external
def cancelPendingLegoUpdate(_legoId: uint256) -> bool:
```

Cancels a pending Lego address update.

**Parameters:**

- `_legoId`: The ID of the Lego whose pending update should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governor
- A pending update must exist for the lego ID

### isValidLegoDisable

```vyper
@view
@external
def isValidLegoDisable(_legoId: uint256) -> bool:
```

Checks if a lego can be disabled.

**Parameters:**

- `_legoId`: The ID of the lego to check

**Returns:**

- True if the lego can be disabled, False otherwise

### disableLegoAddr

```vyper
@external
def disableLegoAddr(_legoId: uint256) -> bool:
```

Initiates the disable process for an existing registered Lego.

**Parameters:**

- `_legoId`: The ID of the Lego to disable

**Returns:**

- True if the disable was successfully initiated, False if the disable is invalid

**Requirements:**

- Caller must be the governor

### confirmLegoDisable

```vyper
@external
def confirmLegoDisable(_legoId: uint256) -> bool:
```

Confirms a pending Lego disable after the required delay period.

**Parameters:**

- `_legoId`: The ID of the Lego to confirm disable for

**Returns:**

- True if the disable was successfully confirmed, False if confirmation fails

**Requirements:**

- Caller must be the governor
- Disable must be past the required delay period

### cancelPendingLegoDisable

```vyper
@external
def cancelPendingLegoDisable(_legoId: uint256) -> bool:
```

Cancels a pending Lego disable.

**Parameters:**

- `_legoId`: The ID of the Lego whose pending disable should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governor
- A pending disable must exist for the lego ID

### setLegoChangeDelay

```vyper
@external
def setLegoChangeDelay(_numBlocks: uint256) -> bool:
```

Sets the delay period required for Lego changes.

**Parameters:**

- `_numBlocks`: The number of blocks to set as the delay period

**Returns:**

- True if the delay was successfully set

**Requirements:**

- Caller must be the governor
- Delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY

### legoChangeDelay

```vyper
@view
@external
def legoChangeDelay() -> uint256:
```

Gets the current lego change delay in blocks.

**Returns:**

- The current delay in blocks

### setLegoChangeDelayToMin

```vyper
@external
def setLegoChangeDelayToMin() -> bool:
```

Sets the lego change delay to the minimum allowed value.

**Returns:**

- True if the delay was successfully set

**Requirements:**

- Caller must be the governor

### numLegosRaw

```vyper
@view
@external
def numLegosRaw() -> uint256:
```

Gets the raw number of legos in the registry.

**Returns:**

- The number of legos registered

### isValidLegoAddr

```vyper
@view
@external
def isValidLegoAddr(_addr: address) -> bool:
```

Checks if an address is a valid registered lego.

**Parameters:**

- `_addr`: The address to check

**Returns:**

- True if the address is a valid lego, False otherwise

### isValidLegoId

```vyper
@view
@external
def isValidLegoId(_legoId: uint256) -> bool:
```

Checks if a lego ID is valid.

**Parameters:**

- `_legoId`: The ID to check

**Returns:**

- True if the lego ID is valid, False otherwise

### getLegoId

```vyper
@view
@external
def getLegoId(_addr: address) -> uint256:
```

Gets the ID of a lego by its address.

**Parameters:**

- `_addr`: The address of the lego

**Returns:**

- The ID of the lego

### getLegoAddr

```vyper
@view
@external
def getLegoAddr(_legoId: uint256) -> address:
```

Gets the address of a lego by its ID.

**Parameters:**

- `_legoId`: The ID of the lego

**Returns:**

- The address of the lego contract

### getLegoInfo

```vyper
@view
@external
def getLegoInfo(_legoId: uint256) -> registry.AddyInfo:
```

Gets all information about a lego by its ID.

**Parameters:**

- `_legoId`: The ID of the lego

**Returns:**

- The lego information structure

### getLegoDescription

```vyper
@view
@external
def getLegoDescription(_legoId: uint256) -> String[64]:
```

Gets the description of a lego by its ID.

**Parameters:**

- `_legoId`: The ID of the lego

**Returns:**

- The description of the lego

### getNumLegos

```vyper
@view
@external
def getNumLegos() -> uint256:
```

Gets the number of active legos in the registry.

**Returns:**

- The number of active legos

### getLastLegoAddr

```vyper
@view
@external
def getLastLegoAddr() -> address:
```

Gets the address of the last lego registered.

**Returns:**

- The address of the last lego

### getLastLegoId

```vyper
@view
@external
def getLastLegoId() -> uint256:
```

Gets the ID of the last lego registered.

**Returns:**

- The ID of the last lego

### getUnderlyingAsset

```vyper
@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
```

Gets the underlying asset for a vault token.

**Parameters:**

- `_vaultToken`: The address of the vault token

**Returns:**

- The underlying asset address, or empty address if not found

### getUnderlyingForUser

```vyper
@view
@external
def getUnderlyingForUser(_user: address, _asset: address) -> uint256:
```

Gets the total underlying amount for a user in a given asset.

**Parameters:**

- `_user`: The address of the user
- `_asset`: The address of the asset

**Returns:**

- The total underlying amount across all vaults

### getVaultTokensForUser

```vyper
@view
@external
def getVaultTokensForUser(_user: address, _asset: address) -> DynArray[VaultTokenInfo, MAX_VAULTS_FOR_USER]:
```

Gets all vault tokens for a user in a given asset.

**Parameters:**

- `_user`: The address of the user
- `_asset`: The address of the asset

**Returns:**

- Array of VaultTokenInfo structs containing legoId and vaultToken address

### getLegoFromVaultToken

```vyper
@view
@external
def getLegoFromVaultToken(_vaultToken: address) -> (uint256, address):
```

Gets the lego ID and address for a given vault token.

**Parameters:**

- `_vaultToken`: The address of the vault token

**Returns:**

- Tuple of (legoId, legoAddress), or (0, empty address) if not found

### isVaultToken

```vyper
@view
@external
def isVaultToken(_vaultToken: address) -> bool:
```

Checks if a given address is a registered vault token.

**Parameters:**

- `_vaultToken`: The address to check

**Returns:**

- True if the address is a vault token, False otherwise

### isValidLegoHelper

```vyper
@view
@external
def isValidLegoHelper(_helperAddr: address) -> bool:
```

Checks if an address can be set as the Lego helper.

**Parameters:**

- `_helperAddr`: The address to validate

**Returns:**

- True if the address can be set as helper, False otherwise

### setLegoHelper

```vyper
@external
def setLegoHelper(_helperAddr: address) -> bool:
```

Sets a new Lego helper address.

**Parameters:**

- `_helperAddr`: The address to set as helper

**Returns:**

- True if the helper was successfully set, False otherwise

**Events Emitted:**

- `LegoHelperSet(helperAddr)`

**Requirements:**

- Caller must be the governor
- Helper address must be a valid contract and different from current helper
