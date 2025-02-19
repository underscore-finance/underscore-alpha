# @version 0.4.0
# pragma optimize codesize

from ethereum.ercs import IERC20
from interfaces import LegoDex
from interfaces import LegoYield

interface WalletConfig:
    def aggregateBatchTxCostData(_aggProtocolCost: TxCostInfo, _aggAgentCost: TxCostInfo, _agent: address, _action: ActionType, _usdValue: uint256, _priceSheets: address, _oracleRegistry: address) -> (TxCostInfo, TxCostInfo): view
    def handleSubscriptionsAndPermissions(_agent: address, _action: ActionType, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS], _cd: CoreData) -> (SubPaymentInfo, SubPaymentInfo): nonpayable
    def canAgentAccess(_agent: address, _action: ActionType, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS]) -> bool: view
    def getAvailableTxAmount(_asset: address, _wantedAmount: uint256, _shouldCheckTrialFunds: bool, _cd: CoreData = empty(CoreData)) -> uint256: view
    def getTransactionCosts(_agent: address, _action: ActionType, _usdValue: uint256, _cd: CoreData) -> (TxCostInfo, TxCostInfo): view
    def isRecipientAllowed(_recipient: address) -> bool: view
    def isAgentActive(_agent: address) -> bool: view
    def owner() -> address: view

interface LegoRegistry:
    def getUnderlyingForUser(_user: address, _asset: address) -> uint256: view
    def getUnderlyingAsset(_vaultToken: address) -> address: view
    def getLegoAddr(_legoId: uint256) -> address: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view
    def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface WethContract:
    def withdraw(_amount: uint256): nonpayable
    def deposit(): payable

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP
    CONVERSION

struct CoreData:
    owner: address
    wallet: address
    walletConfig: address
    legoRegistry: address
    priceSheets: address
    oracleRegistry: address
    trialFundsAsset: address
    trialFundsInitialAmount: uint256

struct SubPaymentInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    didChange: bool

struct TxCostInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256

struct Signature:
    signature: Bytes[65]
    signer: address
    expiration: uint256

struct TrialFundsOpp:
    legoId: uint256
    vaultToken: address

struct ActionInstruction:
    action: ActionType
    legoId: uint256
    asset: address
    vault: address
    amount: uint256
    recipient: address
    altLegoId: uint256
    altVault: address
    altAsset: address
    altAmount: uint256
    pool: address

event AgenticDeposit:
    signer: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    refundAssetAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    broadcaster: address
    isSignerAgent: bool

event AgenticWithdrawal:
    signer: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    refundVaultTokenAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    broadcaster: address
    isSignerAgent: bool

event AgenticSwap:
    signer: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    swapAmount: uint256
    toAmount: uint256
    pool: address
    refundAssetAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    broadcaster: address
    isSignerAgent: bool

event WalletFundsTransferred:
    signer: indexed(address)
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    broadcaster: address
    isSignerAgent: bool

event EthConvertedToWeth:
    signer: indexed(address)
    amount: uint256
    paidEth: uint256
    weth: indexed(address)
    broadcaster: indexed(address)
    isSignerAgent: bool

event WethConvertedToEth:
    signer: indexed(address)
    amount: uint256
    weth: indexed(address)
    broadcaster: indexed(address)
    isSignerAgent: bool

event SubscriptionPaid:
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    isAgent: bool

event TransactionFeePaid:
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    action: ActionType
    isAgent: bool

event TrialFundsRecovered:
    asset: indexed(address)
    amountRecovered: uint256
    remainingAmount: uint256

# core
walletConfig: public(address)

# trial funds info
trialFundsAsset: public(address)
trialFundsInitialAmount: public(uint256)

# config
addyRegistry: public(address)
wethAddr: public(address)
initialized: public(bool)

API_VERSION: constant(String[28]) = "0.0.1"
MAX_ASSETS: constant(uint256) = 25
MAX_LEGOS: constant(uint256) = 20
MAX_INSTRUCTIONS: constant(uint256) = 20

# registry ids
AGENT_FACTORY_ID: constant(uint256) = 1
LEGO_REGISTRY_ID: constant(uint256) = 2
PRICE_SHEETS_ID: constant(uint256) = 3
ORACLE_REGISTRY_ID: constant(uint256) = 4

