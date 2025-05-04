# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1
# pragma optimize codesize

implements: UserWalletInterface
from interfaces import LegoDex
from interfaces import LegoYield
from interfaces import LegoCommon
from interfaces import LegoCredit
from interfaces import UserWalletInterface

from ethereum.ercs import IERC20
from ethereum.ercs import IERC721

interface WalletConfig:
    def finishMigrationIn(_whitelistToMigrate: DynArray[address, MAX_MIGRATION_WHITELIST], _assetsMigrated: DynArray[address, MAX_MIGRATION_ASSETS], _vaultTokensMigrated: DynArray[address, MAX_MIGRATION_ASSETS]) -> bool: nonpayable
    def handleSubscriptionsAndPermissions(_agent: address, _action: ActionType, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS], _cd: CoreData) -> (SubPaymentInfo, SubPaymentInfo): nonpayable
    def updateYieldTrackingOnWithdrawal(_vaultToken: address, _vaultTokenAmountBurned: uint256, _asset: address, _assetAmountReceived: uint256, _legoRegistry: address) -> uint256: nonpayable
    def updateYieldTrackingOnDeposit(_asset: address, _vaultToken: address, _vaultTokenAmountReceived: uint256, _assetAmountDeposited: uint256, _legoRegistry: address): nonpayable
    def getAvailableTxAmount(_asset: address, _wantedAmount: uint256, _shouldCheckTrialFunds: bool, _cd: CoreData = empty(CoreData)) -> uint256: view
    def updateYieldTrackingOnSwap(_tokenIn: address, _tokenOut: address, _tokenOutAmount: uint256, _legoRegistry: address): nonpayable
    def updateYieldTrackingOnEntry(_asset: address, _amount: uint256, _legoRegistry: address): nonpayable
    def updateYieldTrackingOnExit(_asset: address, _legoRegistry: address): nonpayable
    def canTransferToRecipient(_recipient: address) -> bool: view
    def isVaultToken(_asset: address) -> bool: view
    def canWalletBeAmbassador() -> bool: view
    def getProceedsAddr() -> address: view
    def myAmbassador() -> address: view
    def owner() -> address: view

interface LegoRegistry:
    def getVaultTokensForUser(_user: address, _asset: address) -> DynArray[VaultTokenInfo, MAX_VAULTS_FOR_USER]: view
    def getUnderlyingForUser(_user: address, _asset: address) -> uint256: view
    def getUnderlyingAsset(_vaultToken: address) -> address: view
    def getLegoAddr(_legoId: uint256) -> address: view

interface AgentFactory:
    def payAmbassadorYieldBonus(_ambassador: address, _asset: address, _amount: uint256) -> bool: nonpayable
    def agentBlacklist(_agentAddr: address) -> bool: view
    def isUserWallet(_wallet: address) -> bool: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view
    def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface WethContract:
    def withdraw(_amount: uint256): nonpayable
    def deposit(): payable

interface PriceSheets:
    def getTransactionFeeDataWithAmbassadorRatio(_user: address, _action: ActionType) -> (uint256, address, uint256): view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

interface UserWallet:
    def walletConfig() -> address: view

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

struct SubPaymentInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    didChange: bool

struct SwapInstruction:
    legoId: uint256
    amountIn: uint256
    minAmountOut: uint256
    tokenPath: DynArray[address, MAX_TOKEN_PATH]
    poolPath: DynArray[address, MAX_TOKEN_PATH - 1]

struct VaultTokenInfo:
    legoId: uint256
    vaultToken: address

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

event UserWalletBorrow:
    signer: indexed(address)
    borrowAsset: indexed(address)
    borrowAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address
    isSignerAgent: bool

event UserWalletRepayDebt:
    signer: indexed(address)
    paymentAsset: indexed(address)
    paymentAmount: uint256
    usdValue: uint256
    remainingDebt: uint256
    legoId: uint256
    legoAddr: indexed(address)
    isSignerAgent: bool

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

event UserWalletFundsTransferred:
    signer: indexed(address)
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    isSignerAgent: bool

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

event UserWalletEthConvertedToWeth:
    signer: indexed(address)
    amount: uint256
    paidEth: uint256
    weth: indexed(address)
    isSignerAgent: bool

event UserWalletWethConvertedToEth:
    signer: indexed(address)
    amount: uint256
    weth: indexed(address)
    isSignerAgent: bool

event UserWalletSubscriptionPaid:
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    isAgent: bool

event UserWalletTransactionFeePaid:
    asset: indexed(address)
    protocolRecipient: indexed(address)
    protocolAmount: uint256
    ambassadorRecipient: indexed(address)
    ambassadorAmount: uint256
    fee: uint256
    action: ActionType

event UserWalletTrialFundsRecovered:
    asset: indexed(address)
    amountRecovered: uint256
    remainingAmount: uint256

event UserWalletNftRecovered:
    collection: indexed(address)
    nftTokenId: uint256
    owner: indexed(address)

# core 
walletConfig: public(address)

# trial funds info
trialFundsAsset: public(address)
trialFundsInitialAmount: public(uint256)

# config
wethAddr: public(address)

# registry ids
AGENT_FACTORY_ID: constant(uint256) = 1
LEGO_REGISTRY_ID: constant(uint256) = 2
PRICE_SHEETS_ID: constant(uint256) = 3
ORACLE_REGISTRY_ID: constant(uint256) = 4

MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_TOKEN_PATH: constant(uint256) = 5
MAX_ASSETS: constant(uint256) = 25
MAX_LEGOS: constant(uint256) = 20
MAX_VAULTS_FOR_USER: constant(uint256) = 30
MAX_MIGRATION_ASSETS: constant(uint256) = 40
MAX_MIGRATION_WHITELIST: constant(uint256) = 20
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%

ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UnderscoreErc721"
API_VERSION: constant(String[28]) = "0.0.3"

ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(
    _walletConfig: address,
    _addyRegistry: address,
    _wethAddr: address,
    _trialFundsAsset: address,
    _trialFundsInitialAmount: uint256,
):
    """
    @notice Initializes a new UserWallet contract with required configuration parameters
    @dev Sets up the wallet with its configuration, registry addresses, and optional trial funds
    @param _walletConfig Address of the wallet configuration contract that manages permissions and settings
    @param _addyRegistry Address of the registry contract that stores core protocol addresses
    @param _wethAddr Address of the WETH contract for ETH wrapping/unwrapping functionality
    @param _trialFundsAsset Address of the asset used for trial funds (can be empty)
    @param _trialFundsInitialAmount Initial amount of trial funds to be held (can be 0)
    """
    assert empty(address) not in [_walletConfig, _addyRegistry, _wethAddr] # dev: invalid addrs
    self.walletConfig = _walletConfig
    self.wethAddr = _wethAddr
    ADDY_REGISTRY = _addyRegistry

    # trial funds info
    if _trialFundsAsset != empty(address) and _trialFundsInitialAmount != 0:   
        self.trialFundsAsset = _trialFundsAsset
        self.trialFundsInitialAmount = _trialFundsInitialAmount


@payable
@external
def __default__():
    pass


@view
@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    # must implement method for safe NFT transfers
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)


@pure
@external
def apiVersion() -> String[28]:
    """
    @notice Returns the current API version of the contract
    @dev Returns a constant string representing the contract version
    @return String[28] The API version string
    """
    return API_VERSION


@view
@external
def canBeAmbassador() -> bool:
    """
    @notice Checks if the current wallet can be an ambassador
    @dev Returns True if the wallet is a valid ambassador, False otherwise
    @return bool True if the wallet can be an ambassador, False otherwise
    """
    return staticcall WalletConfig(self.walletConfig).canWalletBeAmbassador()


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
) -> (uint256, address, uint256, uint256):
    """
    @notice Deposits tokens into a specified lego integration and vault
    @param _legoId The ID of the lego to use for deposit
    @param _asset The address of the token to deposit
    @param _vault The target vault address
    @param _amount The amount to deposit (defaults to max)
    @return uint256 The amount of assets deposited
    @return address The vault token address
    @return uint256 The amount of vault tokens received
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.DEPOSIT, [_asset], [_legoId], cd)
    return self._depositTokens(msg.sender, _legoId, _asset, _vault, _amount, isSignerAgent, cd)


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

    # update yield tracking
    extcall WalletConfig(_cd.walletConfig).updateYieldTrackingOnDeposit(_asset, vaultToken, vaultTokenAmountReceived, assetAmountDeposited, _cd.legoRegistry)

    log UserWalletDeposit(signer=_signer, asset=_asset, vaultToken=vaultToken, assetAmountDeposited=assetAmountDeposited, vaultTokenAmountReceived=vaultTokenAmountReceived, refundAssetAmount=refundAssetAmount, usdValue=usdValue, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=_isSignerAgent)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue


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
) -> (uint256, uint256, uint256):
    """
    @notice Withdraws tokens from a specified lego integration and vault
    @param _legoId The ID of the lego to use for withdrawal
    @param _asset The address of the token to withdraw
    @param _vaultToken The vault token address
    @param _vaultTokenAmount The amount of vault tokens to withdraw (defaults to max)
    @return uint256 The amount of assets received
    @return uint256 The amount of vault tokens burned
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.WITHDRAWAL, [_asset], [_legoId], cd)
    return self._withdrawTokens(msg.sender, _legoId, _asset, _vaultToken, _vaultTokenAmount, isSignerAgent, True, cd)


