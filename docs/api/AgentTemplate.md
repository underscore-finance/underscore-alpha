# AgentTemplate

The AgentTemplate contract serves as a template for AI agents in the Underscore system. It provides functionality for managing user funds, executing various DeFi operations, and handling ownership changes.

**Source:** `contracts/core/AgentTemplate.vy`

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

Flag defining the types of actions that can be performed in batch operations.

## Structs

### Signature

```vyper
struct Signature:
    signature: Bytes[65]
    signer: address
    expiration: uint256
```

Structure for signature verification.

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

### ActionInstruction

```vyper
struct ActionInstruction:
    usePrevAmountOut: bool
    action: ActionType
    legoId: uint256
    asset: address
    vault: address
    amount: uint256
    altLegoId: uint256
    altAsset: address
    altVault: address
    altAmount: uint256
    minAmountOut: uint256
    pool: address
    proof: bytes32
    nftAddr: address
    nftTokenId: uint256
    tickLower: int24
    tickUpper: int24
    minAmountA: uint256
    minAmountB: uint256
    minLpAmount: uint256
    liqToRemove: uint256
    recipient: address
    isWethToEthConversion: bool
```

Structure for batch action instructions.

### PendingOwner

```vyper
struct PendingOwner:
    newOwner: address
    initiatedBlock: uint256
    confirmBlock: uint256
```

Structure for pending ownership changes.

## Events

### AgentOwnershipChangeInitiated

```vyper
event AgentOwnershipChangeInitiated:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    confirmBlock: uint256
```

Emitted when an ownership change is initiated.

### AgentOwnershipChangeConfirmed

```vyper
event AgentOwnershipChangeConfirmed:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
```

Emitted when an ownership change is confirmed.

### AgentOwnershipChangeCancelled

```vyper
event AgentOwnershipChangeCancelled:
    cancelledOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
```

Emitted when an ownership change is cancelled.

### AgentOwnershipChangeDelaySet

```vyper
event AgentOwnershipChangeDelaySet:
    delayBlocks: uint256
```

Emitted when the ownership change delay is set.

### AgentFundsRecovered

```vyper
event AgentFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256
```

Emitted when funds are recovered from the agent.

## Storage Variables

### initialized

```vyper
initialized: public(bool)
```

Flag indicating if the contract has been initialized.

### usedSignatures

```vyper
usedSignatures: public(HashMap[Bytes[65], bool])
```

Mapping to track used signatures to prevent replay attacks.

### owner

```vyper
owner: public(address)
```

The owner of the agent.

### pendingOwner

```vyper
pendingOwner: public(PendingOwner)
```

Information about a pending ownership change.

### ownershipChangeDelay

```vyper
ownershipChangeDelay: public(uint256)
```

Number of blocks to wait before an ownership change can be confirmed.

## Constants

### MIN_OWNER_CHANGE_DELAY

```vyper
MIN_OWNER_CHANGE_DELAY: public(immutable(uint256))
```

Minimum number of blocks for ownership change delay.

### MAX_OWNER_CHANGE_DELAY

```vyper
MAX_OWNER_CHANGE_DELAY: public(immutable(uint256))
```

Maximum number of blocks for ownership change delay.

### MAX_INSTRUCTIONS

```vyper
MAX_INSTRUCTIONS: constant(uint256) = 20
```

Maximum number of instructions in a batch action.

### MAX_SWAP_INSTRUCTIONS

```vyper
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
```

Maximum number of swap instructions.

### MAX_TOKEN_PATH

```vyper
MAX_TOKEN_PATH: constant(uint256) = 5
```

Maximum number of tokens in a swap path.

### API_VERSION

```vyper
API_VERSION: constant(String[28]) = "0.0.1"
```

The API version of the contract.

## External Functions

### initialize

```vyper
@external
def initialize(_owner: address) -> bool:
```

Initializes a new agent instance.

**Parameters:**
- `_owner`: The address that will own the agent

**Returns:**
- True if initialization was successful

**Requirements:**
- Contract must not be already initialized
- Owner address must not be empty

### apiVersion

```vyper
@pure
@external
def apiVersion() -> String[28]:
```

Returns the API version of the contract.

**Returns:**
- String representing the API version

### depositTokens

```vyper
@external
def depositTokens(
    _userWallet: address,
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256, uint256):
```

