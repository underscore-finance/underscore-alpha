# LegoHelper

The LegoHelper contract provides utility functions for working with legos in the Underscore system.

**Source:** `contracts/core/LegoHelper.vy`

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

### LegoInfo

```vyper
struct LegoInfo:
    legoId: uint256
    legoType: LegoType
    legoAddr: address
```

Structure containing information about a lego.

## Events

### LegoHelperInitialized

```vyper
event LegoHelperInitialized:
    legoRegistry: indexed(address)
```

Emitted when the LegoHelper is initialized.

## Storage Variables

### legoRegistry

```vyper
legoRegistry: public(address)
```

The address of the lego registry.

### isInitialized

```vyper
isInitialized: public(bool)
```

Whether the contract has been initialized.

## External Functions

### initialize

```vyper
@external
def initialize(_legoRegistry: address) -> bool:
```

Initializes the LegoHelper with the lego registry address.

**Parameters:**

- `_legoRegistry`: The address of the lego registry

**Returns:**

- True if initialization was successful

**Requirements:**

- Contract must not already be initialized
- Lego registry address must not be empty

### getVaultTokensGroupedByAsset

```vyper
@view
@external
def getVaultTokensGroupedByAsset(_user: address, _underlyingAssets: DynArray[address, MAX_ASSETS]) -> HashMap[address, DynArray[VaultTokenInfo, MAX_VAULT_TOKENS]]:
```

Gets all vault tokens for a user, grouped by underlying asset.

**Parameters:**

- `_user`: The address of the user
- `_underlyingAssets`: Array of underlying asset addresses to get vault tokens for

**Returns:**

- Mapping from underlying asset address to array of vault token information

### getVaultTokensForAsset

```vyper
@view
@external
def getVaultTokensForAsset(_user: address, _asset: address) -> DynArray[VaultTokenInfo, MAX_VAULT_TOKENS]:
```

Gets all vault tokens for a user for a specific asset.

**Parameters:**

- `_user`: The address of the user
- `_asset`: The address of the underlying asset

**Returns:**

- Array of vault token information for the specified asset

### getLegoByType

```vyper
@view
@external
def getLegoByType(_legoType: LegoType) -> DynArray[LegoInfo, MAX_LEGOS]:
```

Gets all legos of a specific type.

**Parameters:**

- `_legoType`: The type of legos to get (YIELD_OPP or DEX)

**Returns:**

- Array of lego information for the specified type

### getAllLegos

```vyper
@view
@external
def getAllLegos() -> DynArray[LegoInfo, MAX_LEGOS]:
```

Gets all registered legos.

**Parameters:**

- None

**Returns:**

- Array of information for all registered legos

### getUserPositions

```vyper
@view
@external
def getUserPositions(_user: address) -> HashMap[address, uint256]:
```

Gets the user's positions in terms of total underlying value for each asset.

**Parameters:**

- `_user`: The address of the user

**Returns:**

- Mapping from asset address to underlying value

### getUserTotalUsdValue

```vyper
@view
@external
def getUserTotalUsdValue(_user: address, _oracleRegistry: address) -> uint256:
```

Gets the total USD value of all user positions.

**Parameters:**

- `_user`: The address of the user
- `_oracleRegistry`: The address of the oracle registry

**Returns:**

- Total USD value of all user positions

### getUserAssetPositions

```vyper
@view
@external
def getUserAssetPositions(_user: address, _assets: DynArray[address, MAX_ASSETS]) -> HashMap[address, uint256]:
```

Gets the user's positions for specific assets.

**Parameters:**

- `_user`: The address of the user
- `_assets`: Array of asset addresses to get positions for

**Returns:**

- Mapping from asset address to underlying value
