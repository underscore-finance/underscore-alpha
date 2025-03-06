# AddyRegistry API Reference

**File:** `contracts/core/AddyRegistry.vy`

The AddyRegistry contract serves as a registry for managing addresses of various components in the system.

## Data Structures

### AddyInfo

```vyper
struct AddyInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
```

A struct containing information about a registered address:
- `addr`: The actual address of the contract
- `version`: The version number, incremented on updates
- `lastModified`: Timestamp of the last modification
- `description`: A brief description of the contract's functionality

## Events

### NewAddyRegistered

```vyper
event NewAddyRegistered:
    addr: indexed(address)
    addyId: uint256
    description: String[64]
```

Emitted when a new address is registered in the registry.

### AddyIdUpdated

```vyper
event AddyIdUpdated:
    newAddr: indexed(address)
    prevAddy: indexed(address)
    addyId: uint256
    version: uint256
    description: String[64]
```

Emitted when an existing address is updated in the registry.

### AddyIdDisabled

```vyper
event AddyIdDisabled:
    prevAddy: indexed(address)
    addyId: uint256
    version: uint256
    description: String[64]
```

Emitted when an address is disabled in the registry.

### AddyRegistryGovernorSet

```vyper
event AddyRegistryGovernorSet:
    governor: indexed(address)
```

Emitted when the governor of the registry is changed.

## State Variables

### addyInfo

```vyper
addyInfo: public(HashMap[uint256, AddyInfo])
```

Mapping from address IDs to their corresponding AddyInfo struct, which contains the address, version, last modified timestamp, and description.

### addyToId

```vyper
addyToId: public(HashMap[address, uint256])
```

Mapping from addresses to their corresponding IDs in the registry.

### numAddys

```vyper
numAddys: public(uint256)
```

The total number of addresses registered in the system. Starts at 1 since indexing begins at 1.

### governor

```vyper
governor: public(address)
```

The address of the contract governor, which has permission to register, update, and disable addresses.

## External Functions

### registerNewAddy

```vyper
@external
def registerNewAddy(_addy: address, _description: String[64]) -> uint256:
```

Registers a new address in the registry.

**Parameters:**
- `_addy`: The address to register
- `_description`: A brief description of the contract's functionality

**Returns:**
- The assigned ID if registration successful, 0 if failed

**Events Emitted:**
- `NewAddyRegistered(addr, addyId, description)`

**Requirements:**
- Caller must be the governor
- Address must be non-zero, a contract, and not already registered

### updateAddy

```vyper
@external
def updateAddy(_addyId: uint256, _newAddy: address) -> bool:
```

Updates an existing address in the registry.

**Parameters:**
- `_addyId`: The ID of the contract to update
- `_newAddy`: The new address for the contract

**Returns:**
- True if update successful, False otherwise

**Events Emitted:**
- `AddyIdUpdated(newAddr, prevAddy, addyId, version, description)`

**Requirements:**
- Caller must be the governor
- ID must be valid
- New address must be valid and different from current address

### disableAddy

```vyper
@external
def disableAddy(_addyId: uint256) -> bool:
```

Disables a core contract by setting its address to empty.

**Parameters:**
- `_addyId`: The ID of the contract to disable

**Returns:**
- True if disable successful, False otherwise

**Events Emitted:**
- `AddyIdDisabled(prevAddy, addyId, version, description)`

**Requirements:**
- Caller must be the governor
- ID must be valid
- Current address must not be empty

### isValidNewAddy

```vyper
@view
@external
def isValidNewAddy(_addy: address) -> bool:
```

Checks if an address can be registered as a new core contract.

**Parameters:**
- `_addy`: The address to validate

**Returns:**
- True if address can be registered as new core contract, False otherwise

### isValidAddyUpdate

```vyper
@view
@external
def isValidAddyUpdate(_addyId: uint256, _newAddy: address) -> bool:
```

Checks if a core contract update operation would be valid.

**Parameters:**
- `_addyId`: The ID of the contract to update
- `_newAddy`: The proposed new address for the contract

**Returns:**
- True if update would be valid, False otherwise

### isValidAddyDisable

```vyper
@view
@external
def isValidAddyDisable(_addyId: uint256) -> bool:
```

Checks if a core contract can be disabled.

**Parameters:**
- `_addyId`: The ID of the contract to check

**Returns:**
- True if contract can be disabled, False otherwise

### isValidAddy

```vyper
@view
@external
def isValidAddy(_addy: address) -> bool:
```

Checks if an address is a registered core contract.

**Parameters:**
- `_addy`: The address to check

**Returns:**
- True if address is a registered core contract, False otherwise

### isValidAddyId

```vyper
@view
@external
def isValidAddyId(_addyId: uint256) -> bool:
```

Checks if a core contract ID is valid.

**Parameters:**
- `_addyId`: The ID to check

**Returns:**
- True if ID is valid, False otherwise

### getAddyId

```vyper
@view
@external
def getAddyId(_addy: address) -> uint256:
```

Gets the ID of a core contract from its address.

**Parameters:**
- `_addy`: The address to query

**Returns:**
- The ID associated with the address, 0 if address is not registered

### getAddy

```vyper
@view
@external
def getAddy(_addyId: uint256) -> address:
```

Gets the address of a core contract from its ID.

**Parameters:**
- `_addyId`: The ID to query

**Returns:**
- The address associated with the ID, empty address if ID is invalid or contract is disabled

### getAddyInfo

```vyper
@view
@external
def getAddyInfo(_addyId: uint256) -> AddyInfo:
```

Gets all information about a core contract.

**Parameters:**
- `_addyId`: The ID to query

**Returns:**
- AddyInfo struct containing all contract information (address, version, timestamp, description)

### getAddyDescription

```vyper
@view
@external
def getAddyDescription(_addyId: uint256) -> String[64]:
```

Gets the description of a core contract.

**Parameters:**
- `_addyId`: The ID to query

**Returns:**
- The description associated with the ID, empty string if ID is invalid

### getNumAddys

```vyper
@view
@external
def getNumAddys() -> uint256:
```

Gets the total number of registered core contracts.

**Returns:**
- The total number of registered core contracts (number of contracts minus 1 since indexing starts at 1)

### getLastAddy

```vyper
@view
@external
def getLastAddy() -> address:
```

Gets the address of the most recently registered core contract.

**Returns:**
- The address of the last registered contract

### getLastAddyId

```vyper
@view
@external
def getLastAddyId() -> uint256:
```

Gets the ID of the most recently registered core contract.

**Returns:**
- The ID of the last registered contract

### isValidGovernor

```vyper
@view
@external 
def isValidGovernor(_newGovernor: address) -> bool:
```

Checks if an address can be set as the new governor.

**Parameters:**
- `_newGovernor`: The address to validate

**Returns:**
- True if address can be set as governor, False otherwise

### setGovernor

```vyper
@external
def setGovernor(_newGovernor: address) -> bool:
```

Sets a new governor address.

**Parameters:**
- `_newGovernor`: The address to set as governor

**Returns:**
- True if governor was set successfully, False otherwise

**Events Emitted:**
- `AddyRegistryGovernorSet(governor)`

**Requirements:**
- Caller must be the current governor
- New governor must be a contract, non-empty, and different from current governor 