Deposits tokens into a yield-generating vault on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_asset`: Address of the token to deposit
- `_vault`: Address of the vault to deposit into
- `_amount`: Amount of tokens to deposit
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing deposit information (legoId, asset address, amount deposited, vault tokens received)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### withdrawTokens

```vyper
@external
def withdrawTokens(
    _userWallet: address,
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256):
```

Withdraws tokens from a yield position on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_asset`: Address of the underlying token
- `_vaultToken`: Address of the vault token to withdraw
- `_vaultTokenAmount`: Amount of vault tokens to withdraw
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing withdrawal information (legoId, amount withdrawn, vault tokens burned)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### rebalance

```vyper
@external
def rebalance(
    _userWallet: address,
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVault: address,
    _fromVaultTokenAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256, uint256):
```

Rebalances funds from one yield position to another on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_fromLegoId`: ID of the source lego (protocol)
- `_fromAsset`: Address of the source token
- `_fromVaultToken`: Address of the source vault token
- `_toLegoId`: ID of the destination lego (protocol)
- `_toVault`: Address of the destination vault
- `_fromVaultTokenAmount`: Amount of source vault tokens to rebalance
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing rebalance information (legoId, asset address, amount deposited, vault tokens received)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### swapTokens

```vyper
@external
def swapTokens(
    _userWallet: address,
    _swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS],
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256):
```

Swaps tokens on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_swapInstructions`: Array of swap instructions
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing swap information (legoId, amount in, amount out)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### getSwapActionHash

```vyper
@view
@external
def getSwapActionHash(
    _userWallet: address,
    _swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS],
    _expiration: uint256,
) -> bytes32:
```