@internal
def _withdrawTokens(
    _signer: address,
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256,
    _isSignerAgent: bool,
    _shouldHandleFees: bool,
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

    # handle yield profit
    assetProfitAmount: uint256 = extcall WalletConfig(_cd.walletConfig).updateYieldTrackingOnWithdrawal(_vaultToken, vaultTokenAmountBurned, _asset, assetAmountReceived, _cd.legoRegistry)
    if _shouldHandleFees and assetProfitAmount != 0:
        sentProfit: uint256 = self._handleTransactionFees(ActionType.WITHDRAWAL, _asset, assetProfitAmount, _cd.priceSheets, _cd.agentFactory)
        assetAmountReceived -= sentProfit

    log UserWalletWithdrawal(signer=_signer, asset=_asset, vaultToken=_vaultToken, assetAmountReceived=assetAmountReceived, vaultTokenAmountBurned=vaultTokenAmountBurned, refundVaultTokenAmount=refundVaultTokenAmount, usdValue=usdValue, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=_isSignerAgent)
    return assetAmountReceived, vaultTokenAmountBurned, usdValue


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
) -> (uint256, address, uint256, uint256):
    """
    @notice Withdraws tokens from one lego and deposits them into another (always same asset)
    @param _fromLegoId The ID of the source lego
    @param _fromAsset The address of the token to rebalance
    @param _fromVaultToken The source vault token address
    @param _toLegoId The ID of the destination lego
    @param _toVault The destination vault address
    @param _fromVaultTokenAmount The vault token amount to rebalance (defaults to max)
    @return uint256 The amount of assets deposited in the destination vault
    @return address The destination vault token address
    @return uint256 The amount of destination vault tokens received
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.REBALANCE, [_fromAsset], [_fromLegoId, _toLegoId], cd)

    # withdraw from the first lego
    assetAmountReceived: uint256 = 0
    na: uint256 = 0
    withdrawUsdValue: uint256 = 0
    assetAmountReceived, na, withdrawUsdValue = self._withdrawTokens(msg.sender, _fromLegoId, _fromAsset, _fromVaultToken, _fromVaultTokenAmount, isSignerAgent, True, cd)

    # deposit the received assets into the second lego
    assetAmountDeposited: uint256 = 0
    newVaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    depositUsdValue: uint256 = 0
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, depositUsdValue = self._depositTokens(msg.sender, _toLegoId, _fromAsset, _toVault, assetAmountReceived, isSignerAgent, cd)

    usdValue: uint256 = max(withdrawUsdValue, depositUsdValue)
    return assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue


########
# Swap #
########


@nonreentrant
@external
def swapTokens(_swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (uint256, uint256, uint256):
    """
    @notice Swaps tokens between lego integrations
    @param _swapInstructions The instructions for the swaps
    @return uint256 The amount of assets deposited
    @return uint256 The amount of assets received
    @return uint256 The usd value of the transaction
    """
    numSwapInstructions: uint256 = len(_swapInstructions)
    assert numSwapInstructions != 0 # dev: no swaps

    cd: CoreData = self._getCoreData()

    # get high level swap info to check permissions
    tokenIn: address = empty(address)
    tokenOut: address = empty(address)
    initialAmountIn: uint256 = 0
    legoIds: DynArray[uint256, MAX_LEGOS] = []
    tokenIn, tokenOut, initialAmountIn, legoIds = self._getHighLevelSwapInfo(numSwapInstructions, _swapInstructions, cd)

    # check permissions / subscription data
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.SWAP, [tokenIn, tokenOut], legoIds, cd)

    # check if swap token is trial funds asset
    isTrialFundsVaultToken: bool = self._isTrialFundsVaultToken(tokenIn, cd.trialFundsAsset, cd.legoRegistry)

    # perform swap instructions
    amountIn: uint256 = initialAmountIn
    lastTokenOut: address = empty(address)
    lastTokenOutAmount: uint256 = 0
    lastUsdValue: uint256 = 0
    for j: uint256 in range(numSwapInstructions, bound=MAX_SWAP_INSTRUCTIONS):
        i: SwapInstruction = _swapInstructions[j]

        # from lego to lego, must follow the same token path
        if lastTokenOut != empty(address):
            newTokenIn: address = i.tokenPath[0]
            assert lastTokenOut == newTokenIn # dev: invalid token path
            amountIn = min(lastTokenOutAmount, staticcall IERC20(newTokenIn).balanceOf(self))

        lastTokenOut, lastTokenOutAmount, lastUsdValue = self._performSwapInstruction(i.legoId, amountIn, i.minAmountOut, i.tokenPath, i.poolPath, msg.sender, isSignerAgent, cd.legoRegistry, cd.oracleRegistry)

    # make sure they still have enough trial funds
    self._checkTrialFundsPostTx(isTrialFundsVaultToken, cd.trialFundsAsset, cd.trialFundsInitialAmount, cd.legoRegistry)

     # yield tracking
    extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnSwap(tokenIn, lastTokenOut, lastTokenOutAmount, cd.legoRegistry)

    # handle tx fees
    if isSignerAgent:
        self._handleTransactionFees(ActionType.SWAP, lastTokenOut, lastTokenOutAmount, cd.priceSheets, cd.agentFactory)

    return initialAmountIn, lastTokenOutAmount, lastUsdValue


@internal
def _performSwapInstruction(
    _legoId: uint256,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _tokenPath: DynArray[address, MAX_TOKEN_PATH],
    _poolPath: DynArray[address, MAX_TOKEN_PATH - 1],
    _signer: address,
    _isSignerAgent: bool,
    _legoRegistry: address,
    _oracleRegistry: address,
) -> (address, uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # get token in and token out
    tokenIn: address = _tokenPath[0]
    tokenOut: address = _tokenPath[len(_tokenPath) - 1]

    # approve token in
    assert extcall IERC20(tokenIn).approve(legoAddr, _amountIn, default_return_value=True) # dev: approval failed

    # swap assets via lego partner
    tokenInAmount: uint256 = 0
    tokenOutAmount: uint256 = 0
    refundTokenInAmount: uint256 = 0
    usdValue: uint256 = 0
    tokenInAmount, tokenOutAmount, refundTokenInAmount, usdValue = extcall LegoDex(legoAddr).swapTokens(_amountIn, _minAmountOut, _tokenPath, _poolPath, self, _oracleRegistry)

    # reset approvals
    assert extcall IERC20(tokenIn).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log UserWalletSwap(signer=_signer, tokenIn=tokenIn, tokenOut=tokenOut, swapAmount=tokenInAmount, toAmount=tokenOutAmount, refundAssetAmount=refundTokenInAmount, usdValue=usdValue, numTokens=len(_tokenPath), legoId=_legoId, legoAddr=legoAddr, isSignerAgent=_isSignerAgent)
    return tokenOut, tokenOutAmount, usdValue


@view
@internal
def _getHighLevelSwapInfo(
    _numSwapInstructions: uint256,
    _swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS],
    _cd: CoreData,
) -> (address, address, uint256, DynArray[uint256, MAX_LEGOS]):   
    firstRoutePath: DynArray[address, MAX_TOKEN_PATH] = _swapInstructions[0].tokenPath
    firstRouteNumTokens: uint256 = len(firstRoutePath)
    assert firstRouteNumTokens >= 2 # dev: invalid token path

    # finalize token in and token out
    tokenIn: address = firstRoutePath[0]
    tokenOut: address = empty(address)
    if _numSwapInstructions == 1:
        tokenOut = firstRoutePath[firstRouteNumTokens - 1]

    else:
        lastRoutePath: DynArray[address, MAX_TOKEN_PATH] = _swapInstructions[_numSwapInstructions - 1].tokenPath
        lastRouteNumTokens: uint256 = len(lastRoutePath)
        assert lastRouteNumTokens >= 2 # dev: invalid token path
        tokenOut = lastRoutePath[lastRouteNumTokens - 1]

    assert empty(address) not in [tokenIn, tokenOut] # dev: invalid token path

    # get lego ids
    legoIds: DynArray[uint256, MAX_LEGOS] = []
    for i: uint256 in range(_numSwapInstructions, bound=MAX_SWAP_INSTRUCTIONS):
        legoId: uint256 = _swapInstructions[i].legoId
        if legoId not in legoIds:
            legoIds.append(legoId)

    # finalize amount in
    amountIn: uint256 = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(tokenIn, _swapInstructions[0].amountIn, True, _cd)

    return tokenIn, tokenOut, amountIn, legoIds


##################
# Borrow + Repay #
##################


# borrow


@nonreentrant
@external
def borrow(
    _legoId: uint256,
    _borrowAsset: address = empty(address),
    _amount: uint256 = max_value(uint256),
) -> (address, uint256, uint256):
    """
    @notice Borrows an asset from a lego integration
    @param _legoId The ID of the lego to borrow from
    @param _borrowAsset The address of the asset to borrow
    @param _amount The amount of the asset to borrow
    @return address The address of the asset borrowed
    @return uint256 The amount of the asset borrowed
    @return uint256 The usd value of the borrowing
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.BORROW, [_borrowAsset], [_legoId], cd)

    # get lego addr
    legoAddr: address = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # make sure lego can perform this action
    self._checkLegoAccessForAction(legoAddr)

    # borrow via lego partner
    borrowAsset: address = empty(address)
    borrowAmount: uint256 = 0
    usdValue: uint256 = 0
    borrowAsset, borrowAmount, usdValue = extcall LegoCredit(legoAddr).borrow(_borrowAsset, _amount, self, cd.oracleRegistry)

    log UserWalletBorrow(signer=msg.sender, borrowAsset=borrowAsset, borrowAmount=borrowAmount, usdValue=usdValue, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=isSignerAgent)
    return borrowAsset, borrowAmount, usdValue


