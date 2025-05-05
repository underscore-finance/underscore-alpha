# UserWalletTemplate (WalletFunds)

**Source:** `contracts/core/templates/UserWalletTemplate.vy`

The UserWalletTemplate contract handles the management of user funds within the wallet, including deposit and withdrawal functionality, asset tracking, and security measures.

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

Flag defining types of actions that can be performed.

## Structs

### CoreData

```vyper
struct CoreData:
    owner: address
    wallet: address
    walletConfig: address
    addyRegistry: address
    agentFactory: address
    legoRegistry: address
    priceSheets: address
    oracleRegistry: address
    trialFundsAsset: address
    trialFundsInitialAmount: uint256
```

Structure containing core contract addresses and data.

### SubPaymentInfo

```vyper
struct SubPaymentInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    didChange: bool
```

Structure containing subscription payment details.

### SwapInstruction

```vyper
struct SwapInstruction:
    legoId: uint256
    amountIn: uint256
    minAmountOut: uint256
    tokenPath: DynArray[address, MAX_TOKEN_PATH]
    poolPath: DynArray[address, MAX_TOKEN_PATH - 1]
```

Structure containing swap instruction details.

### VaultTokenInfo

```vyper
struct VaultTokenInfo:
    legoId: uint256
    vaultToken: address
```

Structure containing information about a vault token.

## Events

### UserWalletDeposit

```vyper
event UserWalletDeposit:
    signer: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    refundAssetAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when tokens are deposited into a vault.

### UserWalletWithdrawal

```vyper
event UserWalletWithdrawal:
    signer: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    refundVaultTokenAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when tokens are withdrawn from a vault.

### UserWalletSwap

```vyper
event UserWalletSwap:
    signer: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    swapAmount: uint256
    toAmount: uint256
    refundAssetAmount: uint256
    usdValue: uint256
    numTokens: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when tokens are swapped.

### UserWalletBorrow

```vyper
event UserWalletBorrow:
    signer: indexed(address)
    borrowAsset: indexed(address)
    borrowAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when assets are borrowed.

### UserWalletRepayDebt

```vyper
event UserWalletRepayDebt:
    signer: indexed(address)
    paymentAsset: indexed(address)
    paymentAmount: uint256
    usdValue: uint256
    remainingDebt: uint256
    legoId: uint256
    legoAddr: indexed(address)
    isSignerAgent: bool
```

Emitted when debt is repaid.

### UserWalletLiquidityAdded

```vyper
event UserWalletLiquidityAdded:
    signer: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    liqAmountA: uint256
    liqAmountB: uint256
    liquidityAdded: uint256
    pool: address
    usdValue: uint256
    refundAssetAmountA: uint256
    refundAssetAmountB: uint256
    nftTokenId: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when liquidity is added to a pool.

### UserWalletLiquidityRemoved

```vyper
event UserWalletLiquidityRemoved:
    signer: indexed(address)
    tokenA: indexed(address)
    tokenB: address
    removedAmountA: uint256
    removedAmountB: uint256
    usdValue: uint256
    isDepleted: bool
    liquidityRemoved: uint256
    lpToken: indexed(address)
    refundedLpAmount: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when liquidity is removed from a pool.

### UserWalletFundsTransferred

```vyper
event UserWalletFundsTransferred:
    signer: indexed(address)
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    isSignerAgent: bool
```

Emitted when funds are transferred to a recipient.

### UserWalletRewardsClaimed

```vyper
event UserWalletRewardsClaimed:
    signer: address
    market: address
    rewardToken: address
    rewardAmount: uint256
    usdValue: uint256
    proof: bytes32
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool
```

Emitted when rewards are claimed.

### UserWalletEthConvertedToWeth

```vyper
event UserWalletEthConvertedToWeth:
    signer: indexed(address)
    amount: uint256
    paidEth: uint256
    weth: indexed(address)
    isSignerAgent: bool
```

Emitted when ETH is converted to WETH.

### UserWalletWethConvertedToEth

