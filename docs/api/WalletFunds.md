# WalletFunds API Reference

**File:** `contracts/core/WalletFunds.vy`

The WalletFunds contract handles the management of user funds within the wallet, including deposit and withdrawal functionality, asset tracking, and security measures.

## Structs

### CoreData

```vyper
struct CoreData:
    owner: address
    wallet: address
    walletConfig: address
    addyRegistry: address
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

### TrialFundsOpp

```vyper
struct TrialFundsOpp:
    legoId: uint256
    vaultToken: address
```

Structure containing information about trial funds opportunities.

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
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
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

### addyRegistry

```vyper
addyRegistry: public(address)
```

The address of the address registry.

### wethAddr

```vyper
wethAddr: public(address)
```

The address of the WETH contract.

### initialized

```vyper
initialized: public(bool)
```

Whether the contract has been initialized.

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
API_VERSION: constant(String[28]) = "0.0.1"
```

API version of the contract.

## External Functions

### __default__

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

### initialize

```vyper
@external
def initialize(
    _walletConfig: address,
    _addyRegistry: address,
    _wethAddr: address,
    _trialFundsAsset: address,
    _trialFundsInitialAmount: uint256,
) -> bool:
```

Initializes a new wallet funds instance.

**Parameters:**
- `_walletConfig`: The address of the wallet config contract
- `_addyRegistry`: The address of the address registry
- `_wethAddr`: The address of the WETH contract
- `_trialFundsAsset`: The address of the trial funds asset
- `_trialFundsInitialAmount`: The amount of trial funds to provide

**Returns:**
- True if initialization was successful

**Requirements:**
- Contract must not be already initialized
- Valid wallet config, address registry, and WETH addresses

### apiVersion

```vyper
@pure
@external
def apiVersion() -> String[28]:
```

Returns the current API version of the contract.

**Returns:**
- The API version string

### depositTokens

```vyper
@nonreentrant
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

**Events Emitted:**
- `UserWalletDeposit`

**Requirements:**
- Caller must have permission to deposit
- Valid lego ID and asset address
- Sufficient balance of the asset

### withdrawTokens

```vyper
@nonreentrant
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

**Events Emitted:**
- `UserWalletWithdrawal`

**Requirements:**
- Caller must have permission to withdraw
- Valid lego ID and asset address
- Sufficient balance of the vault token

### rebalance