Gets the hash of a swap action for signature verification.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_swapInstructions`: Array of swap instructions
- `_expiration`: Expiration timestamp for the signature

**Returns:**
- Hash of the swap action

### borrow

```vyper
@external
def borrow(
    _userWallet: address,
    _legoId: uint256,
    _borrowAsset: address = empty(address),
    _amount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (address, uint256, uint256):
```

Borrows assets from a lending protocol on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_borrowAsset`: Address of the asset to borrow
- `_amount`: Amount to borrow
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing borrow information (asset address, amount borrowed, debt token amount)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### repayDebt

```vyper
@external
def repayDebt(
    _userWallet: address,
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (address, uint256, uint256, uint256):
```

Repays debt to a lending protocol on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_paymentAsset`: Address of the asset to repay with
- `_paymentAmount`: Amount to repay
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing repay information (asset address, amount repaid, debt token amount, remaining debt)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### claimRewards

```vyper
@external
def claimRewards(
    _userWallet: address,
    _legoId: uint256,
    _market: address = empty(address),
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _proof: bytes32 = empty(bytes32),
    _sig: Signature = empty(Signature),
):
```

Claims rewards from a protocol on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_market`: Address of the market to claim rewards from
- `_rewardToken`: Address of the reward token
- `_rewardAmount`: Amount of rewards to claim
- `_proof`: Merkle proof for claiming rewards
- `_sig`: Signature data for verification

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### addLiquidity

```vyper
@external
def addLiquidity(
    _userWallet: address,
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _tickLower: int24 = min_value(int24),
    _tickUpper: int24 = max_value(int24),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _minLpAmount: uint256 = 0,
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256, uint256, uint256):
```

Adds liquidity to a pool on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_nftAddr`: Address of the NFT contract
- `_nftTokenId`: ID of the NFT token
- `_pool`: Address of the pool
- `_tokenA`: Address of token A
- `_tokenB`: Address of token B
- `_amountA`: Amount of token A to add
- `_amountB`: Amount of token B to add
- `_tickLower`: Lower tick for concentrated liquidity
- `_tickUpper`: Upper tick for concentrated liquidity
- `_minAmountA`: Minimum amount of token A to add
- `_minAmountB`: Minimum amount of token B to add
- `_minLpAmount`: Minimum amount of LP tokens to receive
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing liquidity information (legoId, amount A, amount B, LP amount, NFT token ID)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### removeLiquidity

```vyper
@external
def removeLiquidity(
    _userWallet: address,
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _liqToRemove: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256, bool):
```

Removes liquidity from a pool on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_legoId`: ID of the lego (protocol) to use
- `_nftAddr`: Address of the NFT contract
- `_nftTokenId`: ID of the NFT token
- `_pool`: Address of the pool
- `_tokenA`: Address of token A
- `_tokenB`: Address of token B
- `_liqToRemove`: Amount of liquidity to remove
- `_minAmountA`: Minimum amount of token A to receive
- `_minAmountB`: Minimum amount of token B to receive
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing removal information (amount A received, amount B received, liquidity removed, success)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### transferFunds

```vyper
@external
def transferFunds(
    _userWallet: address,
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256):
```

Transfers funds from a user wallet to a recipient.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_recipient`: The address of the recipient
- `_amount`: Amount to transfer
- `_asset`: Address of the asset to transfer
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing transfer information (amount transferred, balance after transfer)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### convertEthToWeth

```vyper
@external
def convertEthToWeth(
    _userWallet: address,
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
```

Converts ETH to WETH on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_amount`: Amount of ETH to convert
- `_depositLegoId`: ID of the lego (protocol) to deposit to after conversion
- `_depositVault`: Address of the vault to deposit to after conversion
- `_sig`: Signature data for verification

**Returns:**
- Tuple containing conversion information (amount converted, vault address, vault tokens received)

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### convertWethToEth

```vyper
@external
def convertWethToEth(
    _userWallet: address,
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
    _sig: Signature = empty(Signature),
) -> uint256:
```

Converts WETH to ETH on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_amount`: Amount of WETH to convert
- `_recipient`: Address to receive the ETH
- `_withdrawLegoId`: ID of the lego (protocol) to withdraw from before conversion
- `_withdrawVaultToken`: Address of the vault token to withdraw before conversion
- `_sig`: Signature data for verification

**Returns:**
- Amount of ETH converted

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used

### performBatchActions

```vyper
@external
def performBatchActions(
    _userWallet: address,
    _instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS],
    _sig: Signature = empty(Signature),
) -> bool:
```

Performs a batch of actions on behalf of a user wallet.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_instructions`: Array of action instructions to execute
- `_sig`: Signature data for verification

**Returns:**
- True if all actions were executed successfully

**Requirements:**
- Valid signature from the wallet owner
- Signature not expired
- Signature not already used
- At least one instruction provided

### getBatchActionHash

```vyper
@view
@external
def getBatchActionHash(
    _userWallet: address, 
    _instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS], 
    _expiration: uint256
) -> bytes32:
```

Gets the hash of a batch action for signature verification.

**Parameters:**
- `_userWallet`: The address of the user wallet
- `_instructions`: Array of action instructions
- `_expiration`: Expiration timestamp for the signature

**Returns:**
- Hash of the batch action

### DOMAIN_SEPARATOR

```vyper
@view
@external
def DOMAIN_SEPARATOR() -> bytes32:
```

Returns the domain separator used for EIP-712 signatures.

**Returns:**
- Domain separator as bytes32

### changeOwnership

```vyper
@external
def changeOwnership(_newOwner: address):
```

Initiates a change of ownership for the agent.

**Parameters:**
- `_newOwner`: The address of the new owner

**Events Emitted:**
- `AgentOwnershipChangeInitiated(prevOwner, newOwner, confirmBlock)`

**Requirements:**
- Can only be called by the current owner
- New owner address must not be empty or the current owner

### confirmOwnershipChange

```vyper
@external
def confirmOwnershipChange():
```

Confirms a pending ownership change.

**Events Emitted:**
- `AgentOwnershipChangeConfirmed(prevOwner, newOwner, initiatedBlock, confirmBlock)`

**Requirements:**
- Can only be called by the pending new owner
- Time delay must have passed since initiation

### cancelOwnershipChange

```vyper
@external
def cancelOwnershipChange():
```

Cancels a pending ownership change.

**Events Emitted:**
- `AgentOwnershipChangeCancelled(cancelledOwner, initiatedBlock, confirmBlock)`

**Requirements:**
- Can only be called by the current owner
- A pending ownership change must exist

### setOwnershipChangeDelay

```vyper
@external
def setOwnershipChangeDelay(_numBlocks: uint256):
```

Sets the delay (in blocks) required for ownership changes.

**Parameters:**
- `_numBlocks`: The number of blocks to wait before ownership can be changed

**Events Emitted:**
- `AgentOwnershipChangeDelaySet(delayBlocks)`

**Requirements:**
- Can only be called by the owner
- Delay must be within allowed range

### recoverFunds

```vyper
@external
def recoverFunds(_asset: address) -> bool:
```

Recovers funds from the agent contract to the owner.

**Parameters:**
- `_asset`: The address of the asset to recover

**Returns:**
- True if the funds were recovered successfully

**Events Emitted:**
- `AgentFundsRecovered(asset, recipient, balance)`

**Requirements:**
- Can only be called by the owner
- Asset address must not be empty
- Balance must be greater than zero 