```vyper
event UserWalletWethConvertedToEth:
    signer: indexed(address)
    amount: uint256
    weth: indexed(address)
    isSignerAgent: bool
```

Emitted when WETH is converted to ETH.

### UserWalletSubscriptionPaid

```vyper
event UserWalletSubscriptionPaid:
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    isAgent: bool
```

Emitted when a subscription payment is made.

### UserWalletTransactionFeePaid

```vyper
event UserWalletTransactionFeePaid:
    asset: indexed(address)
    protocolRecipient: indexed(address)
    protocolAmount: uint256
    ambassadorRecipient: indexed(address)
    ambassadorAmount: uint256
    fee: uint256
    action: ActionType
```

Emitted when a transaction fee is paid.

### UserWalletTrialFundsRecovered

```vyper
event UserWalletTrialFundsRecovered:
    asset: indexed(address)
    amountRecovered: uint256
    remainingAmount: uint256
```

Emitted when trial funds are recovered.

### UserWalletNftRecovered

```vyper
event UserWalletNftRecovered:
    collection: indexed(address)
    nftTokenId: uint256
    owner: indexed(address)
```

Emitted when an NFT is recovered.

## Storage Variables

### walletConfig

```vyper
walletConfig: public(address)
```

The address of the wallet configuration contract.

### trialFundsAsset

```vyper
trialFundsAsset: public(address)
```

The address of the trial funds asset.

### trialFundsInitialAmount

```vyper
trialFundsInitialAmount: public(uint256)
```

The initial amount of trial funds.

### wethAddr

```vyper
wethAddr: public(address)
```

The address of the WETH contract.

## Constants

### AGENT_FACTORY_ID

```vyper
AGENT_FACTORY_ID: constant(uint256) = 1
```

ID of the agent factory in the address registry.

### LEGO_REGISTRY_ID

```vyper
LEGO_REGISTRY_ID: constant(uint256) = 2
```

ID of the lego registry in the address registry.

### PRICE_SHEETS_ID

```vyper
PRICE_SHEETS_ID: constant(uint256) = 3
```

ID of the price sheets in the address registry.

### ORACLE_REGISTRY_ID

```vyper
ORACLE_REGISTRY_ID: constant(uint256) = 4
```

ID of the oracle registry in the address registry.

### MAX_SWAP_INSTRUCTIONS

```vyper
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
```

Maximum number of swap instructions allowed.

### MAX_TOKEN_PATH

```vyper
MAX_TOKEN_PATH: constant(uint256) = 5
```

Maximum number of tokens in a swap path.

### MAX_ASSETS

```vyper
MAX_ASSETS: constant(uint256) = 25
```

Maximum number of assets allowed.

### MAX_LEGOS

```vyper
MAX_LEGOS: constant(uint256) = 20
```

Maximum number of legos allowed.

### MAX_VAULTS_FOR_USER

```vyper
MAX_VAULTS_FOR_USER: constant(uint256) = 30
```

Maximum number of vaults for a user.

### MAX_MIGRATION_ASSETS

```vyper
MAX_MIGRATION_ASSETS: constant(uint256) = 40
```

Maximum number of assets for migration.

### MAX_MIGRATION_WHITELIST

```vyper
MAX_MIGRATION_WHITELIST: constant(uint256) = 20
```

Maximum number of addresses in migration whitelist.

### HUNDRED_PERCENT

```vyper
HUNDRED_PERCENT: constant(uint256) = 100_00
```

Represents 100.00% in basis points.

### ERC721_RECEIVE_DATA

```vyper
ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UnderscoreErc721"
```

Data used for ERC721 receive operations.

### API_VERSION

```vyper
API_VERSION: constant(String[28]) = "0.0.3"
```

API version of the contract.

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

The address of the AddyRegistry contract.

## External Functions

### **default**

```vyper
@payable
@external
def __default__():
```

Default function to receive ETH.

### onERC721Received

```vyper
@view
@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
```

Handles the receipt of an NFT.

**Parameters:**

