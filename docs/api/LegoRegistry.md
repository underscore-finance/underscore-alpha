# LegoRegistry

The LegoRegistry contract maintains a registry of all available "legos" (DeFi protocol integrations) in the system.

**Source:** `contracts/core/LegoRegistry.vy`

## Flags

### LegoType

```vyper
flag LegoType:
    YIELD_OPP
    DEX
```

Flag defining the types of legos that can be registered.

## Structs

### LegoInfo

```vyper
struct LegoInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
    legoType: LegoType
```

Structure containing information about a registered lego.

## Events

### NewLegoRegistered

```vyper
event NewLegoRegistered:
    addr: indexed(address)
    legoId: uint256
    description: String[64]
    legoType: LegoType
```

Emitted when a new lego is registered in the system.

### LegoAddrUpdated

```vyper
event LegoAddrUpdated:
    newAddr: indexed(address)
    prevAddr: indexed(address)
    legoId: uint256
    version: uint256
    description: String[64]
    legoType: LegoType
```

Emitted when a lego's address is updated.

### LegoAddrDisabled

```vyper
event LegoAddrDisabled:
    prevAddr: indexed(address)
    legoId: uint256
    version: uint256
    description: String[64]
    legoType: LegoType
```

Emitted when a lego is disabled.

### LegoHelperSet

```vyper
event LegoHelperSet:
    helperAddr: indexed(address)
```

Emitted when the lego helper address is set.

## Storage Variables

### legoHelper

```vyper
legoHelper: public(address)
```

Address of the lego helper contract.

### legoInfo

```vyper
legoInfo: public(HashMap[uint256, LegoInfo])
```

Mapping from lego ID to lego information.

### legoAddrToId

```vyper
legoAddrToId: public(HashMap[address, uint256])
```

Mapping from lego address to lego ID.

### numLegos

```vyper
numLegos: public(uint256)
```

Total number of registered legos.

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

Address of the address registry.

## Constants

### MAX_VAULTS

```vyper
MAX_VAULTS: constant(uint256) = 15
```

Maximum number of vaults that can be associated with a lego.

## External Functions

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
def registerNewLego(_addr: address, _description: String[64], _legoType: LegoType) -> uint256:
```

Registers a new lego in the registry.

**Parameters:**
- `_addr`: The address of the lego contract
- `_description`: A brief description of the lego's functionality
- `_legoType`: The type of the lego

**Returns:**
- The ID of the newly registered lego

**Events Emitted:**
- `NewLegoRegistered(addr, legoId, description, legoType)`

**Requirements:**
- Caller must be the governor
- Lego address must be a valid contract
- Lego must not be already registered

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

Updates the address of an existing lego.

**Parameters:**
- `_legoId`: The ID of the lego to update
- `_newAddr`: The new address for the lego

**Returns:**
- True if the update was successful, False otherwise

**Events Emitted:**
- `LegoAddrUpdated(newAddr, prevAddr, legoId, version, description, legoType)`

**Requirements:**
- Caller must be the governor
- Lego ID must be valid
- New lego address must be a valid contract

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

### disableLego

```vyper
@external
def disableLego(_legoId: uint256) -> bool:
```

Disables a lego by setting its address to empty.

**Parameters:**
- `_legoId`: The ID of the lego to disable

**Returns:**
- True if the lego was successfully disabled, False otherwise

**Events Emitted:**
- `LegoAddrDisabled(prevAddr, legoId, version, description, legoType)`

**Requirements:**
- Caller must be the governor
- Lego ID must be valid
- Lego must not already be disabled

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

**Requirements:**
- Lego ID must be valid

### getLegoIdFromAddr

```vyper
@view
@external
def getLegoIdFromAddr(_addr: address) -> uint256:
```

Gets the ID of a lego by its address.

**Parameters:**
- `_addr`: The address of the lego

**Returns:**
- The ID of the lego

### getLegoType

```vyper
@view
@external
def getLegoType(_legoId: uint256) -> LegoType:
```

Gets the type of a lego by its ID.

**Parameters:**
- `_legoId`: The ID of the lego

**Returns:**
- The type of the lego

**Requirements:**
- Lego ID must be valid

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

**Requirements:**
- Lego ID must be valid

### getLegoVersion

```vyper
@view
@external
def getLegoVersion(_legoId: uint256) -> uint256:
```

Gets the version of a lego by its ID.

**Parameters:**
- `_legoId`: The ID of the lego

**Returns:**
- The version of the lego

**Requirements:**
- Lego ID must be valid

### getLegoLastModified

```vyper
@view
@external
def getLegoLastModified(_legoId: uint256) -> uint256:
```

Gets the last modified timestamp of a lego by its ID.

**Parameters:**
- `_legoId`: The ID of the lego

**Returns:**
- The last modified timestamp of the lego

**Requirements:**
- Lego ID must be valid

### setLegoHelper

```vyper
@external
def setLegoHelper(_helperAddr: address) -> bool:
```

Sets the lego helper address.

**Parameters:**
- `_helperAddr`: The address of the lego helper contract

**Returns:**
- True if the helper was successfully set

**Events Emitted:**
- `LegoHelperSet(helperAddr)`

**Requirements:**
- Caller must be the governor
- Helper address must be a valid contract

### getYieldVaults

```vyper
@view
@external
def getYieldVaults(_legoId: uint256) -> DynArray[address, MAX_VAULTS]:
```

Gets the yield vaults associated with a lego.

**Parameters:**
- `_legoId`: The ID of the lego

**Returns:**
- Array of vault addresses

**Requirements:**
- Lego ID must be valid
- Lego must be of type YIELD_OPP

### getYieldVaultTokens

```vyper
@view
@external
def getYieldVaultTokens(_legoId: uint256) -> DynArray[address, MAX_VAULTS]:
```

Gets the vault tokens associated with a lego.

**Parameters:**
- `_legoId`: The ID of the lego

**Returns:**
- Array of vault token addresses

**Requirements:**
- Lego ID must be valid
- Lego must be of type YIELD_OPP 