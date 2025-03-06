# LegoHelper API Reference

**File:** `contracts/core/LegoHelper.vy`

The LegoHelper contract provides helper functions for lego operations, including yield and DEX functionality.

## Flags

### LegoType

```vyper
flag LegoType:
    YIELD_OPP
    DEX
```

Flag defining the types of legos.

## Structs

### SwapRoute

```vyper
struct SwapRoute:
    legoId: uint256
    pool: address
    tokenIn: address
    tokenOut: address
    amountIn: uint256
    amountOut: uint256
```

Structure for swap route information.

### SwapInstruction

```vyper
struct SwapInstruction:
    legoId: uint256
    amountIn: uint256
    minAmountOut: uint256
    tokenPath: DynArray[address, MAX_TOKEN_PATH]
    poolPath: DynArray[address, MAX_TOKEN_PATH - 1]
```

Structure for swap instructions.

### UnderlyingData

```vyper
struct UnderlyingData:
    asset: address
    amount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    legoDesc: String[64]
```

Structure for underlying asset data.

### LegoInfo

```vyper
struct LegoInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
    legoType: LegoType
```

Structure for lego information.

## Constants

### MAX_ROUTES

```vyper
MAX_ROUTES: constant(uint256) = 10
```

Maximum number of routes for swaps.

### MAX_TOKEN_PATH

```vyper
MAX_TOKEN_PATH: constant(uint256) = 5
```

Maximum number of tokens in a swap path.

### MAX_SWAP_INSTRUCTIONS

```vyper
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
```

Maximum number of swap instructions.

### MAX_LEGOS

```vyper
MAX_LEGOS: constant(uint256) = 20
```

Maximum number of legos.

### HUNDRED_PERCENT

```vyper
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%
```

Constant representing 100% with 2 decimal places.

## Storage Variables

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

Address of the address registry.

### ROUTER_TOKENA

```vyper
ROUTER_TOKENA: public(immutable(address))
```

Address of the first router token.

### ROUTER_TOKENB

```vyper
ROUTER_TOKENB: public(immutable(address))
```

Address of the second router token.

### Yield Lego IDs

```vyper
AAVE_V3_ID: public(immutable(uint256))
COMPOUND_V3_ID: public(immutable(uint256))
EULER_ID: public(immutable(uint256))
FLUID_ID: public(immutable(uint256))
MOONWELL_ID: public(immutable(uint256))
MORPHO_ID: public(immutable(uint256))
SKY_ID: public(immutable(uint256))
```

IDs for various yield legos.

### DEX Lego IDs

```vyper
UNISWAP_V2_ID: public(immutable(uint256))
UNISWAP_V3_ID: public(immutable(uint256))
AERODROME_ID: public(immutable(uint256))
AERODROME_SLIPSTREAM_ID: public(immutable(uint256))
CURVE_ID: public(immutable(uint256))
```

IDs for various DEX legos.

## External Functions

### Yield Lego Accessors

#### aaveV3

```vyper
@view
@external
def aaveV3() -> address:
```

Gets the address of the Aave V3 lego.

**Returns:**
- The address of the Aave V3 lego

#### aaveV3Id

```vyper
@view
@external
def aaveV3Id() -> uint256:
```

Gets the ID of the Aave V3 lego.

**Returns:**
- The ID of the Aave V3 lego

#### compoundV3

```vyper
@view
@external
def compoundV3() -> address:
```

Gets the address of the Compound V3 lego.

**Returns:**
- The address of the Compound V3 lego

#### compoundV3Id

```vyper
@view
@external
def compoundV3Id() -> uint256:
```

Gets the ID of the Compound V3 lego.

**Returns:**
- The ID of the Compound V3 lego

### DEX Lego Accessors

#### uniswapV2

```vyper
@view
@external
def uniswapV2() -> address:
```

Gets the address of the Uniswap V2 lego.

**Returns:**
- The address of the Uniswap V2 lego

#### uniswapV2Id

```vyper
@view
@external
def uniswapV2Id() -> uint256:
```

Gets the ID of the Uniswap V2 lego.

**Returns:**
- The ID of the Uniswap V2 lego

#### uniswapV3

```vyper
@view
@external
def uniswapV3() -> address:
```

Gets the address of the Uniswap V3 lego.

**Returns:**
- The address of the Uniswap V3 lego

#### uniswapV3Id

```vyper
@view
@external
def uniswapV3Id() -> uint256:
```

Gets the ID of the Uniswap V3 lego.

**Returns:**
- The ID of the Uniswap V3 lego

### Helper Functions

#### getUnderlyingForUser

```vyper
@view
@external
def getUnderlyingForUser(_user: address, _vaultToken: address) -> uint256:
```

Gets the amount of underlying tokens a user has in a vault.

**Parameters:**
- `_user`: The address of the user
- `_vaultToken`: The address of the vault token

**Returns:**
- The amount of underlying tokens

#### getUnderlyingAsset

```vyper
@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
```

Gets the underlying asset of a vault token.

**Parameters:**
- `_vaultToken`: The address of the vault token

**Returns:**
- The address of the underlying asset

#### getAmountOut

```vyper
@view
@external
def getAmountOut(_legoId: uint256, _tokenIn: address, _tokenOut: address, _amountIn: uint256, _pool: address) -> uint256:
```

Gets the expected output amount for a swap.

**Parameters:**
- `_legoId`: The ID of the lego to use
- `_tokenIn`: The address of the input token
- `_tokenOut`: The address of the output token
- `_amountIn`: The amount of input tokens
- `_pool`: The address of the pool to use

**Returns:**
- The expected amount of output tokens

#### getBestSwapRoute

```vyper
@view
@external
def getBestSwapRoute(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> SwapRoute:
```

Gets the best swap route for a given pair of tokens.

**Parameters:**
- `_tokenIn`: The address of the input token
- `_tokenOut`: The address of the output token
- `_amountIn`: The amount of input tokens

**Returns:**
- The best swap route

#### getSwapInstructions

```vyper
@view
@external
def getSwapInstructions(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]:
```

Gets swap instructions for a given pair of tokens.

**Parameters:**
- `_tokenIn`: The address of the input token
- `_tokenOut`: The address of the output token
- `_amountIn`: The amount of input tokens

**Returns:**
- Array of swap instructions 