- `_operator`: The address which called the function
- `_owner`: The address which previously owned the token
- `_tokenId`: The NFT identifier
- `_data`: Additional data with no specified format

**Returns:**

- The function selector

### apiVersion

```vyper
@pure
@external
def apiVersion() -> String[28]:
```

Returns the current API version of the contract.

**Returns:**

- String representing the API version

### canBeAmbassador

```vyper
@view
@external
def canBeAmbassador() -> bool:
```

Checks if the current wallet can be an ambassador.

**Returns:**

- True if the wallet can be an ambassador, False otherwise

### depositTokens

```vyper
@external
def depositTokens(
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256 = max_value(uint256),
) -> (uint256, address, uint256, uint256):
```

Deposits tokens into a specified lego integration and vault.

**Parameters:**

- `_legoId`: The ID of the lego to use for deposit
- `_asset`: The address of the token to deposit
- `_vault`: The target vault address
- `_amount`: The amount to deposit (defaults to max)

**Returns:**

- The amount of assets deposited
- The vault token address
- The amount of vault tokens received
- The USD value of the transaction

### withdrawTokens

```vyper
@external
def withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256 = max_value(uint256),
) -> (uint256, uint256, uint256):
```

Withdraws tokens from a specified lego integration and vault.

**Parameters:**

- `_legoId`: The ID of the lego to use for withdrawal
- `_asset`: The address of the token to withdraw
- `_vaultToken`: The vault token address
- `_vaultTokenAmount`: The amount of vault tokens to withdraw (defaults to max)

**Returns:**

- The amount of assets received
- The amount of vault tokens burned
- The USD value of the transaction

### rebalance

```vyper
@external
def rebalance(
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVault: address,
    _fromVaultTokenAmount: uint256 = max_value(uint256),
) -> (uint256, address, uint256, uint256):
```

Withdraws tokens from one lego and deposits them into another (always same asset).

**Parameters:**

- `_fromLegoId`: The ID of the source lego
- `_fromAsset`: The address of the token to rebalance
- `_fromVaultToken`: The source vault token address
- `_toLegoId`: The ID of the destination lego
- `_toVault`: The destination vault address
- `_fromVaultTokenAmount`: The amount of source vault tokens to rebalance (defaults to max)

**Returns:**

- The amount of assets deposited
- The destination vault token address
- The amount of destination vault tokens received
- The USD value of the transaction

### swapTokens

```vyper
@external
def swapTokens(_swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (uint256, uint256, uint256):
```

Swaps tokens using specified instructions.

**Parameters:**

- `_swapInstructions`: Array of swap instructions

**Returns:**

- The amount swapped
- The amount received
- The USD value of the transaction

### borrow

```vyper
@external
def borrow(
    _legoId: uint256,
    _borrowAsset: address = empty(address),
    _amount: uint256 = max_value(uint256),
) -> (address, uint256, uint256):
```

Borrows assets from a specified lego integration.

**Parameters:**

- `_legoId`: The ID of the lego to use for borrowing
- `_borrowAsset`: The address of the asset to borrow (defaults to empty)
- `_amount`: The amount to borrow (defaults to max)

**Returns:**

- The borrowed asset address
- The amount borrowed
- The USD value of the transaction

### repayDebt

```vyper
@external
def repayDebt(
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
) -> (address, uint256, uint256, uint256):
```

Repays debt to a specified lego integration.

**Parameters:**

- `_legoId`: The ID of the lego to use for repayment
- `_paymentAsset`: The address of the asset to use for repayment
- `_paymentAmount`: The amount to repay (defaults to max)

**Returns:**

- The payment asset address
- The amount paid
- The USD value of the transaction
- The remaining debt

### addLiquidity

```vyper
@external
def addLiquidity(
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
) -> (uint256, uint256, uint256, uint256, uint256):
```

Adds liquidity to a pool.

**Parameters:**