# repay debt


@nonreentrant
@external
def repayDebt(
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
) -> (address, uint256, uint256, uint256):
    """
    @notice Repays debt for a lego integration
    @param _legoId The ID of the lego to repay debt for
    @param _paymentAsset The address of the asset to use for repayment
    @param _paymentAmount The amount of the asset to use for repayment
    @return address The address of the asset used for repayment
    @return uint256 The amount of the asset used for repayment
    @return uint256 The usd value of the repayment
    @return uint256 The remaining debt
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.REPAY, [_paymentAsset], [_legoId], cd)

    # get lego addr
    legoAddr: address = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # make sure lego can perform this action
    self._checkLegoAccessForAction(legoAddr)

    # finalize amount
    paymentAmount: uint256 = staticcall WalletConfig(cd.walletConfig).getAvailableTxAmount(_paymentAsset, _paymentAmount, True, cd)

    # check if payment asset is trial funds asset
    isTrialFundsVaultToken: bool = self._isTrialFundsVaultToken(_paymentAsset, cd.trialFundsAsset, cd.legoRegistry)

    # repay debt via lego partner
    paymentAsset: address = empty(address)
    usdValue: uint256 = 0
    remainingDebt: uint256 = 0
    assert extcall IERC20(_paymentAsset).approve(legoAddr, paymentAmount, default_return_value=True) # dev: approval failed
    paymentAsset, paymentAmount, usdValue, remainingDebt = extcall LegoCredit(legoAddr).repayDebt(_paymentAsset, paymentAmount, self, cd.oracleRegistry)
    assert extcall IERC20(_paymentAsset).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    # make sure they still have enough trial funds
    self._checkTrialFundsPostTx(isTrialFundsVaultToken, cd.trialFundsAsset, cd.trialFundsInitialAmount, cd.legoRegistry)

    # yield tracking -- paying back debt with vault token
    extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnExit(_paymentAsset, cd.legoRegistry)

    log UserWalletRepayDebt(signer=msg.sender, paymentAsset=paymentAsset, paymentAmount=paymentAmount, usdValue=usdValue, remainingDebt=remainingDebt, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=isSignerAgent)
    return paymentAsset, paymentAmount, usdValue, remainingDebt


#################
# Claim Rewards #
#################


@nonreentrant
@external
def claimRewards(
    _legoId: uint256,
    _market: address = empty(address),
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _proof: bytes32 = empty(bytes32),
):
    """
    @notice Claims rewards from a lego integration
    @param _legoId The lego ID to claim rewards from
    @param _market The market to claim rewards from
    @param _rewardToken The reward token to claim
    @param _rewardAmount The reward amount to claim
    @param _proof The proof to verify the rewards
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.CLAIM_REWARDS, [_rewardToken], [_legoId], cd)

    # get lego addr
    legoAddr: address = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # make sure lego has access to claim rewards
    self._checkLegoAccessForAction(legoAddr)

    # pre reward balance
    preRewardBalance: uint256 = 0
    if _rewardToken != empty(address):
        preRewardBalance = staticcall IERC20(_rewardToken).balanceOf(self)

    # claim rewards
    extcall LegoCommon(legoAddr).claimRewards(self, _market, _rewardToken, _rewardAmount, _proof)

    # post reward balance
    postRewardBalance: uint256 = 0
    if _rewardToken != empty(address):
        postRewardBalance = staticcall IERC20(_rewardToken).balanceOf(self)
    rewardAmount: uint256 = postRewardBalance - preRewardBalance

    # handle tx fees
    if isSignerAgent:
        self._handleTransactionFees(ActionType.CLAIM_REWARDS, _rewardToken, rewardAmount, cd.priceSheets, cd.agentFactory)

    usdValue: uint256 = 0
    if rewardAmount != 0:
        usdValue = staticcall OracleRegistry(cd.oracleRegistry).getUsdValue(_rewardToken, rewardAmount)
    log UserWalletRewardsClaimed(signer=msg.sender, market=_market, rewardToken=_rewardToken, rewardAmount=rewardAmount, usdValue=usdValue, proof=_proof, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=isSignerAgent)


#################
# Add Liquidity #
#################


