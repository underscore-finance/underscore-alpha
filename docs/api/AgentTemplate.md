# AgentTemplate

The AgentTemplate contract serves as a template for AI agents in the Underscore system. It provides functionality for managing user funds, executing various DeFi operations, and handling ownership changes.

**Source:** `contracts/core/templates/AgentTemplate.vy`

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
    swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]
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
API_VERSION: constant(String[28]) = "0.0.2"
```

The API version of the contract.

### DOMAIN_TYPE_HASH

```vyper
DOMAIN_TYPE_HASH: constant(bytes32) = keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)')
```

EIP-712 domain type hash.

### DEPOSIT_TYPE_HASH

```vyper
DEPOSIT_TYPE_HASH: constant(bytes32) = keccak256('Deposit(address userWallet,uint256 legoId,address asset,address vault,uint256 amount,uint256 expiration)')
```

Type hash for deposit signatures.

### WITHDRAWAL_TYPE_HASH

```vyper
WITHDRAWAL_TYPE_HASH: constant(bytes32) = keccak256('Withdrawal(address userWallet,uint256 legoId,address asset,address vaultToken,uint256 vaultTokenAmount,uint256 expiration)')
```

Type hash for withdrawal signatures.

### REBALANCE_TYPE_HASH

```vyper
REBALANCE_TYPE_HASH: constant(bytes32) = keccak256('Rebalance(address userWallet,uint256 fromLegoId,address fromAsset,address fromVaultToken,uint256 toLegoId,address toVault,uint256 fromVaultTokenAmount,uint256 expiration)')
```

Type hash for rebalance signatures.

### SWAP_ACTION_TYPE_HASH

```vyper
SWAP_ACTION_TYPE_HASH: constant(bytes32) =  keccak256('Swap(address userWallet,SwapInstruction[] swapInstructions,uint256 expiration)')
```

Type hash for swap signatures.

### SWAP_INSTRUCTION_TYPE_HASH

```vyper
SWAP_INSTRUCTION_TYPE_HASH: constant(bytes32) = keccak256('SwapInstruction(uint256 legoId,uint256 amountIn,uint256 minAmountOut,address[] tokenPath,address[] poolPath)')
```

Type hash for swap instruction signatures.

### ADD_LIQ_TYPE_HASH

```vyper
ADD_LIQ_TYPE_HASH: constant(bytes32) = keccak256('AddLiquidity(address userWallet,uint256 legoId,address nftAddr,uint256 nftTokenId,address pool,address tokenA,address tokenB,uint256 amountA,uint256 amountB,int24 tickLower,int24 tickUpper,uint256 minAmountA,uint256 minAmountB,uint256 minLpAmount,uint256 expiration)')
```

Type hash for add liquidity signatures.

### REMOVE_LIQ_TYPE_HASH

```vyper
REMOVE_LIQ_TYPE_HASH: constant(bytes32) = keccak256('RemoveLiquidity(address userWallet,uint256 legoId,address nftAddr,uint256 nftTokenId,address pool,address tokenA,address tokenB,uint256 liqToRemove,uint256 minAmountA,uint256 minAmountB,uint256 expiration)')
```

Type hash for remove liquidity signatures.

### TRANSFER_TYPE_HASH

```vyper
TRANSFER_TYPE_HASH: constant(bytes32) = keccak256('Transfer(address userWallet,address recipient,uint256 amount,address asset,uint256 expiration)')
```

Type hash for transfer signatures.

### ETH_TO_WETH_TYPE_HASH

```vyper
ETH_TO_WETH_TYPE_HASH: constant(bytes32) = keccak256('EthToWeth(address userWallet,uint256 amount,uint256 depositLegoId,address depositVault,uint256 expiration)')
```

Type hash for ETH to WETH conversion signatures.

### WETH_TO_ETH_TYPE_HASH

```vyper
WETH_TO_ETH_TYPE_HASH: constant(bytes32) = keccak256('WethToEth(address userWallet,uint256 amount,address recipient,uint256 withdrawLegoId,address withdrawVaultToken,uint256 expiration)')
```

Type hash for WETH to ETH conversion signatures.

### CLAIM_REWARDS_TYPE_HASH

```vyper
CLAIM_REWARDS_TYPE_HASH: constant(bytes32) = keccak256('ClaimRewards(address userWallet,uint256 legoId,address market,address rewardToken,uint256 rewardAmount,bytes32 proof,uint256 expiration)')
```

Type hash for claim rewards signatures.

### BORROW_TYPE_HASH

```vyper
BORROW_TYPE_HASH: constant(bytes32) = keccak256('Borrow(address userWallet,uint256 legoId,address borrowAsset,uint256 amount,uint256 expiration)')
```

Type hash for borrow signatures.

### REPAY_TYPE_HASH

```vyper
REPAY_TYPE_HASH: constant(bytes32) = keccak256('Repay(address userWallet,uint256 legoId,address paymentAsset,uint256 paymentAmount,uint256 expiration)')
```

Type hash for repay signatures.

### BATCH_ACTIONS_TYPE_HASH

```vyper
BATCH_ACTIONS_TYPE_HASH: constant(bytes32) =  keccak256('BatchActions(address userWallet,ActionInstruction[] instructions,uint256 expiration)')
```

Type hash for batch actions signatures.

### ACTION_INSTRUCTION_TYPE_HASH

```vyper
ACTION_INSTRUCTION_TYPE_HASH: constant(bytes32) = keccak256('ActionInstruction(bool usePrevAmountOut,uint256 action,uint256 legoId,address asset,address vault,uint256 amount,uint256 altLegoId,address altAsset,address altVault,uint256 altAmount,uint256 minAmountOut,address pool,bytes32 proof,address nftAddr,uint256 nftTokenId,int24 tickLower,int24 tickUpper,uint256 minAmountA,uint256 minAmountB,uint256 minLpAmount,uint256 liqToRemove,address recipient,bool isWethToEthConversion,SwapInstruction[] swapInstructions)')
```

Type hash for action instruction signatures.

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
@nonreentrant
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
- `_amount`: Amount of tokens to deposit (defaults to max)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (asset amount deposited, vault token address, vault token amount received, USD value)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### withdrawTokens

```vyper
@nonreentrant
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
- `_vaultTokenAmount`: Amount of vault tokens to withdraw (defaults to max)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (asset amount received, vault token amount burned, USD value)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### rebalance