- `_legoId`: The ID of the lego to use
- `_nftAddr`: The NFT address (for concentrated liquidity positions)
- `_nftTokenId`: The NFT token ID
- `_pool`: The pool address
- `_tokenA`: The first token address
- `_tokenB`: The second token address
- `_amountA`: The amount of the first token to add (defaults to max)
- `_amountB`: The amount of the second token to add (defaults to max)
- `_tickLower`: The lower tick bound (for concentrated liquidity)
- `_tickUpper`: The upper tick bound (for concentrated liquidity)
- `_minAmountA`: The minimum amount of token A to use
- `_minAmountB`: The minimum amount of token B to use
- `_minLpAmount`: The minimum LP tokens to receive

**Returns:**

- The amount of token A used
- The amount of token B used
- The amount of LP tokens received
- The USD value of the transaction
- The NFT token ID (for concentrated liquidity positions)

### removeLiquidity

```vyper
@external
def removeLiquidity(
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _liqToRemove: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
) -> (uint256, uint256, uint256, bool):
```

Removes liquidity from a pool.

**Parameters:**

- `_legoId`: The ID of the lego to use
- `_nftAddr`: The NFT address (for concentrated liquidity positions)
- `_nftTokenId`: The NFT token ID
- `_pool`: The pool address
- `_tokenA`: The first token address
- `_tokenB`: The second token address
- `_liqToRemove`: The amount of liquidity to remove (defaults to max)
- `_minAmountA`: The minimum amount of token A to receive
- `_minAmountB`: The minimum amount of token B to receive

**Returns:**

- The amount of token A received
- The amount of token B received
- The USD value of the transaction
- Whether all liquidity was removed

### transferFunds

```vyper
@external
def transferFunds(
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
) -> (uint256, uint256):
```

Transfers funds to a recipient.

**Parameters:**

- `_recipient`: The recipient address
- `_amount`: The amount to transfer (defaults to max)
- `_asset`: The asset to transfer (defaults to empty)

**Returns:**

- The amount transferred
- The USD value of the transaction

### claimRewards

```vyper
@external
def claimRewards(
    _legoId: uint256,
    _market: address = empty(address),
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _proof: bytes32 = empty(bytes32),
):
```

Claims rewards for a position.

**Parameters:**

- `_legoId`: The ID of the lego to use
- `_market`: The market address
- `_rewardToken`: The reward token address
- `_rewardAmount`: The reward amount to claim
- `_proof`: The proof for claiming rewards

### convertEthToWeth

```vyper
@external
def convertEthToWeth(
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
) -> (uint256, address, uint256):
```

Converts ETH to WETH and optionally deposits into a vault.

**Parameters:**

- `_amount`: The amount of ETH to convert (defaults to max)
- `_depositLegoId`: The ID of the lego to deposit WETH into (0 means no deposit)
- `_depositVault`: The vault address to deposit WETH into

**Returns:**

- The amount of ETH converted
- The vault token address (if deposited)
- The amount of vault tokens received (if deposited)

### convertWethToEth

```vyper
@external
def convertWethToEth(
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
) -> uint256:
```

Converts WETH to ETH, optionally first withdrawing from a vault.

**Parameters:**

- `_amount`: The amount of WETH to convert (defaults to max)
- `_recipient`: The recipient for the ETH (defaults to empty, meaning this wallet)
- `_withdrawLegoId`: The ID of the lego to withdraw WETH from (0 means no withdrawal)
- `_withdrawVaultToken`: The vault token address to withdraw from

**Returns:**

- The amount of ETH received

### recoverERC721

```vyper
@external
def recoverERC721(_collection: address, _tokenId: uint256) -> bool:
```

Recovers an ERC721 token held by the wallet.

**Parameters:**

- `_collection`: The collection address
- `_tokenId`: The token ID

**Returns:**

- True if the recovery was successful

### recoverTrialFunds

```vyper
@external
def recoverTrialFunds(_opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]) -> bool:
```

Recovers trial funds from various opportunities.

**Parameters:**

- `_opportunities`: Array of opportunities to recover funds from

**Returns:**

- True if the recovery was successful