# eip-712
usedSignatures: public(HashMap[Bytes[65], bool])
ECRECOVER_PRECOMPILE: constant(address) = 0x0000000000000000000000000000000000000001
DOMAIN_TYPE_HASH: constant(bytes32) = keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)')
DEPOSIT_TYPE_HASH: constant(bytes32) = keccak256('Deposit(uint256 legoId,address asset,address vault,uint256 amount,uint256 expiration)')
WITHDRAWAL_TYPE_HASH: constant(bytes32) = keccak256('Withdrawal(uint256 legoId,address asset,address vaultToken,uint256 vaultTokenAmount,uint256 expiration)')
REBALANCE_TYPE_HASH: constant(bytes32) = keccak256('Rebalance(uint256 fromLegoId,address fromAsset,address fromVaultToken,uint256 toLegoId,address toVault,uint256 fromVaultTokenAmount,uint256 expiration)')
SWAP_TYPE_HASH: constant(bytes32) = keccak256('Swap(uint256 legoId,address tokenIn,address tokenOut,uint256 amountIn,uint256 minAmountOut,address pool,uint256 expiration)')
TRANSFER_TYPE_HASH: constant(bytes32) = keccak256('Transfer(address recipient,uint256 amount,address asset,uint256 expiration)')
ETH_TO_WETH_TYPE_HASH: constant(bytes32) = keccak256('EthToWeth(uint256 amount,uint256 depositLegoId,address depositVault,uint256 expiration)')
WETH_TO_ETH_TYPE_HASH: constant(bytes32) = keccak256('WethToEth(uint256 amount,address recipient,uint256 withdrawLegoId,address withdrawVaultToken,uint256 expiration)')


@deploy
def __init__():
    # make sure original reference contract can't be initialized
    self.initialized = True


@payable
@external
def __default__():
    pass


@external
def initialize(
    _walletConfig: address,
    _addyRegistry: address,
    _wethAddr: address,
    _trialFundsAsset: address,
    _trialFundsInitialAmount: uint256,
) -> bool:
    """
    @notice Sets up the initial state of the wallet template
    @dev Can only be called once and sets core contract parameters
    @param _walletConfig The address of the wallet config contract
    @param _addyRegistry The address of the core registry contract
    @param _wethAddr The address of the WETH contract
    @param _trialFundsAsset The address of the gift asset
    @param _trialFundsInitialAmount The amount of the gift asset
    @return bool True if initialization was successful
    """
    assert not self.initialized # dev: can only initialize once
    self.initialized = True

    assert empty(address) not in [_walletConfig, _addyRegistry, _wethAddr] # dev: invalid addrs
    self.walletConfig = _walletConfig
    self.addyRegistry = _addyRegistry
    self.wethAddr = _wethAddr

    # trial funds info
    if _trialFundsAsset != empty(address) and _trialFundsInitialAmount != 0:   
        self.trialFundsAsset = _trialFundsAsset
        self.trialFundsInitialAmount = _trialFundsInitialAmount

    return True


@pure
@external
def apiVersion() -> String[28]:
    """
    @notice Returns the current API version of the contract
    @dev Returns a constant string representing the contract version
    @return String[28] The API version string
    """
    return API_VERSION


###########
# Deposit #
###########


@nonreentrant
@external
def depositTokens(
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256, uint256):
    """
    @notice Deposits tokens into a specified lego integration and vault
    @param _legoId The ID of the lego to use for deposit
    @param _asset The address of the token to deposit
    @param _vault The target vault address
    @param _amount The amount to deposit (defaults to max)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets deposited
    @return address The vault token address
    @return uint256 The amount of vault tokens received
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()

    # check permissions / subscription data
    signer: address = self._getSignerOnDeposit(_legoId, _asset, _vault, _amount, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.DEPOSIT, [_asset], [_legoId], cd)

    # deposit tokens
    assetAmountDeposited: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    usdValue: uint256 = 0
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue = self._depositTokens(signer, _legoId, _asset, _vault, _amount, isSignerAgent, cd)

    self._handleTransactionFees(signer, isSignerAgent, ActionType.DEPOSIT, usdValue, cd)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue


@nonreentrant
@external
def depositTokensWithTransfer(
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256 = max_value(uint256),
) -> (uint256, address, uint256, uint256):
    """
    @notice Transfers tokens from sender and deposits them into a specified lego integration and vault
    @param _legoId The ID of the lego to use for deposit
    @param _asset The address of the token to deposit
    @param _vault The target vault address
    @param _amount The amount to deposit (defaults to max)
    @return uint256 The amount of assets deposited
    @return address The vault token address
    @return uint256 The amount of vault tokens received
    @return uint256 The usd value of the transaction
    """
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, amount, default_return_value=True) # dev: transfer failed
    cd: CoreData = self._getCoreData()
    return self._depositTokens(msg.sender, _legoId, _asset, _vault, amount, staticcall WalletConfig(cd.walletConfig).isAgentActive(msg.sender), cd)


@internal
def _depositTokens(
    _signer: address,
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256,
    _isSignerAgent: bool,
    _cd: CoreData,
) -> (uint256, address, uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(_cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize amount
    amount: uint256 = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(_asset, _amount, False, _cd)
    assert extcall IERC20(_asset).approve(legoAddr, amount, default_return_value=True) # dev: approval failed

    # deposit into lego partner
    assetAmountDeposited: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    refundAssetAmount: uint256 = 0
    usdValue: uint256 = 0
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, refundAssetAmount, usdValue = extcall LegoYield(legoAddr).depositTokens(_asset, amount, _vault, self)
    assert extcall IERC20(_asset).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticDeposit(_signer, _asset, vaultToken, assetAmountDeposited, vaultTokenAmountReceived, refundAssetAmount, usdValue, _legoId, legoAddr, msg.sender, _isSignerAgent)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue


@internal
def _getSignerOnDeposit(
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(DEPOSIT_TYPE_HASH, _legoId, _asset, _vault, _amount, _sig.expiration), _sig)

    return _sig.signer


############
# Withdraw #
############


@nonreentrant
@external
def withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256):
    """
    @notice Withdraws tokens from a specified lego integration and vault
    @param _legoId The ID of the lego to use for withdrawal
    @param _asset The address of the token to withdraw
    @param _vaultToken The vault token address
    @param _vaultTokenAmount The amount of vault tokens to withdraw (defaults to max)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets received
    @return uint256 The amount of vault tokens burned
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()

    # check permissions / subscription data
    signer: address = self._getSignerOnWithdrawal(_legoId, _asset, _vaultToken, _vaultTokenAmount, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.WITHDRAWAL, [_asset], [_legoId], cd)

    # withdraw from lego partner
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    usdValue: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned, usdValue = self._withdrawTokens(signer, _legoId, _asset, _vaultToken, _vaultTokenAmount, isSignerAgent, cd)

    self._handleTransactionFees(signer, isSignerAgent, ActionType.WITHDRAWAL, usdValue, cd)
    return assetAmountReceived, vaultTokenAmountBurned, usdValue