@nonreentrant
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
    """
    @notice Adds liquidity to a pool
    @param _legoId The ID of the lego to use for adding liquidity
    @param _nftAddr The address of the NFT token contract
    @param _nftTokenId The ID of the NFT token to use for adding liquidity
    @param _pool The address of the pool to add liquidity to
    @param _tokenA The address of the first token to add liquidity
    @param _tokenB The address of the second token to add liquidity
    @param _amountA The amount of the first token to add liquidity
    @param _amountB The amount of the second token to add liquidity
    @param _tickLower The lower tick of the liquidity range
    @param _tickUpper The upper tick of the liquidity range
    @param _minAmountA The minimum amount of the first token to add liquidity
    @param _minAmountB The minimum amount of the second token to add liquidity
    @param _minLpAmount The minimum amount of lp token amount to receive
    @return uint256 The amount of liquidity added
    @return uint256 The amount of the first token added
    @return uint256 The amount of the second token added
    @return uint256 The usd value of the liquidity added
    @return uint256 The ID of the NFT token used for adding liquidity
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.ADD_LIQ, [_tokenA, _tokenB], [_legoId], cd)

    # get lego addr
    legoAddr: address = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # token a
    amountA: uint256 = 0
    isTrialFundsVaultTokenA: bool = False
    if _amountA != 0:
        amountA = staticcall WalletConfig(cd.walletConfig).getAvailableTxAmount(_tokenA, _amountA, True, cd)
        assert extcall IERC20(_tokenA).approve(legoAddr, amountA, default_return_value=True) # dev: approval failed
        isTrialFundsVaultTokenA = self._isTrialFundsVaultToken(_tokenA, cd.trialFundsAsset, cd.legoRegistry)

    # token b
    amountB: uint256 = 0
    isTrialFundsVaultTokenB: bool = False
    if _amountB != 0:
        amountB = staticcall WalletConfig(cd.walletConfig).getAvailableTxAmount(_tokenB, _amountB, True, cd)
        assert extcall IERC20(_tokenB).approve(legoAddr, amountB, default_return_value=True) # dev: approval failed
        isTrialFundsVaultTokenB = self._isTrialFundsVaultToken(_tokenB, cd.trialFundsAsset, cd.legoRegistry)

    # transfer nft to lego (if applicable)
    hasNftLiqPosition: bool = _nftAddr != empty(address) and _nftTokenId != 0
    if hasNftLiqPosition:
        extcall IERC721(_nftAddr).safeTransferFrom(self, legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # add liquidity via lego partner
    liquidityAdded: uint256 = 0
    liqAmountA: uint256 = 0
    liqAmountB: uint256 = 0
    usdValue: uint256 = 0
    refundAssetAmountA: uint256 = 0
    refundAssetAmountB: uint256 = 0
    nftTokenId: uint256 = 0
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = extcall LegoDex(legoAddr).addLiquidity(_nftTokenId, _pool, _tokenA, _tokenB, _tickLower, _tickUpper, amountA, amountB, _minAmountA, _minAmountB, _minLpAmount, self, cd.oracleRegistry)

    # validate the nft came back
    if hasNftLiqPosition:
        assert staticcall IERC721(_nftAddr).ownerOf(_nftTokenId) == self # dev: nft not returned

    # token a
    self._checkTrialFundsPostTx(isTrialFundsVaultTokenA, cd.trialFundsAsset, cd.trialFundsInitialAmount, cd.legoRegistry)
    if amountA != 0:
        assert extcall IERC20(_tokenA).approve(legoAddr, 0, default_return_value=True) # dev: approval failed
        extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnExit(_tokenA, cd.legoRegistry)

    # token b
    self._checkTrialFundsPostTx(isTrialFundsVaultTokenB, cd.trialFundsAsset, cd.trialFundsInitialAmount, cd.legoRegistry)
    if amountB != 0:
        assert extcall IERC20(_tokenB).approve(legoAddr, 0, default_return_value=True) # dev: approval failed
        extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnExit(_tokenB, cd.legoRegistry)

    log UserWalletLiquidityAdded(signer=msg.sender, tokenA=_tokenA, tokenB=_tokenB, liqAmountA=liqAmountA, liqAmountB=liqAmountB, liquidityAdded=liquidityAdded, pool=_pool, usdValue=usdValue, refundAssetAmountA=refundAssetAmountA, refundAssetAmountB=refundAssetAmountB, nftTokenId=nftTokenId, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=isSignerAgent)
    return liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId


####################
# Remove Liquidity #
####################


@nonreentrant
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
    """
    @notice Removes liquidity from a pool
    @param _legoId The ID of the lego to use for removing liquidity
    @param _nftAddr The address of the NFT token contract
    @param _nftTokenId The ID of the NFT token to use for removing liquidity
    @param _pool The address of the pool to remove liquidity from
    @param _tokenA The address of the first token to remove liquidity
    @param _tokenB The address of the second token to remove liquidity
    @param _liqToRemove The amount of liquidity to remove
    @param _minAmountA The minimum amount of the first token to remove liquidity
    @param _minAmountB The minimum amount of the second token to remove liquidity
    @return uint256 The amount of the first token removed
    @return uint256 The amount of the second token removed
    @return uint256 The usd value of the liquidity removed
    @return bool True if the liquidity moved to lego contract was depleted, false otherwise
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.REMOVE_LIQ, [_tokenA, _tokenB], [_legoId], cd)

    # get lego addr
    legoAddr: address = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    lpToken: address = empty(address)
    liqToRemove: uint256 = _liqToRemove

    # transfer nft to lego (if applicable)
    hasNftLiqPosition: bool = _nftAddr != empty(address) and _nftTokenId != 0
    if hasNftLiqPosition:
        extcall IERC721(_nftAddr).safeTransferFrom(self, legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # handle lp token
    else:
        lpToken = staticcall LegoDex(legoAddr).getLpToken(_pool)
        liqToRemove = staticcall WalletConfig(cd.walletConfig).getAvailableTxAmount(lpToken, liqToRemove, False, cd)
        assert extcall IERC20(lpToken).approve(legoAddr, liqToRemove, default_return_value=True) # dev: approval failed

    # remove liquidity via lego partner
    amountA: uint256 = 0
    amountB: uint256 = 0
    usdValue: uint256 = 0
    liquidityRemoved: uint256 = 0
    refundedLpAmount: uint256 = 0
    isDepleted: bool = False
    amountA, amountB, usdValue, liquidityRemoved, refundedLpAmount, isDepleted = extcall LegoDex(legoAddr).removeLiquidity(_nftTokenId, _pool, _tokenA, _tokenB, lpToken, liqToRemove, _minAmountA, _minAmountB, self, cd.oracleRegistry)

    # validate the nft came back, reset lp token approvals
    if hasNftLiqPosition:
        if not isDepleted:
            assert staticcall IERC721(_nftAddr).ownerOf(_nftTokenId) == self # dev: nft not returned
    else:
        assert extcall IERC20(lpToken).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    # yield tracking -- if vault tokens are what is removed from liquidity
    extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnEntry(_tokenA, amountA, cd.legoRegistry)
    extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnEntry(_tokenB, amountB, cd.legoRegistry)

    log UserWalletLiquidityRemoved(signer=msg.sender, tokenA=_tokenA, tokenB=_tokenB, removedAmountA=amountA, removedAmountB=amountB, usdValue=usdValue, isDepleted=isDepleted, liquidityRemoved=liquidityRemoved, lpToken=lpToken, refundedLpAmount=refundedLpAmount, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=isSignerAgent)
    return amountA, amountB, usdValue, isDepleted


##################
# Transfer Funds #
##################


@nonreentrant
@external
def transferFunds(
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
) -> (uint256, uint256):
    """
    @notice Transfers funds to a specified recipient
    @dev Handles both ETH and token transfers with optional amount specification
    @param _recipient The address to receive the funds
    @param _amount The amount to transfer (defaults to max)
    @param _asset The token address (empty for ETH)
    @return uint256 The amount of funds transferred
    @return uint256 The usd value of the transaction
    """
    cd: CoreData = self._getCoreData()
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.TRANSFER, [_asset], [], cd)
    return self._transferFunds(msg.sender, _recipient, _amount, _asset, isSignerAgent, cd)