```vyper
@nonreentrant
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
- `_fromVaultTokenAmount`: The vault token amount to rebalance (defaults to max)

**Returns:**
- The amount of assets deposited in the destination vault
- The destination vault token address
- The amount of destination vault tokens received
- The USD value of the transaction

**Events Emitted:**
- `UserWalletWithdrawal` and `UserWalletDeposit`

**Requirements:**
- Caller must have permission to rebalance
- Valid lego IDs and asset address
- Sufficient balance of the source vault token

### swapTokens

```vyper
@nonreentrant
@external
def swapTokens(
    _swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS],
) -> (uint256, uint256, uint256):
```

Swaps tokens using the specified swap instructions.

**Parameters:**
- `_swapInstructions`: Array of swap instructions

**Returns:**
- The amount of tokens swapped
- The amount of tokens received
- The USD value of the transaction

**Events Emitted:**
- `UserWalletSwap`

**Requirements:**
- Caller must have permission to swap
- Valid lego IDs and asset addresses
- Sufficient balance of the input tokens

### borrow

```vyper
@nonreentrant
@external
def borrow(
    _legoId: uint256,
    _borrowAsset: address,
    _amount: uint256,
) -> (uint256, uint256):
```

Borrows assets from a lending protocol.

**Parameters:**
- `_legoId`: The ID of the lego to use for borrowing
- `_borrowAsset`: The address of the asset to borrow
- `_amount`: The amount to borrow

**Returns:**
- The amount borrowed
- The USD value of the transaction

**Events Emitted:**
- `UserWalletBorrow`

**Requirements:**
- Caller must have permission to borrow
- Valid lego ID and asset address
- Sufficient borrowing capacity

### repayDebt

```vyper
@nonreentrant
@external
def repayDebt(
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
) -> (uint256, uint256, uint256):
```

Repays debt to a lending protocol.

**Parameters:**
- `_legoId`: The ID of the lego to use for repayment
- `_paymentAsset`: The address of the asset to repay with
- `_paymentAmount`: The amount to repay (defaults to max)

**Returns:**
- The amount repaid
- The remaining debt
- The USD value of the transaction

**Events Emitted:**
- `UserWalletRepayDebt`

**Requirements:**
- Caller must have permission to repay
- Valid lego ID and asset address
- Sufficient balance of the payment asset

### claimRewards

```vyper
@nonreentrant
@external
def claimRewards(
    _legoId: uint256,
    _market: address,
    _rewardToken: address,
    _rewardAmount: uint256,
    _proof: bytes32,
) -> (uint256, uint256):
```

Claims rewards from a protocol.

**Parameters:**
- `_legoId`: The ID of the lego to use for claiming rewards
- `_market`: The address of the market
- `_rewardToken`: The address of the reward token
- `_rewardAmount`: The amount of rewards to claim
- `_proof`: The proof for claiming rewards

**Returns:**
- The amount of rewards claimed
- The USD value of the transaction

**Events Emitted:**
- `UserWalletRewardsClaimed`

**Requirements:**
- Caller must have permission to claim rewards
- Valid lego ID and market address
- Valid proof for claiming rewards

### addLiquidity

```vyper
@nonreentrant
@external
def addLiquidity(
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _tickLower: int24,
    _tickUpper: int24,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
) -> (uint256, uint256, uint256, uint256, uint256, uint256):
```

Adds liquidity to a pool.

**Parameters:**
- `_legoId`: The ID of the lego to use for adding liquidity
- `_nftAddr`: The address of the NFT contract
- `_nftTokenId`: The token ID of the NFT
- `_pool`: The address of the pool
- `_tokenA`: The address of token A
- `_tokenB`: The address of token B
- `_amountA`: The amount of token A to add
- `_amountB`: The amount of token B to add
- `_tickLower`: The lower tick bound
- `_tickUpper`: The upper tick bound
- `_minAmountA`: The minimum amount of token A to add
- `_minAmountB`: The minimum amount of token B to add
- `_minLpAmount`: The minimum amount of LP tokens to receive

**Returns:**
- The amount of token A added
- The amount of token B added
- The amount of liquidity added
- The USD value of the transaction
- The refund amount of token A
- The refund amount of token B

**Events Emitted:**
- `UserWalletLiquidityAdded`

**Requirements:**
- Caller must have permission to add liquidity
- Valid lego ID and pool address
- Sufficient balance of tokens A and B

### removeLiquidity

```vyper
@nonreentrant
@external
def removeLiquidity(
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _liqToRemove: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
) -> (uint256, uint256, uint256, bool, uint256, uint256):
```

Removes liquidity from a pool.

**Parameters:**
- `_legoId`: The ID of the lego to use for removing liquidity
- `_nftAddr`: The address of the NFT contract
- `_nftTokenId`: The token ID of the NFT
- `_pool`: The address of the pool
- `_tokenA`: The address of token A
- `_tokenB`: The address of token B
- `_liqToRemove`: The amount of liquidity to remove
- `_minAmountA`: The minimum amount of token A to receive
- `_minAmountB`: The minimum amount of token B to receive

**Returns:**
- The amount of token A received
- The amount of token B received
- The USD value of the transaction
- Whether the position was fully depleted
- The amount of liquidity removed
- The refund amount of LP tokens

**Events Emitted:**
- `UserWalletLiquidityRemoved`

**Requirements:**
- Caller must have permission to remove liquidity
- Valid lego ID and pool address
- Sufficient balance of LP tokens

### transferFunds

```vyper
@nonreentrant
@external
def transferFunds(
    _recipient: address,
    _amount: uint256,
    _asset: address,
) -> (uint256, uint256):
```

Transfers funds to a recipient.

**Parameters:**
- `_recipient`: The address of the recipient
- `_amount`: The amount to transfer
- `_asset`: The address of the asset to transfer

**Returns:**
- The amount transferred
- The USD value of the transaction

**Events Emitted:**
- `UserWalletFundsTransferred`

**Requirements:**
- Caller must have permission to transfer
- Valid recipient and asset address
- Sufficient balance of the asset
- Recipient must be allowed

### convertEthToWeth

```vyper
@nonreentrant
@payable
@external
def convertEthToWeth(
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
) -> (uint256, uint256):
```

Converts ETH to WETH and optionally deposits to a vault.

**Parameters:**
- `_depositLegoId`: The ID of the lego to use for deposit (optional)
- `_depositVault`: The address of the vault to deposit to (optional)

**Returns:**
- The amount of ETH converted
- The amount of WETH received

**Events Emitted:**
- `UserWalletEthConvertedToWeth`
- `UserWalletDeposit` (if depositing)

**Requirements:**
- Caller must have permission to convert
- ETH must be sent with the transaction
- Valid lego ID and vault address if depositing

### convertWethToEth

```vyper
@nonreentrant
@external
def convertWethToEth(
    _amount: uint256,
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
) -> (uint256, uint256):
```

Converts WETH to ETH and optionally withdraws from a vault.

**Parameters:**
- `_amount`: The amount to convert
- `_recipient`: The address of the recipient (optional)
- `_withdrawLegoId`: The ID of the lego to use for withdrawal (optional)
- `_withdrawVaultToken`: The address of the vault token to withdraw from (optional)

**Returns:**
- The amount of WETH converted
- The amount of ETH received

**Events Emitted:**
- `UserWalletWethConvertedToEth`
- `UserWalletWithdrawal` (if withdrawing)

**Requirements:**
- Caller must have permission to convert
- Sufficient balance of WETH
- Valid lego ID and vault token address if withdrawing
- Recipient must be allowed if specified

### recoverTrialFunds

```vyper
@nonreentrant
@external
def recoverTrialFunds(_opportunities: DynArray[TrialFundsOpp, MAX_LEGOS]) -> bool:
```

Recovers trial funds from the wallet.

**Parameters:**
- `_opportunities`: Array of trial funds opportunities

**Returns:**
- True if the trial funds were recovered successfully

**Events Emitted:**
- `UserWalletTrialFundsRecovered`

**Requirements:**
- Caller must be the wallet config
- Valid trial funds asset
- Opportunities array must not be empty

### recoverNft

```vyper
@nonreentrant
@external
def recoverNft(_collection: address, _nftTokenId: uint256) -> bool:
```

Recovers an NFT from the wallet.

**Parameters:**
- `_collection`: The address of the NFT collection
- `_nftTokenId`: The token ID of the NFT

**Returns:**
- True if the NFT was recovered successfully

**Events Emitted:**
- `UserWalletNftRecovered`

**Requirements:**
- Caller must be the owner
- Valid NFT collection address
- Wallet must own the NFT 