@internal
def _withdrawTokens(
    _signer: address,
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256,
    _isSignerAgent: bool,
    _cd: CoreData,
) -> (uint256, uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(_cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize amount, this will look at vault token balance (not always 1:1 with underlying asset)
    withdrawAmount: uint256 = _vaultTokenAmount
    if _vaultToken != empty(address):
        withdrawAmount = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(_vaultToken, _vaultTokenAmount, False, _cd)

        # some vault tokens require max value approval (comp v3)
        assert extcall IERC20(_vaultToken).approve(legoAddr, max_value(uint256), default_return_value=True) # dev: approval failed

    assert withdrawAmount != 0 # dev: nothing to withdraw

    # withdraw from lego partner
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    refundVaultTokenAmount: uint256 = 0
    usdValue: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount, usdValue = extcall LegoYield(legoAddr).withdrawTokens(_asset, withdrawAmount, _vaultToken, self)

    # zero out approvals
    if _vaultToken != empty(address):
        assert extcall IERC20(_vaultToken).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticWithdrawal(_signer, _asset, _vaultToken, assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount, usdValue, _legoId, legoAddr, msg.sender, _isSignerAgent)
    return assetAmountReceived, vaultTokenAmountBurned, usdValue


@internal
def _getSignerOnWithdrawal(
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(WITHDRAWAL_TYPE_HASH, _legoId, _asset, _vaultToken, _vaultTokenAmount, _sig.expiration), _sig)

    return _sig.signer


#############
# Rebalance #
#############


@nonreentrant
@external
def rebalance(
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVault: address,
    _fromVaultTokenAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256, uint256):
    """
    @notice Withdraws tokens from one lego and deposits them into another (always same asset)
    @param _fromLegoId The ID of the source lego
    @param _fromAsset The address of the token to rebalance
    @param _fromVaultToken The source vault token address
    @param _toLegoId The ID of the destination lego
    @param _toVault The destination vault address
    @param _fromVaultTokenAmount The vault token amount to rebalance (defaults to max)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets deposited in the destination vault
    @return address The destination vault token address
    @return uint256 The amount of destination vault tokens received
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()

    # check permissions / subscription data
    signer: address = self._getSignerOnRebalance(_fromLegoId, _fromAsset, _fromVaultToken, _toLegoId, _toVault, _fromVaultTokenAmount, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.REBALANCE, [_fromAsset], [_fromLegoId, _toLegoId], cd)

    # rebalance
    assetAmountDeposited: uint256 = 0
    newVaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    usdValue: uint256 = 0
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue = self._rebalance(signer, _fromLegoId, _fromAsset, _fromVaultToken, _toLegoId, _toVault, _fromVaultTokenAmount, isSignerAgent, cd)

    self._handleTransactionFees(signer, isSignerAgent, ActionType.REBALANCE, usdValue, cd)
    return assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue


@internal
def _rebalance(
    _signer: address,
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVault: address,
    _fromVaultTokenAmount: uint256,
    _isSignerAgent: bool,
    _cd: CoreData,
) -> (uint256, address, uint256, uint256):

    # withdraw from the first lego
    assetAmountReceived: uint256 = 0
    na: uint256 = 0
    withdrawUsdValue: uint256 = 0
    assetAmountReceived, na, withdrawUsdValue = self._withdrawTokens(_signer, _fromLegoId, _fromAsset, _fromVaultToken, _fromVaultTokenAmount, _isSignerAgent, _cd)

    # deposit the received assets into the second lego
    assetAmountDeposited: uint256 = 0
    newVaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    depositUsdValue: uint256 = 0
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, depositUsdValue = self._depositTokens(_signer, _toLegoId, _fromAsset, _toVault, assetAmountReceived, _isSignerAgent, _cd)

    return assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, max(withdrawUsdValue, depositUsdValue)


@internal
def _getSignerOnRebalance(
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVault: address,
    _fromVaultTokenAmount: uint256,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(REBALANCE_TYPE_HASH, _fromLegoId, _fromAsset, _fromVaultToken, _toLegoId, _toVault, _fromVaultTokenAmount, _sig.expiration), _sig)

    return _sig.signer


########
# Swap #
########


@nonreentrant
@external
def swapTokens(
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256 = max_value(uint256),
    _minAmountOut: uint256 = 0,
    _pool: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256):
    """
    @notice Swaps tokens using a specified lego integration
    @dev Validates agent permissions if caller is not the owner
    @param _legoId The ID of the lego to use for swapping
    @param _tokenIn The address of the token to swap from
    @param _tokenOut The address of the token to swap to
    @param _amountIn The amount of input tokens to swap (defaults to max balance)
    @param _minAmountOut The minimum amount of output tokens to receive (defaults to 0)
    @param _pool The pool address to use for swapping (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The actual amount of input tokens swapped
    @return uint256 The amount of output tokens received
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()

    # check permissions / subscription data
    signer: address = self._getSignerOnSwap(_legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _pool, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.SWAP, [_tokenIn, _tokenOut], [_legoId], cd)

    # swap
    actualSwapAmount: uint256 = 0
    toAmount: uint256 = 0
    usdValue: uint256 = 0
    actualSwapAmount, toAmount, usdValue = self._swapTokens(signer, _legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _pool, isSignerAgent, cd)

    self._handleTransactionFees(signer, isSignerAgent, ActionType.SWAP, usdValue, cd)
    return actualSwapAmount, toAmount, usdValue


@internal
def _swapTokens(
    _signer: address,
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _pool: address,
    _isSignerAgent: bool,
    _cd: CoreData,
) -> (uint256, uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(_cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego
    assert empty(address) not in [_tokenIn, _tokenOut] # dev: invalid tokens

    # finalize amount
    swapAmount: uint256 = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(_tokenIn, _amountIn, True, _cd)
    assert extcall IERC20(_tokenIn).approve(legoAddr, swapAmount, default_return_value=True) # dev: approval failed

    # check if vault token of trial funds asset
    isTrialFundsVaultToken: bool = self._isTrialFundsVaultToken(_tokenIn, _cd.trialFundsAsset, _cd.legoRegistry)
    
    # swap assets via lego partner
    toAmount: uint256 = 0
    refundAssetAmount: uint256 = 0
    usdValue: uint256 = 0
    swapAmount, toAmount, refundAssetAmount, usdValue = extcall LegoDex(legoAddr).swapTokens(_tokenIn, _tokenOut, swapAmount, _minAmountOut, _pool, self)
    assert extcall IERC20(_tokenIn).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    # make sure they still have enough trial funds
    self._checkTrialFundsPostTx(isTrialFundsVaultToken, _cd.trialFundsAsset, _cd.trialFundsInitialAmount, _cd.legoRegistry)
    
    log AgenticSwap(_signer, _tokenIn, _tokenOut, swapAmount, toAmount, _pool, refundAssetAmount, usdValue, _legoId, legoAddr, msg.sender, _isSignerAgent)
    return swapAmount, toAmount, usdValue


@internal
def _getSignerOnSwap(
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _pool: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(SWAP_TYPE_HASH, _legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _pool, _sig.expiration), _sig)

    return _sig.signer


##################
# Transfer Funds #
##################


@nonreentrant
@external
def transferFunds(
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256):
    """
    @notice Transfers funds to a specified recipient
    @dev Handles both ETH and token transfers with optional amount specification
    @param _recipient The address to receive the funds
    @param _amount The amount to transfer (defaults to max)
    @param _asset The token address (empty for ETH)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of funds transferred
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()

    # check permissions / subscription data
    signer: address = self._getSignerOnTransfer(_recipient, _amount, _asset, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.TRANSFER, [_asset], [], cd)

    # transfer funds
    amount: uint256 = 0
    usdValue: uint256 = 0
    amount, usdValue = self._transferFunds(signer, _recipient, _amount, _asset, isSignerAgent, cd)

    self._handleTransactionFees(signer, isSignerAgent, ActionType.TRANSFER, usdValue, cd)
    return amount, usdValue


@internal
def _transferFunds(
    _signer: address,
    _recipient: address,
    _amount: uint256,
    _asset: address,
    _isSignerAgent: bool,
    _cd: CoreData,
) -> (uint256, uint256):
    amount: uint256 = 0
    usdValue: uint256 = 0

    # validate recipient
    if _recipient != _cd.owner:
        assert staticcall WalletConfig(_cd.walletConfig).isRecipientAllowed(_recipient) # dev: recipient not allowed

    # handle eth
    if _asset == empty(address):
        amount = min(_amount, self.balance)
        assert amount != 0 # dev: nothing to transfer
        send(_recipient, amount)
        usdValue = staticcall OracleRegistry(_cd.oracleRegistry).getEthUsdValue(amount)

    # erc20 tokens
    else:

        # check if vault token of trial funds asset
        isTrialFundsVaultToken: bool = self._isTrialFundsVaultToken(_asset, _cd.trialFundsAsset, _cd.legoRegistry)

        # perform transfer
        amount = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(_asset, _amount, True, _cd)
        assert extcall IERC20(_asset).transfer(_recipient, amount, default_return_value=True) # dev: transfer failed
        usdValue = staticcall OracleRegistry(_cd.oracleRegistry).getUsdValue(_asset, amount)

        # make sure they still have enough trial funds
        self._checkTrialFundsPostTx(isTrialFundsVaultToken, _cd.trialFundsAsset, _cd.trialFundsInitialAmount, _cd.legoRegistry)

    log WalletFundsTransferred(_signer, _recipient, _asset, amount, usdValue, msg.sender, _isSignerAgent)
    return amount, usdValue


@internal
def _getSignerOnTransfer(
    _recipient: address,
    _amount: uint256,
    _asset: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(TRANSFER_TYPE_HASH, _recipient, _amount, _asset, _sig.expiration), _sig)

    return _sig.signer


################
# Wrapped ETH #
################


# eth -> weth


@nonreentrant
@payable
@external
def convertEthToWeth(
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
    """
    @notice Converts ETH to WETH and optionally deposits into a lego integration and vault
    @param _amount The amount of ETH to convert (defaults to max)
    @param _depositLegoId The lego ID to use for deposit (optional)
    @param _depositVault The vault address for deposit (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets deposited (if deposit performed)
    @return address The vault token address (if deposit performed)
    @return uint256 The amount of vault tokens received (if deposit performed)
    """
    cd: CoreData = self._getCoreData()
    weth: address = self.wethAddr

    # check permissions / subscription data
    signer: address = self._getSignerOnEthToWeth(_amount, _depositLegoId, _depositVault, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.CONVERSION, [weth], [_depositLegoId], cd)

    # convert eth to weth
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).deposit(value=amount)
    log EthConvertedToWeth(signer, amount, msg.value, weth, msg.sender, isSignerAgent)

    # deposit weth into lego partner
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    if _depositLegoId != 0:
        depositUsdValue: uint256 = 0
        amount, vaultToken, vaultTokenAmountReceived, depositUsdValue = self._depositTokens(signer, _depositLegoId, weth, _depositVault, amount, isSignerAgent, cd)
        self._handleTransactionFees(signer, isSignerAgent, ActionType.DEPOSIT, depositUsdValue, cd)

    return amount, vaultToken, vaultTokenAmountReceived


@internal
def _getSignerOnEthToWeth(
    _amount: uint256,
    _depositLegoId: uint256,
    _depositVault: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(ETH_TO_WETH_TYPE_HASH, _amount, _depositLegoId, _depositVault, _sig.expiration), _sig)

    return _sig.signer


# weth -> eth


@nonreentrant
@external
def convertWethToEth(
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
    _sig: Signature = empty(Signature),
) -> uint256:
    """
    @notice Converts WETH to ETH and optionally withdraws from a vault first
    @param _amount The amount of WETH to convert (defaults to max)
    @param _recipient The address to receive the ETH (optional)
    @param _withdrawLegoId The lego ID to withdraw from (optional)
    @param _withdrawVaultToken The vault token to withdraw (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of ETH received
    """
    cd: CoreData = self._getCoreData()
    weth: address = self.wethAddr

    # check permissions / subscription data
    signer: address = self._getSignerOnWethToEth(_amount, _recipient, _withdrawLegoId, _withdrawVaultToken, _sig)
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, ActionType.CONVERSION, [weth], [_withdrawLegoId], cd)

    # withdraw weth from lego partner (if applicable)
    amount: uint256 = _amount
    usdValue: uint256 = 0
    if _withdrawLegoId != 0:
        _na: uint256 = 0
        amount, _na, usdValue = self._withdrawTokens(signer, _withdrawLegoId, weth, _withdrawVaultToken, _amount, isSignerAgent, cd)
        self._handleTransactionFees(signer, isSignerAgent, ActionType.WITHDRAWAL, usdValue, cd)

    # convert weth to eth
    amount = min(amount, staticcall IERC20(weth).balanceOf(self))
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).withdraw(amount)
    log WethConvertedToEth(signer, amount, weth, msg.sender, isSignerAgent)

    # transfer eth to recipient (if applicable)
    if _recipient != empty(address):
        amount, usdValue = self._transferFunds(signer, _recipient, amount, empty(address), isSignerAgent, cd)
        self._handleTransactionFees(signer, isSignerAgent, ActionType.TRANSFER, usdValue, cd)

    return amount


@internal
def _getSignerOnWethToEth(
    _amount: uint256,
    _recipient: address,
    _withdrawLegoId: uint256,
    _withdrawVaultToken: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(WETH_TO_ETH_TYPE_HASH, _amount, _recipient, _withdrawLegoId, _withdrawVaultToken, _sig.expiration), _sig)

    return _sig.signer


#################
# Batch Actions #
#################


@nonreentrant
@external
def performManyActions(_instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS]) -> bool:
    """
    @notice Performs multiple actions in a single transaction
    @dev Executes a batch of instructions with proper permission checks
    @param _instructions Array of action instructions to execute
    @return bool True if all actions were executed successfully
    """
    assert len(_instructions) != 0 # dev: no instructions
    cd: CoreData = self._getCoreData()

    signer: address = msg.sender
    # TODO: allow broadcaster to be different from signer

    # pass in empty action, lego ids, and assets here
    isSignerAgent: bool = self._checkPermsAndHandleSubs(signer, empty(ActionType), [], [], cd)

    aggProtocolCost: TxCostInfo = empty(TxCostInfo)
    aggAgentCost: TxCostInfo = empty(TxCostInfo)

    # init vars
    usdValue: uint256 = 0
    naValueA: uint256 = 0
    naAddyA: address = empty(address)
    naValueB: uint256 = 0

    # iterate through instructions
    for i: uint256 in range(len(_instructions), bound=MAX_INSTRUCTIONS):
        instruction: ActionInstruction = _instructions[i]

        # deposit
        if instruction.action == ActionType.DEPOSIT:
            if isSignerAgent:
                assert staticcall WalletConfig(cd.walletConfig).canAgentAccess(signer, ActionType.DEPOSIT, [instruction.asset], [instruction.legoId]) # dev: agent not allowed
            naValueA, naAddyA, naValueB, usdValue = self._depositTokens(signer, instruction.legoId, instruction.asset, instruction.vault, instruction.amount, isSignerAgent, cd)
            if isSignerAgent and usdValue != 0:
                aggProtocolCost, aggAgentCost = staticcall WalletConfig(cd.walletConfig).aggregateBatchTxCostData(aggProtocolCost, aggAgentCost, signer, ActionType.DEPOSIT, usdValue, cd.priceSheets, cd.oracleRegistry)

        # withdraw
        elif instruction.action == ActionType.WITHDRAWAL:
            if isSignerAgent:
                assert staticcall WalletConfig(cd.walletConfig).canAgentAccess(signer, ActionType.WITHDRAWAL, [instruction.asset], [instruction.legoId]) # dev: agent not allowed
            naValueA, naValueB, usdValue = self._withdrawTokens(signer, instruction.legoId, instruction.asset, instruction.vault, instruction.amount, isSignerAgent, cd)
            if isSignerAgent and usdValue != 0:
                aggProtocolCost, aggAgentCost = staticcall WalletConfig(cd.walletConfig).aggregateBatchTxCostData(aggProtocolCost, aggAgentCost, signer, ActionType.WITHDRAWAL, usdValue, cd.priceSheets, cd.oracleRegistry)

        # rebalance
        elif instruction.action == ActionType.REBALANCE:
            if isSignerAgent:
                assert staticcall WalletConfig(cd.walletConfig).canAgentAccess(signer, ActionType.REBALANCE, [instruction.asset], [instruction.legoId, instruction.altLegoId]) # dev: agent not allowed
            naValueA, naAddyA, naValueB, usdValue = self._rebalance(signer, instruction.legoId, instruction.asset, instruction.vault, instruction.altLegoId, instruction.altVault, instruction.amount, isSignerAgent, cd)
            if isSignerAgent and usdValue != 0:
                aggProtocolCost, aggAgentCost = staticcall WalletConfig(cd.walletConfig).aggregateBatchTxCostData(aggProtocolCost, aggAgentCost, signer, ActionType.REBALANCE, usdValue, cd.priceSheets, cd.oracleRegistry)

        # swap
        elif instruction.action == ActionType.SWAP:
            if isSignerAgent:
                assert staticcall WalletConfig(cd.walletConfig).canAgentAccess(signer, ActionType.SWAP, [instruction.asset, instruction.altAsset], [instruction.legoId]) # dev: agent not allowed
            naValueA, naValueB, usdValue = self._swapTokens(signer, instruction.legoId, instruction.asset, instruction.altAsset, instruction.amount, instruction.altAmount, instruction.pool, isSignerAgent, cd)
            if isSignerAgent and usdValue != 0:
                aggProtocolCost, aggAgentCost = staticcall WalletConfig(cd.walletConfig).aggregateBatchTxCostData(aggProtocolCost, aggAgentCost, signer, ActionType.SWAP, usdValue, cd.priceSheets, cd.oracleRegistry)

        # transfer
        elif instruction.action == ActionType.TRANSFER:
            if isSignerAgent:
                assert staticcall WalletConfig(cd.walletConfig).canAgentAccess(signer, ActionType.TRANSFER, [instruction.asset], [instruction.legoId]) # dev: agent not allowed
            naValueA, usdValue = self._transferFunds(signer, instruction.recipient, instruction.amount, instruction.asset, isSignerAgent, cd)
            if isSignerAgent and usdValue != 0:
                aggProtocolCost, aggAgentCost = staticcall WalletConfig(cd.walletConfig).aggregateBatchTxCostData(aggProtocolCost, aggAgentCost, signer, ActionType.TRANSFER, usdValue, cd.priceSheets, cd.oracleRegistry)

    # pay tx fees
    self._payTransactionFees(aggProtocolCost, aggAgentCost, empty(ActionType))

    return True


#############
# Utilities #
#############


@view
@internal
def _getCoreData() -> CoreData:
    addyRegistry: address = self.addyRegistry
    walletConfig: address = self.walletConfig
    return CoreData(
        owner=staticcall WalletConfig(walletConfig).owner(),
        wallet=self,
        walletConfig=walletConfig,
        legoRegistry=staticcall AddyRegistry(addyRegistry).getAddy(LEGO_REGISTRY_ID),
        priceSheets=staticcall AddyRegistry(addyRegistry).getAddy(PRICE_SHEETS_ID),
        oracleRegistry=staticcall AddyRegistry(addyRegistry).getAddy(ORACLE_REGISTRY_ID),
        trialFundsAsset=self.trialFundsAsset,
        trialFundsInitialAmount=self.trialFundsInitialAmount,
    )


# payments (subscriptions, transaction fees)


@internal
def _checkPermsAndHandleSubs(
    _signer: address,
    _action: ActionType,
    _assets: DynArray[address, MAX_ASSETS],
    _legoIds: DynArray[uint256, MAX_LEGOS],
    _cd: CoreData,
) -> bool:
    agent: address = _signer
    if _signer == _cd.owner:
        agent = empty(address)

    # handle subscriptions and permissions
    protocolSub: SubPaymentInfo = empty(SubPaymentInfo)
    agentSub: SubPaymentInfo = empty(SubPaymentInfo)
    protocolSub, agentSub = extcall WalletConfig(_cd.walletConfig).handleSubscriptionsAndPermissions(agent, _action, _assets, _legoIds, _cd)

    # handle protocol subscription payment
    if protocolSub.amount != 0:
        assert extcall IERC20(protocolSub.asset).transfer(protocolSub.recipient, protocolSub.amount, default_return_value=True) # dev: protocol subscription payment failed
        log SubscriptionPaid(protocolSub.recipient, protocolSub.asset, protocolSub.amount, protocolSub.usdValue, protocolSub.paidThroughBlock, False)

    # handle agent subscription payment
    if agentSub.amount != 0:
        assert extcall IERC20(agentSub.asset).transfer(agentSub.recipient, agentSub.amount, default_return_value=True) # dev: agent subscription payment failed
        log SubscriptionPaid(agent, agentSub.asset, agentSub.amount, agentSub.usdValue, agentSub.paidThroughBlock, True)

    return agent != empty(address)


@internal
def _handleTransactionFees(
    _agent: address,
    _isSignerAgent: bool,
    _action: ActionType,
    _usdValue: uint256,
    _cd: CoreData,
):
    if not _isSignerAgent or _usdValue == 0:
        return

    # get costs
    protocolCost: TxCostInfo = empty(TxCostInfo)
    agentCost: TxCostInfo = empty(TxCostInfo)
    protocolCost, agentCost = staticcall WalletConfig(_cd.walletConfig).getTransactionCosts(_agent, _action, _usdValue, _cd)

    # make payment
    self._payTransactionFees(protocolCost, agentCost, _action)


@internal
def _payTransactionFees(_protocolCost: TxCostInfo, _agentCost: TxCostInfo, _action: ActionType):
    
    # protocol tx fees
    if _protocolCost.amount != 0:
        assert extcall IERC20(_protocolCost.asset).transfer(_protocolCost.recipient, _protocolCost.amount, default_return_value=True) # dev: protocol tx fee payment failed
        log TransactionFeePaid(_protocolCost.recipient, _protocolCost.asset, _protocolCost.amount, _protocolCost.usdValue, _action, False)

    # agent tx fees
    if _agentCost.amount != 0:
        assert extcall IERC20(_agentCost.asset).transfer(_agentCost.recipient, _agentCost.amount, default_return_value=True) # dev: agent tx fee payment failed
        log TransactionFeePaid(_agentCost.recipient, _agentCost.asset, _agentCost.amount, _agentCost.usdValue, _action, True)


# trial funds


@view
@internal
def _isTrialFundsVaultToken(_asset: address, _trialFundsAsset: address, _legoRegistry: address) -> bool:
    if _trialFundsAsset == empty(address) or _asset == _trialFundsAsset:
        return False
    return _trialFundsAsset == staticcall LegoRegistry(_legoRegistry).getUnderlyingAsset(_asset)


@view
@internal
def _checkTrialFundsPostTx(_isTrialFundsVaultToken: bool, _trialFundsAsset: address, _trialFundsInitialAmount: uint256, _legoRegistry: address):
    if not _isTrialFundsVaultToken:
        return
    postUnderlying: uint256 = staticcall LegoRegistry(_legoRegistry).getUnderlyingForUser(self, _trialFundsAsset)
    assert postUnderlying >= _trialFundsInitialAmount # dev: cannot transfer trial funds vault token


@external
def recoverTrialFunds(_opportunities: DynArray[TrialFundsOpp, MAX_LEGOS] = []) -> bool:
    cd: CoreData = self._getCoreData()
    agentFactory: address = staticcall AddyRegistry(self.addyRegistry).getAddy(AGENT_FACTORY_ID)
    assert msg.sender == agentFactory # dev: no perms

    # validation
    assert cd.trialFundsAsset != empty(address) # dev: no trial funds asset
    assert cd.trialFundsInitialAmount != 0 # dev: no trial funds amount

    # iterate through clawback data
    balanceAvail: uint256 = staticcall IERC20(cd.trialFundsAsset).balanceOf(self)
    for i: uint256 in range(len(_opportunities), bound=MAX_LEGOS):
        if balanceAvail >= cd.trialFundsInitialAmount:
            break

        # get vault token data
        opp: TrialFundsOpp = _opportunities[i]
        vaultTokenBal: uint256 = staticcall IERC20(opp.vaultToken).balanceOf(self)
        if vaultTokenBal == 0:
            continue

        # withdraw from lego partner
        assetAmountReceived: uint256 = 0
        na1: uint256 = 0
        na2: uint256 = 0
        assetAmountReceived, na1, na2 = self._withdrawTokens(agentFactory, opp.legoId, cd.trialFundsAsset, opp.vaultToken, vaultTokenBal, False, cd)
        balanceAvail += assetAmountReceived

        # deposit any extra balance back lego
        if balanceAvail > cd.trialFundsInitialAmount:
            self._depositTokens(agentFactory, opp.legoId, cd.trialFundsAsset, opp.vaultToken, balanceAvail - cd.trialFundsInitialAmount, False, cd)
            break

    # transfer back to agent factory
    amountRecovered: uint256 = min(cd.trialFundsInitialAmount, staticcall IERC20(cd.trialFundsAsset).balanceOf(self))
    assert amountRecovered != 0 # dev: no funds to transfer
    assert extcall IERC20(cd.trialFundsAsset).transfer(agentFactory, amountRecovered, default_return_value=True) # dev: trial funds transfer failed

    # update trial funds data
    remainingTrialFunds: uint256 = cd.trialFundsInitialAmount - amountRecovered
    self.trialFundsInitialAmount = remainingTrialFunds
    if remainingTrialFunds == 0:
        self.trialFundsAsset = empty(address)

    log TrialFundsRecovered(cd.trialFundsAsset, amountRecovered, remainingTrialFunds)
    return True


# eip 712


@view
@external
def DOMAIN_SEPARATOR() -> bytes32:
    return self._domainSeparator()


@view
@internal
def _domainSeparator() -> bytes32:
    return keccak256(
        concat(
            DOMAIN_TYPE_HASH,
            keccak256('AgenticWallet'),
            keccak256(API_VERSION),
            abi_encode(chain.id, self)
        )
    )


@internal
def _isValidSignature(_encodedValue: Bytes[256], _sig: Signature):
    assert not self.usedSignatures[_sig.signature] # dev: signature already used
    assert _sig.expiration >= block.timestamp # dev: signature expired
    
    digest: bytes32 = keccak256(concat(b'\x19\x01', self._domainSeparator(), keccak256(_encodedValue)))

    # NOTE: signature is packed as r, s, v
    r: bytes32 = convert(slice(_sig.signature, 0, 32), bytes32)
    s: bytes32 = convert(slice(_sig.signature, 32, 32), bytes32)
    v: uint8 = convert(slice(_sig.signature, 64, 1), uint8)
    
    response: Bytes[32] = raw_call(
        ECRECOVER_PRECOMPILE,
        abi_encode(digest, v, r, s),
        max_outsize=32,
        is_static_call=True # This is a view function
    )
    
    assert len(response) == 32 # dev: invalid ecrecover response length
    assert abi_decode(response, address) == _sig.signer # dev: invalid signature
    self.usedSignatures[_sig.signature] = True