@internal
def _transferFunds(
    _signer: address,
    _recipient: address,
    _amount: uint256,
    _asset: address,
    _isSignerAgent: bool,
    _cd: CoreData,
) -> (uint256, uint256):
    transferAmount: uint256 = 0
    usdValue: uint256 = 0

    # validate recipient
    if _recipient != _cd.owner:
        assert staticcall WalletConfig(_cd.walletConfig).canTransferToRecipient(_recipient) # dev: recipient not allowed

    # handle eth
    if _asset == empty(address):
        transferAmount = min(_amount, self.balance)
        assert transferAmount != 0 # dev: nothing to transfer
        send(_recipient, transferAmount)
        usdValue = staticcall OracleRegistry(_cd.oracleRegistry).getEthUsdValue(transferAmount)

    # erc20 tokens
    else:

        # check if vault token of trial funds asset
        isTrialFundsVaultToken: bool = self._isTrialFundsVaultToken(_asset, _cd.trialFundsAsset, _cd.legoRegistry)
        transferAmount = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(_asset, _amount, True, _cd)

        assert extcall IERC20(_asset).transfer(_recipient, transferAmount, default_return_value=True) # dev: transfer failed
        usdValue = staticcall OracleRegistry(_cd.oracleRegistry).getUsdValue(_asset, transferAmount)

        # make sure they still have enough trial funds
        self._checkTrialFundsPostTx(isTrialFundsVaultToken, _cd.trialFundsAsset, _cd.trialFundsInitialAmount, _cd.legoRegistry)

        # yield tracking -- transferring out vault token
        extcall WalletConfig(_cd.walletConfig).updateYieldTrackingOnExit(_asset, _cd.legoRegistry)

    log UserWalletFundsTransferred(signer=_signer, recipient=_recipient, asset=_asset, amount=transferAmount, usdValue=usdValue, isSignerAgent=_isSignerAgent)
    return transferAmount, usdValue


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
) -> (uint256, address, uint256):
    """
    @notice Converts ETH to WETH and optionally deposits into a lego integration and vault
    @param _amount The amount of ETH to convert (defaults to max)
    @param _depositLegoId The lego ID to use for deposit (optional)
    @param _depositVault The vault address for deposit (optional)
    @return uint256 The amount of assets deposited (if deposit performed)
    @return address The vault token address (if deposit performed)
    @return uint256 The amount of vault tokens received (if deposit performed)
    """
    cd: CoreData = self._getCoreData()
    weth: address = self.wethAddr
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.CONVERSION, [weth], [_depositLegoId], cd)

    # convert eth to weth
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).deposit(value=amount)
    log UserWalletEthConvertedToWeth(signer=msg.sender, amount=amount, paidEth=msg.value, weth=weth, isSignerAgent=isSignerAgent)

    # deposit weth into lego partner
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    if _depositLegoId != 0:
        depositUsdValue: uint256 = 0
        amount, vaultToken, vaultTokenAmountReceived, depositUsdValue = self._depositTokens(msg.sender, _depositLegoId, weth, _depositVault, amount, isSignerAgent, cd)

    return amount, vaultToken, vaultTokenAmountReceived


# weth -> eth


@nonreentrant
@external
def convertWethToEth(
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
) -> uint256:
    """
    @notice Converts WETH to ETH and optionally withdraws from a vault first
    @param _amount The amount of WETH to convert (defaults to max)
    @param _recipient The address to receive the ETH (optional)
    @param _withdrawLegoId The lego ID to withdraw from (optional)
    @param _withdrawVaultToken The vault token to withdraw (optional)
    @return uint256 The amount of ETH received
    """
    cd: CoreData = self._getCoreData()
    weth: address = self.wethAddr
    isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.CONVERSION, [weth], [_withdrawLegoId], cd)

    # withdraw weth from lego partner (if applicable)
    amount: uint256 = _amount
    usdValue: uint256 = 0
    if _withdrawLegoId != 0:
        _na: uint256 = 0
        amount, _na, usdValue = self._withdrawTokens(msg.sender, _withdrawLegoId, weth, _withdrawVaultToken, _amount, isSignerAgent, True, cd)

    # convert weth to eth
    amount = min(amount, staticcall IERC20(weth).balanceOf(self))
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).withdraw(amount)
    log UserWalletWethConvertedToEth(signer=msg.sender, amount=amount, weth=weth, isSignerAgent=isSignerAgent)

    # transfer eth to recipient (if applicable)
    if _recipient != empty(address):
        amount, usdValue = self._transferFunds(msg.sender, _recipient, amount, empty(address), isSignerAgent, cd)

    return amount


#############
# Utilities #
#############


