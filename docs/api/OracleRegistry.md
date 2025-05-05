# OracleRegistry API Reference

**File:** `contracts/core/registries/OracleRegistry.vy`

The OracleRegistry contract maintains a registry of price oracles and provides functions to access price data.

## Events

### PriorityOraclePartnerIdsModified

```vyper
event PriorityOraclePartnerIdsModified:
    numIds: uint256
```

Emitted when the list of priority oracle partner IDs is modified.

### StaleTimeSet

```vyper
event StaleTimeSet:
    staleTime: uint256
```

Emitted when the stale time configuration is updated.

## Storage Variables

### priorityOraclePartnerIds

```vyper
priorityOraclePartnerIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
```

An array of oracle partner IDs in priority order, which are checked first when requesting prices.

### staleTime

```vyper
staleTime: public(uint256)
```

The maximum staleness time allowed for price data in seconds.

### ETH

```vyper
ETH: public(immutable(address))
```

The address representing ETH in the system.

### MIN_STALE_TIME

```vyper
MIN_STALE_TIME: public(immutable(uint256))
```

The minimum staleness time that can be configured.

### MAX_STALE_TIME

```vyper
MAX_STALE_TIME: public(immutable(uint256))
```

The maximum staleness time that can be configured.

## Constants

### MAX_PRIORITY_PARTNERS

```vyper
MAX_PRIORITY_PARTNERS: constant(uint256) = 10
```

The maximum number of oracle partners that can be set as priority partners.

## External Functions

### getPrice

```vyper
@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
```

Gets the USD price of an asset from registered oracle partners.

**Parameters:**

- `_asset`: The address of the asset to get the price for
- `_shouldRaise`: If True, raises an error when a price feed exists but returns no price

**Returns:**

- The asset price in USD with 18 decimals

### getUsdValue

```vyper
@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256:
```

Calculates the USD value of a given amount of an asset.

**Parameters:**

- `_asset`: The address of the asset
- `_amount`: The amount of the asset
- `_shouldRaise`: If True, raises an error when a price feed exists but returns no price

**Returns:**

- The USD value with 18 decimals

### getAssetAmount

```vyper
@view
@external
def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256:
```

Calculates the amount of an asset worth a given USD value.

**Parameters:**

- `_asset`: The address of the asset
- `_usdValue`: The USD value to convert to asset amount (18 decimals)
- `_shouldRaise`: If True, raises an error when a price feed exists but returns no price

**Returns:**

- The amount of the asset

### hasPriceFeed

```vyper
@view
@external
def hasPriceFeed(_asset: address) -> bool:
```

Checks if any oracle partner has a price feed for the asset.

**Parameters:**

- `_asset`: The address of the asset to check

**Returns:**

- True if a price feed exists, False otherwise

### getEthUsdValue

```vyper
@view
@external
def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256:
```

Calculates the USD value of a given amount of ETH.

**Parameters:**

- `_amount`: The amount of ETH in wei
- `_shouldRaise`: If True, raises an error when a price feed exists but returns no price

**Returns:**

- The USD value with 18 decimals

### getEthAmount

```vyper
@view
@external
def getEthAmount(_usdValue: uint256, _shouldRaise: bool = False) -> uint256:
```

Calculates the amount of ETH worth a given USD value.

**Parameters:**

- `_usdValue`: The USD value to convert to ETH amount (18 decimals)
- `_shouldRaise`: If True, raises an error when a price feed exists but returns no price

**Returns:**

- The amount of ETH in wei

### isValidNewOraclePartnerAddr

```vyper
@view
@external
def isValidNewOraclePartnerAddr(_addr: address) -> bool:
```

Checks if an address can be registered as a new Oracle Partner.

**Parameters:**

- `_addr`: The address to validate

**Returns:**

- True if the address can be registered, False otherwise

### registerNewOraclePartner

```vyper
@external
def registerNewOraclePartner(_addr: address, _description: String[64]) -> bool:
```

Initiates the registration process for a new Oracle Partner.

**Parameters:**

- `_addr`: The address of the Oracle Partner to register
- `_description`: A short description of the Oracle Partner (max 64 characters)

**Returns:**

- True if the registration was successfully initiated, False if the Oracle Partner is invalid

**Requirements:**

- Caller must be the governor

### confirmNewOraclePartnerRegistration

```vyper
@external
def confirmNewOraclePartnerRegistration(_addr: address) -> uint256:
```

Confirms a pending Oracle Partner registration after the required delay period.

**Parameters:**

- `_addr`: The address of the Oracle Partner to confirm registration for

**Returns:**

- The assigned ID for the registered Oracle Partner, or 0 if confirmation fails

**Requirements:**

- Caller must be the governor
- Registration must be past the required delay period

### cancelPendingNewOraclePartner

```vyper
@external
def cancelPendingNewOraclePartner(_addr: address) -> bool:
```

Cancels a pending Oracle Partner registration.

**Parameters:**

- `_addr`: The address of the Oracle Partner whose pending registration should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governor
- A pending registration must exist for the address

### isValidOraclePartnerUpdate

```vyper
@view
@external
def isValidOraclePartnerUpdate(_oracleId: uint256, _newAddr: address) -> bool:
```

Checks if an Oracle Partner update operation would be valid.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner to update
- `_newAddr`: The proposed new address for the Oracle Partner

**Returns:**

- True if the update would be valid, False otherwise

### updateOraclePartnerAddr