```vyper
@nonreentrant
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
- `_fromVaultTokenAmount`: Amount of source vault tokens to rebalance (defaults to max)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (asset amount deposited, vault token address, vault token amount received, USD value)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### swapTokens

```vyper
@nonreentrant
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
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (in amount, out amount, USD value)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

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
@nonreentrant
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
- `_borrowAsset`: Address of the asset to borrow (defaults to empty)
- `_amount`: Amount to borrow (defaults to max)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (borrow asset address, amount borrowed, USD value)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### repayDebt

```vyper
@nonreentrant
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
- `_paymentAmount`: Amount to repay (defaults to max)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (payment asset address, payment amount, USD value, remaining debt)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### claimRewards

```vyper
@nonreentrant
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
- `_market`: Address of the market (defaults to empty)
- `_rewardToken`: Address of the reward token (defaults to empty)
- `_rewardAmount`: Amount of rewards to claim (defaults to max)
- `_proof`: Proof for claiming rewards (defaults to empty)
- `_sig`: Signature data for verification (optional)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### addLiquidity

```vyper
@nonreentrant
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
- `_nftAddr`: Address of the NFT contract (for concentrated liquidity)
- `_nftTokenId`: Token ID of the NFT (for concentrated liquidity)
- `_pool`: Address of the pool
- `_tokenA`: Address of token A
- `_tokenB`: Address of token B
- `_amountA`: Amount of token A to add (defaults to max)
- `_amountB`: Amount of token B to add (defaults to max)
- `_tickLower`: Lower tick bound for concentrated liquidity (defaults to min value)
- `_tickUpper`: Upper tick bound for concentrated liquidity (defaults to max value)
- `_minAmountA`: Minimum amount of token A to use (defaults to 0)
- `_minAmountB`: Minimum amount of token B to use (defaults to 0)
- `_minLpAmount`: Minimum LP tokens to receive (defaults to 0)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (amount A used, amount B used, LP tokens received, USD value, NFT token ID)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### removeLiquidity

```vyper
@nonreentrant
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
- `_nftAddr`: Address of the NFT contract (for concentrated liquidity)
- `_nftTokenId`: Token ID of the NFT (for concentrated liquidity)
- `_pool`: Address of the pool
- `_tokenA`: Address of token A
- `_tokenB`: Address of token B
- `_liqToRemove`: Amount of liquidity to remove (defaults to max)
- `_minAmountA`: Minimum amount of token A to receive (defaults to 0)
- `_minAmountB`: Minimum amount of token B to receive (defaults to 0)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (amount A received, amount B received, USD value, is fully depleted)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### transferFunds

```vyper
@nonreentrant
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
- `_recipient`: Address of the recipient
- `_amount`: Amount to transfer (defaults to max)
- `_asset`: Address of the asset to transfer (defaults to empty)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (amount transferred, USD value)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### convertEthToWeth

```vyper
@nonreentrant
@external
def convertEthToWeth(
    _userWallet: address,
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
```

Converts ETH to WETH and optionally deposits it on behalf of a user wallet.

**Parameters:**

- `_userWallet`: The address of the user wallet
- `_amount`: Amount of ETH to convert (defaults to max)
- `_depositLegoId`: ID of the lego to deposit WETH into (defaults to 0, no deposit)
- `_depositVault`: Address of the vault to deposit WETH into (defaults to empty)
- `_sig`: Signature data for verification (optional)

**Returns:**

- A tuple containing (amount converted, vault token address, vault token amount)

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### convertWethToEth

```vyper
@nonreentrant
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

Converts WETH to ETH and optionally withdraws first on behalf of a user wallet.

**Parameters:**

- `_userWallet`: The address of the user wallet
- `_amount`: Amount of WETH to convert (defaults to max)
- `_recipient`: Address to send ETH to (defaults to empty, user wallet)
- `_withdrawLegoId`: ID of the lego to withdraw WETH from (defaults to 0, no withdrawal)
- `_withdrawVaultToken`: Address of the vault token to withdraw (defaults to empty)
- `_sig`: Signature data for verification (optional)

**Returns:**

- The amount of ETH received

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required

### performBatchActions

```vyper
@nonreentrant
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
- `_instructions`: Array of action instructions
- `_sig`: Signature data for verification (optional)

**Returns:**

- True if the batch actions were executed successfully

**Requirements:**

- If msg.sender is not the owner, valid signature from the owner is required
- Non-empty instructions array

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