@view
@internal
def _getCoreData() -> CoreData:
    addyRegistry: address = ADDY_REGISTRY
    walletConfig: address = self.walletConfig
    return CoreData(
        owner=staticcall WalletConfig(walletConfig).owner(),
        wallet=self,
        walletConfig=walletConfig,
        addyRegistry=addyRegistry,
        agentFactory=staticcall AddyRegistry(addyRegistry).getAddy(AGENT_FACTORY_ID),
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

    # check if agent is blacklisted
    if agent != empty(address):
        assert not staticcall AgentFactory(_cd.agentFactory).agentBlacklist(agent) # dev: agent is blacklisted

    # handle subscriptions and permissions
    protocolSub: SubPaymentInfo = empty(SubPaymentInfo)
    agentSub: SubPaymentInfo = empty(SubPaymentInfo)
    protocolSub, agentSub = extcall WalletConfig(_cd.walletConfig).handleSubscriptionsAndPermissions(agent, _action, _assets, _legoIds, _cd)

    # handle protocol subscription payment
    if protocolSub.amount != 0:
        assert extcall IERC20(protocolSub.asset).transfer(protocolSub.recipient, protocolSub.amount, default_return_value=True) # dev: protocol subscription payment failed
        log UserWalletSubscriptionPaid(recipient=protocolSub.recipient, asset=protocolSub.asset, amount=protocolSub.amount, usdValue=protocolSub.usdValue, paidThroughBlock=protocolSub.paidThroughBlock, isAgent=False)

    # handle agent subscription payment
    if agentSub.amount != 0:
        assert extcall IERC20(agentSub.asset).transfer(agentSub.recipient, agentSub.amount, default_return_value=True) # dev: agent subscription payment failed
        log UserWalletSubscriptionPaid(recipient=agent, asset=agentSub.asset, amount=agentSub.amount, usdValue=agentSub.usdValue, paidThroughBlock=agentSub.paidThroughBlock, isAgent=True)

    return agent != empty(address)


@internal
def _handleTransactionFees(
    _action: ActionType,
    _asset: address,
    _amount: uint256,
    _priceSheets: address,
    _agentFactory: address,
) -> uint256:
    if _amount == 0 or _asset == empty(address):
        return 0

    # pay ambassador yield bonus first (we do early return once we get into tx fees)
    ambassadorRecipient: address = empty(address)
    if _action == ActionType.WITHDRAWAL:
        ambassadorRecipient = self._getAmbassadorProceedsAddr(empty(address))
        extcall AgentFactory(_agentFactory).payAmbassadorYieldBonus(ambassadorRecipient, _asset, _amount)

    # get transaction fees
    fee: uint256 = 0
    protocolRecipient: address = empty(address)
    ambassadorRatio: uint256 = 0
    fee, protocolRecipient, ambassadorRatio = staticcall PriceSheets(_priceSheets).getTransactionFeeDataWithAmbassadorRatio(self, _action)
    if fee == 0 or protocolRecipient == empty(address):
        return 0

    adjFee: uint256 = min(fee, HUNDRED_PERCENT)
    feeTotalAmount: uint256 = min(_amount * adjFee // HUNDRED_PERCENT, staticcall IERC20(_asset).balanceOf(self))
    if feeTotalAmount == 0:
        return 0

    protocolAmount: uint256 = feeTotalAmount
    ambassadorAmount: uint256 = 0

    # pay ambassador proceeds
    if ambassadorRatio != 0:
        ambassadorRecipient = self._getAmbassadorProceedsAddr(ambassadorRecipient)
        ambassadorAmount = self._payAmbassadorTxFee(_asset, protocolAmount, ambassadorRatio, ambassadorRecipient)
        if ambassadorAmount != 0:
            protocolAmount = min(protocolAmount - ambassadorAmount, staticcall IERC20(_asset).balanceOf(self))

    # pay protocol proceeds
    if protocolAmount != 0:
        assert extcall IERC20(_asset).transfer(protocolRecipient, protocolAmount, default_return_value=True) # dev: protocol tx fee payment failed

    log UserWalletTransactionFeePaid(asset=_asset, protocolRecipient=protocolRecipient, protocolAmount=protocolAmount, ambassadorRecipient=ambassadorRecipient, ambassadorAmount=ambassadorAmount, fee=fee, action=_action)
    return feeTotalAmount


# ambassador


@view
@internal
def _getAmbassadorProceedsAddr(_maybeAmbassador: address) -> address:
    if _maybeAmbassador != empty(address):
        return _maybeAmbassador

    myAmbassador: address = staticcall WalletConfig(self.walletConfig).myAmbassador()
    if myAmbassador == empty(address):
        return empty(address)
    ambassadorWalletConfig: address = staticcall UserWallet(myAmbassador).walletConfig()
    return staticcall WalletConfig(ambassadorWalletConfig).getProceedsAddr()


@internal
def _payAmbassadorTxFee(
    _asset: address,
    _amount: uint256,
    _ambassadorRatio: uint256,
    _ambassadorAddr: address,
) -> uint256:
    if _ambassadorAddr == empty(address):
        return 0

    ambassadorRatio: uint256 = min(_ambassadorRatio, HUNDRED_PERCENT)
    amount: uint256 = min(_amount * ambassadorRatio // HUNDRED_PERCENT, staticcall IERC20(_asset).balanceOf(self))
    if amount != 0:
        assert extcall IERC20(_asset).transfer(_ambassadorAddr, amount, default_return_value=True) # dev: ambassador tx fee payment failed

    return min(_amount, amount)


# allow lego to perform action


@internal
def _checkLegoAccessForAction(_legoAddr: address):
    targetAddr: address = empty(address)
    accessAbi: String[64] = empty(String[64])
    numInputs: uint256 = 0
    targetAddr, accessAbi, numInputs = staticcall LegoCommon(_legoAddr).getAccessForLego(self)

    # nothing to do here
    if targetAddr == empty(address):
        return

    method_abi: bytes4 = convert(slice(keccak256(accessAbi), 0, 4), bytes4)
    success: bool = False
    response: Bytes[32] = b""

    # assumes input is: lego addr (operator)
    if numInputs == 1:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(_legoAddr, bytes32),
            ),
            revert_on_failure=False,
            max_outsize=32,
        )
    
    # assumes input (and order) is: user addr (owner), lego addr (operator)
    elif numInputs == 2:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(self, bytes32),
                convert(_legoAddr, bytes32),
            ),
            revert_on_failure=False,
            max_outsize=32,
        )

    # assumes input (and order) is: user addr (owner), lego addr (operator), allowed bool
    elif numInputs == 3:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(self, bytes32),
                convert(_legoAddr, bytes32),
                convert(True, bytes32),
            ),
            revert_on_failure=False,
            max_outsize=32,
        )

    assert success # dev: failed to set operator


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
def recoverTrialFunds() -> bool:
    """
    @notice Recovers trial funds from the wallet by withdrawing from vault tokens and transferring to the agent factory
    @dev This function can only be called by the agent factory, owner, or wallet config. It will:
        1. Check if there are trial funds to recover
        2. Calculate target recovery amount with 2% buffer
        3. Transfer any available balance directly
        4. Withdraw from vault tokens if needed
        5. Update trial funds tracking data
    @return bool True if trial funds were recovered successfully, False otherwise
    """
    cd: CoreData = self._getCoreData()
    assert msg.sender in [cd.agentFactory, cd.owner, cd.walletConfig] # dev: no perms

    # make sure something to recover
    if cd.trialFundsAsset == empty(address) or cd.trialFundsInitialAmount == 0:
        return False

    # account for extra dust / yield
    targetRecoveryAmount: uint256 = cd.trialFundsInitialAmount * 101_00 // HUNDRED_PERCENT # 1% buffer
    amountRecovered: uint256 = 0

    # transfer any available balance
    balanceAvail: uint256 = staticcall IERC20(cd.trialFundsAsset).balanceOf(self)
    if balanceAvail != 0:
        availableAmount: uint256 = min(balanceAvail, targetRecoveryAmount)
        assert extcall IERC20(cd.trialFundsAsset).transfer(cd.agentFactory, availableAmount, default_return_value=True) # dev: trial funds transfer failed
        amountRecovered += availableAmount
        targetRecoveryAmount -= availableAmount

    if targetRecoveryAmount == 0:
        return True

    # iterate through vault tokens (related to trial funds)
    trialFundsVaultTokens: DynArray[VaultTokenInfo, MAX_VAULTS_FOR_USER] = staticcall LegoRegistry(cd.legoRegistry).getVaultTokensForUser(self, cd.trialFundsAsset)
    for v: VaultTokenInfo in trialFundsVaultTokens:
        assetAmountReceived: uint256 = 0
        na1: uint256 = 0
        na2: uint256 = 0
        assetAmountReceived, na1, na2 = self._withdrawTokens(cd.agentFactory, v.legoId, cd.trialFundsAsset, v.vaultToken, max_value(uint256), False, False, cd)

        # recover funds
        transferAmount: uint256 = min(assetAmountReceived, targetRecoveryAmount)
        assert extcall IERC20(cd.trialFundsAsset).transfer(cd.agentFactory, transferAmount, default_return_value=True) # dev: trial funds transfer failed
        amountRecovered += transferAmount
        targetRecoveryAmount -= transferAmount

        # reached target recovery amount, deposit any extra balance back lego
        if targetRecoveryAmount == 0:
            depositAmount: uint256 = min(assetAmountReceived - transferAmount, staticcall IERC20(cd.trialFundsAsset).balanceOf(self))
            if depositAmount != 0:
                self._depositTokens(msg.sender, v.legoId, cd.trialFundsAsset, v.vaultToken, depositAmount, False, cd)
            break

    if amountRecovered == 0:
        return False

    # update trial funds data
    newTrialFundsInitialAmount: uint256 = cd.trialFundsInitialAmount - min(cd.trialFundsInitialAmount, amountRecovered)
    self.trialFundsInitialAmount = newTrialFundsInitialAmount
    if newTrialFundsInitialAmount == 0:
        self.trialFundsAsset = empty(address)

    log UserWalletTrialFundsRecovered(asset=cd.trialFundsAsset, amountRecovered=amountRecovered, remainingAmount=newTrialFundsInitialAmount)
    return True