```vyper
@external
def updateOraclePartnerAddr(_oracleId: uint256, _newAddr: address) -> bool:
```

Initiates an address update for an existing registered Oracle Partner.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner to update
- `_newAddr`: The new address to set for the Oracle Partner

**Returns:**

- True if the update was successfully initiated, False if the update is invalid

**Requirements:**

- Caller must be the governor

### confirmOraclePartnerUpdate

```vyper
@external
def confirmOraclePartnerUpdate(_oracleId: uint256) -> bool:
```

Confirms a pending Oracle Partner address update after the required delay period.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner to confirm update for

**Returns:**

- True if the update was successfully confirmed, False if confirmation fails

**Requirements:**

- Caller must be the governor
- Update must be past the required delay period

### cancelPendingOraclePartnerUpdate

```vyper
@external
def cancelPendingOraclePartnerUpdate(_oracleId: uint256) -> bool:
```

Cancels a pending Oracle Partner address update.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner whose pending update should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governor
- A pending update must exist for the Oracle Partner ID

### isValidOraclePartnerDisable

```vyper
@view
@external
def isValidOraclePartnerDisable(_oracleId: uint256) -> bool:
```

Checks if an Oracle Partner can be disabled.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner to check

**Returns:**

- True if the Oracle Partner can be disabled, False otherwise

### disableOraclePartnerAddr

```vyper
@external
def disableOraclePartnerAddr(_oracleId: uint256) -> bool:
```

Initiates the disable process for an existing registered Oracle Partner.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner to disable

**Returns:**

- True if the disable was successfully initiated, False if the disable is invalid

**Requirements:**

- Caller must be the governor

### confirmOraclePartnerDisable

```vyper
@external
def confirmOraclePartnerDisable(_oracleId: uint256) -> bool:
```

Confirms a pending Oracle Partner disable after the required delay period.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner to confirm disable for

**Returns:**

- True if the disable was successfully confirmed, False if confirmation fails

**Requirements:**

- Caller must be the governor
- Disable must be past the required delay period

### cancelPendingOraclePartnerDisable

```vyper
@external
def cancelPendingOraclePartnerDisable(_oracleId: uint256) -> bool:
```

Cancels a pending Oracle Partner disable.

**Parameters:**

- `_oracleId`: The ID of the Oracle Partner whose pending disable should be cancelled

**Returns:**

- True if the cancellation was successful

**Requirements:**

- Caller must be the governor
- A pending disable must exist for the Oracle Partner ID

### setOraclePartnerChangeDelay

```vyper
@external
def setOraclePartnerChangeDelay(_numBlocks: uint256) -> bool:
```

Sets the delay period required for Oracle Partner changes.

**Parameters:**

- `_numBlocks`: The number of blocks to set as the delay period

**Returns:**

- True if the delay was successfully set

**Requirements:**

- Caller must be the governor
- Delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY

### oracleChangeDelay

```vyper
@view
@external
def oracleChangeDelay() -> uint256:
```

Gets the current oracle change delay in blocks.

**Returns:**

- The current delay in blocks

### setOraclePartnerChangeDelayToMin

```vyper
@external
def setOraclePartnerChangeDelayToMin() -> bool:
```

Sets the oracle change delay to the minimum allowed value.

**Returns:**

- True if the delay was successfully set

**Requirements:**

- Caller must be the governor

### getPriorityOraclePartnerIds

```vyper
@view
@external
def getPriorityOraclePartnerIds() -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
```

Gets the list of priority oracle partner IDs.

**Returns:**

- Array of oracle partner IDs in priority order

### areValidPriorityOraclePartnerIds

```vyper
@view
@external
def areValidPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
```

Checks if a list of priority oracle partner IDs is valid.

**Parameters:**

- `_priorityIds`: Array of oracle partner IDs to validate

**Returns:**

- True if all IDs are valid, False otherwise

### setPriorityOraclePartnerIds

```vyper
@external
def setPriorityOraclePartnerIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
```

Sets the list of priority oracle partner IDs.

**Parameters:**

- `_priorityIds`: Array of oracle partner IDs in desired priority order

**Returns:**

- True if the priority list was set successfully, False otherwise

**Events Emitted:**

- `PriorityOraclePartnerIdsModified(numIds)`

**Requirements:**

- Caller must be the governor

### isValidStaleTime

```vyper
@view
@external
def isValidStaleTime(_staleTime: uint256) -> bool:
```

Checks if a stale time value is valid.

**Parameters:**

- `_staleTime`: The stale time in seconds to validate

**Returns:**

- True if the stale time is valid, False otherwise

### setStaleTime

```vyper
@external
def setStaleTime(_staleTime: uint256) -> bool:
```

Sets the maximum staleness time for price data.

**Parameters:**

- `_staleTime`: The stale time in seconds to set

**Returns:**

- True if the stale time was set successfully, False otherwise

**Events Emitted:**

- `StaleTimeSet(staleTime)`

**Requirements:**

- Caller must be the governor
- Stale time must be between MIN_STALE_TIME and MAX_STALE_TIME

## Inherited Methods

The OracleRegistry inherits from the Registry module, which provides functionality for managing registered addresses, similar to the AddyRegistry. It also uses the same two-step governance model for critical operations.

## Governance

Like other registries in the system, the OracleRegistry implements a two-step governance process:

1. **Initiation**: The governor initiates a change (registration, update, disable)
2. **Confirmation**: After the required delay period, the governor confirms the change

This delay mechanism provides security against malicious changes and allows time for review
