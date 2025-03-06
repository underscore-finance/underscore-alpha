# OracleRegistry

The OracleRegistry contract manages the registration and access to price oracles.

**Source:** `contracts/core/OracleRegistry.vy`

## Structs

### OraclePartnerInfo

```vyper
struct OraclePartnerInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
```

Structure containing information about a registered oracle partner.

## Events

### NewOraclePartnerRegistered

```vyper
event NewOraclePartnerRegistered:
    addr: indexed(address)
    oraclePartnerId: uint256
    description: String[64]
```

Emitted when a new oracle partner is registered in the system.

### OraclePartnerAddrUpdated

```vyper
event OraclePartnerAddrUpdated:
    newAddr: indexed(address)
    prevAddr: indexed(address)
    oraclePartnerId: uint256
    version: uint256
    description: String[64]
```

Emitted when an oracle partner's address is updated.

### OraclePartnerAddrDisabled

```vyper
event OraclePartnerAddrDisabled:
    prevAddr: indexed(address)
    oraclePartnerId: uint256
    version: uint256
    description: String[64]
```

Emitted when an oracle partner is disabled.

### PriorityOraclePartnerIdsModified

```vyper
event PriorityOraclePartnerIdsModified:
    numIds: uint256
```

Emitted when the priority oracle partner IDs are modified.

### StaleTimeSet

```vyper
event StaleTimeSet:
    staleTime: uint256
```

Emitted when the stale time is set.

## Storage Variables

### oraclePartnerInfo

```vyper
oraclePartnerInfo: public(HashMap[uint256, OraclePartnerInfo])
```

Mapping from oracle partner ID to oracle partner information.

### oraclePartnerAddrToId

```vyper
oraclePartnerAddrToId: public(HashMap[address, uint256])
```

Mapping from oracle partner address to oracle partner ID.

### numOraclePartners

```vyper
numOraclePartners: public(uint256)
```

Total number of registered oracle partners.

### priorityOraclePartnerIds

```vyper
priorityOraclePartnerIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
```

List of oracle partner IDs in priority order.

### staleTime

```vyper
staleTime: public(uint256)
```

Time after which a price is considered stale.

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

Address of the address registry.

### ETH

```vyper
ETH: public(immutable(address))
```

Address of the ETH token.

### MIN_STALE_TIME

```vyper
MIN_STALE_TIME: public(immutable(uint256))
```

Minimum allowed stale time.

### MAX_STALE_TIME

```vyper
MAX_STALE_TIME: public(immutable(uint256))
```

Maximum allowed stale time.

## Constants

### MAX_PRIORITY_PARTNERS

```vyper
MAX_PRIORITY_PARTNERS: constant(uint256) = 10
```

Maximum number of priority oracle partners.

## External Functions

### registerOracle

```vyper
@external
def registerOracle(_oracleAddr: address) -> uint256:
```

Registers a new oracle in the registry.

**Parameters:**
- `_oracleAddr`: The address of the oracle contract

**Returns:**
- The ID of the newly registered oracle

**Events Emitted:**
- `OracleRegistered(oracleId, oracleAddr)`

**Requirements:**
- Caller must be the governor
- Oracle address must be a valid contract
- Oracle must not be already registered

### updateOracle

```vyper
@external
def updateOracle(_oracleId: uint256, _newOracleAddr: address) -> bool:
```

Updates an existing oracle with a new address.

**Parameters:**
- `_oracleId`: The ID of the oracle to update
- `_newOracleAddr`: The new address of the oracle contract

**Returns:**
- True if oracle was successfully updated

**Events Emitted:**
- `OracleUpdated(oracleId, oldOracleAddr, newOracleAddr)`

**Requirements:**
- Caller must be the governor
- Oracle ID must be valid
- New oracle address must be a valid contract

### getPrice

```vyper
@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
```

Gets the USD price of an asset from registered oracle partners.

**Parameters:**
- `_asset`: The address of the asset to get price for
- `_shouldRaise`: If True, raises an error when price feed exists but returns no price

**Returns:**
- The asset price in USD with 18 decimals

### getUsdValue

```vyper
@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256:
```

Gets the USD value of a given amount of an asset.

**Parameters:**
- `_asset`: The address of the asset
- `_amount`: The amount of the asset
- `_shouldRaise`: Whether to raise an error if the price is not available

**Returns:**
- The USD value of the asset amount

**Requirements:**
- If `_shouldRaise` is True, a valid price must be available

### getEthUsdValue

```vyper
@view
@external
def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256:
```

Gets the USD value of a given amount of ETH.

**Parameters:**
- `_amount`: The amount of ETH
- `_shouldRaise`: Whether to raise an error if the price is not available

**Returns:**
- The USD value of the ETH amount

**Requirements:**
- If `_shouldRaise` is True, a valid price must be available

### isValidNewOraclePartnerAddr

```vyper
@view
@external
def isValidNewOraclePartnerAddr(_addr: address) -> bool:
```

Checks if an address can be registered as a new oracle partner.

**Parameters:**
- `_addr`: The address to validate

**Returns:**
- True if the address can be registered as a new oracle partner, False otherwise

### registerNewOraclePartner

