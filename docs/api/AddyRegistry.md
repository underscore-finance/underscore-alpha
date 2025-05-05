# AddyRegistry API Reference

**File:** `contracts/core/registries/AddyRegistry.vy`

The AddyRegistry contract serves as a registry for managing addresses of various components in the system.

## Storage Variables

### isUserWallet

```vyper
isUserWallet: public(HashMap[address, bool])
```

Mapping to track which addresses are user wallets.

### isAgent

```vyper
isAgent: public(HashMap[address, bool])
```

Mapping to track which addresses are agents.

## External Functions

### setIsUserWalletOrAgent

```vyper
@external
def setIsUserWalletOrAgent(_addr: address, _isThing: bool, _setUserWalletMap: bool) -> bool:
```

Sets an address as a user wallet or agent.

**Parameters:**

- `_addr`: The address to set
- `_isThing`: Whether the address is a wallet/agent (true) or not (false)
- `_setUserWalletMap`: If true, sets as wallet; if false, sets as agent

**Returns:**

- True if setting was successful, False otherwise

**Requirements:**

- Caller must be a registered address
- Caller must be the agent factory (address ID 1)
- Address must be a contract

### registerNewAddy

```vyper
@external
def registerNewAddy(_addr: address, _description: String[64]) -> bool:
```

Initiates the registration process for a new address.

**Parameters:**

- `_addr`: The address to register
- `_description`: A short description of the address (max 64 characters)

**Returns:**

- True if the registration was successfully initiated, False if the address is invalid

**Requirements:**

- Caller must be the governance address

### confirmNewAddy

```vyper
@external
def confirmNewAddy(_addr: address) -> uint256:
```

Confirms a pending address registration after the required delay period.

**Parameters:**

- `_addr`: The address to confirm registration for

**Returns:**

- The assigned ID for the registered address, or 0 if confirmation fails

**Requirements:**

- Caller must be the governance address
- Registration must be past the required delay period

### cancelPendingNewAddy

```vyper
@external
def cancelPendingNewAddy(_addr: address) -> bool:
```

Cancels a pending address registration.

**Parameters:**

- `_addr`: The address whose pending registration should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governance address
- A pending registration must exist for the address

### updateAddyAddr

```vyper
@external
def updateAddyAddr(_addyId: uint256, _newAddr: address) -> bool:
```

Initiates an address update for an existing registered address.

**Parameters:**

- `_addyId`: The ID of the address to update
- `_newAddr`: The new address to set

**Returns:**

- True if the update was successfully initiated, False if the update is invalid

**Requirements:**

- Caller must be the governance address

### confirmAddyUpdate

```vyper
@external
def confirmAddyUpdate(_addyId: uint256) -> bool:
```

Confirms a pending address update after the required delay period.

**Parameters:**

- `_addyId`: The ID of the address to confirm update for

**Returns:**

- True if the update was successfully confirmed, False if confirmation fails

**Requirements:**

- Caller must be the governance address
- Update must be past the required delay period

### cancelPendingAddyUpdate

```vyper
@external
def cancelPendingAddyUpdate(_addyId: uint256) -> bool:
```

Cancels a pending address update.

**Parameters:**

- `_addyId`: The ID of the address whose pending update should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governance address
- A pending update must exist for the address ID

### disableAddyAddr

```vyper
@external
def disableAddyAddr(_addyId: uint256) -> bool:
```

Initiates the disable process for an existing registered address.

**Parameters:**

- `_addyId`: The ID of the address to disable

**Returns:**

- True if the disable was successfully initiated, False if the disable is invalid

**Requirements:**

- Caller must be the governance address

### confirmAddyDisable

```vyper
@external
def confirmAddyDisable(_addyId: uint256) -> bool:
```

Confirms a pending address disable after the required delay period.

**Parameters:**

- `_addyId`: The ID of the address to confirm disable for

**Returns:**

- True if the disable was successfully confirmed, False if confirmation fails

**Requirements:**

- Caller must be the governance address
- Disable must be past the required delay period

### cancelPendingAddyDisable

```vyper
@external
def cancelPendingAddyDisable(_addyId: uint256) -> bool:
```

Cancels a pending address disable.

**Parameters:**

- `_addyId`: The ID of the address whose pending disable should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governance address
- A pending disable must exist for the address ID

### setAddyChangeDelay

```vyper
@external
def setAddyChangeDelay(_numBlocks: uint256) -> bool:
```

Sets the delay period required for address changes.

**Parameters:**

- `_numBlocks`: The number of blocks to set as the delay period

**Returns:**

- True if the delay was successfully set

**Requirements:**

- Caller must be the governance address
- Delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY

### setAddyChangeDelayToMin

```vyper
@external
def setAddyChangeDelayToMin() -> bool:
```

Sets the address change delay to the minimum allowed value.

**Returns:**

- True if the delay was successfully set to the minimum

**Requirements:**

- Caller must be the governance address

## Inherited Methods

The AddyRegistry inherits from the Registry module, which provides the following functionality:

### Registry Methods

- `_isValidAddyId(uint256)`: Checks if an address ID is valid
- `_isValidAddyAddr(address)`: Checks if an address is a valid registered address
- `_isValidNewAddy(address)`: Checks if an address can be registered as a new address
- `_isValidAddyUpdate(uint256, address, address)`: Checks if an address update operation would be valid
- `_isValidAddyDisable(uint256, address)`: Checks if an address can be disabled
- `_getAddy(uint256)`: Gets the address for a given ID
- `_getAddyId(address)`: Gets the ID for a given address
- `_getNumAddys()`: Gets the number of active addresses
- `_getLastAddyAddr()`: Gets the most recently registered address
- `_getLastAddyId()`: Gets the most recently registered address ID

### State Variables from Registry

- `addyInfo`: Mapping from address IDs to their corresponding info struct
- `addyToId`: Mapping from addresses to their corresponding IDs
- `numAddys`: Total number of addresses registered
- `addyChangeDelay`: Number of blocks required between initiating and confirming a change
- `MIN_ADDY_CHANGE_DELAY`: Minimum allowed change delay
- `MAX_ADDY_CHANGE_DELAY`: Maximum allowed change delay

## Governance

The AddyRegistry uses a governance model where all critical operations require a two-step process:

1. **Initiation**: The governor initiates a change (registration, update, disable)
2. **Confirmation**: After the required delay period, the governor confirms the change

This delay mechanism provides security against malicious changes and allows time for review.