# recover nft


@external
def recoverNft(_collection: address, _nftTokenId: uint256) -> bool:
    """
    @notice Recovers an NFT from the wallet
    @param _collection The address of the NFT collection
    @param _nftTokenId The ID of the NFT to recover
    @return bool True if the NFT was recovered successfully, False otherwise
    """
    owner: address = staticcall WalletConfig(self.walletConfig).owner()
    assert msg.sender == owner # dev: no perms

    if staticcall IERC721(_collection).ownerOf(_nftTokenId) != self:
        return False

    extcall IERC721(_collection).safeTransferFrom(self, owner, _nftTokenId)
    log UserWalletNftRecovered(collection=_collection, nftTokenId=_nftTokenId, owner=owner)
    return True


# wallet migration


@external
def migrateWalletOut(
    _newWallet: address,
    _assetsToMigrate: DynArray[address, MAX_MIGRATION_ASSETS],
    _whitelistToMigrate: DynArray[address, MAX_MIGRATION_WHITELIST],
) -> bool:
    """
    @notice Migrates a wallet to a new wallet
    @param _newWallet The address of the new wallet
    @param _assetsToMigrate The assets to migrate
    @param _whitelistToMigrate The whitelist to migrate
    @return bool True if the migration was successful, False otherwise
    """
    cd: CoreData = self._getCoreData()
    assert msg.sender == cd.walletConfig # dev: only wallet config can call this
    assert staticcall AgentFactory(cd.agentFactory).isUserWallet(_newWallet) # dev: must be Underscore wallet

    # eth
    if self.balance != 0:
        send(_newWallet, self.balance)

    assetsMigrated: DynArray[address, MAX_MIGRATION_ASSETS] = []
    vaultTokensMigrated: DynArray[address, MAX_MIGRATION_ASSETS] = []

    # erc20 tokens
    for asset: address in _assetsToMigrate:
        if asset == empty(address):
            continue

        assetBal: uint256 = staticcall IERC20(asset).balanceOf(self)
        if assetBal == 0:
            continue

        assert extcall IERC20(asset).transfer(_newWallet, assetBal, default_return_value=True) # dev: asset transfer failed
        if staticcall WalletConfig(cd.walletConfig).isVaultToken(asset):
            vaultTokensMigrated.append(asset)
        else:
            assetsMigrated.append(asset)

    # finish migration
    newWalletConfig: address = staticcall UserWallet(_newWallet).walletConfig()
    assert extcall WalletConfig(newWalletConfig).finishMigrationIn(_whitelistToMigrate, assetsMigrated, vaultTokensMigrated) # dev: migration failed
    return True