```vyper
@external
def registerNewOraclePartner(_addr: address, _description: String[64]) -> uint256:
```

Registers a new oracle partner in the registry.

**Parameters:**
- `_addr`: The address of the oracle partner contract
- `_description`: A brief description of the oracle partner's functionality

**Returns:**
- The ID of the newly registered oracle partner

**Events Emitted:**
- `NewOraclePartnerRegistered(addr, oraclePartnerId, description)`

**Requirements:**
- Caller must be the governor
- Oracle partner address must be a valid contract
- Oracle partner must not be already registered

### isValidOraclePartnerUpdate

```vyper
@view
@external
def isValidOraclePartnerUpdate(_oraclePartnerId: uint256, _newAddr: address) -> bool:
```

Checks if an oracle partner update operation would be valid.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner to update
- `_newAddr`: The proposed new address for the oracle partner

**Returns:**
- True if the update would be valid, False otherwise

### updateOraclePartnerAddr

```vyper
@external
def updateOraclePartnerAddr(_oraclePartnerId: uint256, _newAddr: address) -> bool:
```

Updates the address of an existing oracle partner.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner to update
- `_newAddr`: The new address for the oracle partner

**Returns:**
- True if the update was successful, False otherwise

**Events Emitted:**
- `OraclePartnerAddrUpdated(newAddr, prevAddr, oraclePartnerId, version, description)`

**Requirements:**
- Caller must be the governor
- Oracle partner ID must be valid
- New oracle partner address must be a valid contract

### isValidOraclePartnerDisable

```vyper
@view
@external
def isValidOraclePartnerDisable(_oraclePartnerId: uint256) -> bool:
```

Checks if an oracle partner can be disabled.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner to check

**Returns:**
- True if the oracle partner can be disabled, False otherwise

### disableOraclePartner

```vyper
@external
def disableOraclePartner(_oraclePartnerId: uint256) -> bool:
```

Disables an oracle partner by setting its address to empty.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner to disable

**Returns:**
- True if the oracle partner was successfully disabled, False otherwise

**Events Emitted:**
- `OraclePartnerAddrDisabled(prevAddr, oraclePartnerId, version, description)`

**Requirements:**
- Caller must be the governor
- Oracle partner ID must be valid
- Oracle partner must not already be disabled

### isValidOraclePartnerId

```vyper
@view
@external
def isValidOraclePartnerId(_oraclePartnerId: uint256) -> bool:
```

Checks if an oracle partner ID is valid.

**Parameters:**
- `_oraclePartnerId`: The ID to check

**Returns:**
- True if the oracle partner ID is valid, False otherwise

### getOraclePartnerAddr

```vyper
@view
@external
def getOraclePartnerAddr(_oraclePartnerId: uint256) -> address:
```

Gets the address of an oracle partner by its ID.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner

**Returns:**
- The address of the oracle partner contract

**Requirements:**
- Oracle partner ID must be valid

### getOraclePartnerIdFromAddr

```vyper
@view
@external
def getOraclePartnerIdFromAddr(_addr: address) -> uint256:
```

Gets the ID of an oracle partner by its address.

**Parameters:**
- `_addr`: The address of the oracle partner

**Returns:**
- The ID of the oracle partner

### getOraclePartnerDescription

```vyper
@view
@external
def getOraclePartnerDescription(_oraclePartnerId: uint256) -> String[64]:
```

Gets the description of an oracle partner by its ID.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner

**Returns:**
- The description of the oracle partner

**Requirements:**
- Oracle partner ID must be valid

### getOraclePartnerVersion

```vyper
@view
@external
def getOraclePartnerVersion(_oraclePartnerId: uint256) -> uint256:
```

Gets the version of an oracle partner by its ID.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner

**Returns:**
- The version of the oracle partner

**Requirements:**
- Oracle partner ID must be valid

### getOraclePartnerLastModified

```vyper
@view
@external
def getOraclePartnerLastModified(_oraclePartnerId: uint256) -> uint256:
```

Gets the last modified timestamp of an oracle partner by its ID.

**Parameters:**
- `_oraclePartnerId`: The ID of the oracle partner

**Returns:**
- The last modified timestamp of the oracle partner

**Requirements:**
- Oracle partner ID must be valid

### setPriorityOraclePartnerIds

```vyper
@external
def setPriorityOraclePartnerIds(_priorityOraclePartnerIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
```

Sets the priority oracle partner IDs.

**Parameters:**
- `_priorityOraclePartnerIds`: Array of oracle partner IDs in priority order

**Returns:**
- True if the priority IDs were successfully set

**Events Emitted:**
- `PriorityOraclePartnerIdsModified(numIds)`

**Requirements:**
- Caller must be the governor
- All IDs must be valid oracle partner IDs

### setStaleTime

```vyper
@external
def setStaleTime(_staleTime: uint256) -> bool:
```

Sets the stale time for price feeds.

**Parameters:**
- `_staleTime`: The new stale time in seconds

**Returns:**
- True if the stale time was successfully set

**Events Emitted:**
- `StaleTimeSet(staleTime)`

**Requirements:**
- Caller must be the governor
- Stale time must be within allowed range 