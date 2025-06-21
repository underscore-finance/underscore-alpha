# @version 0.4.1
# pragma optimize codesize

# implements: UserWalletInterface
from interfaces import LegoDex
from interfaces import LegoYield
from interfaces import LegoCommon
from interfaces import LegoCredit
from interfaces import UserWalletInterface

from ethereum.ercs import IERC20
from ethereum.ercs import IERC721

interface LegoPartner:
    def addLiquidityConcentrated(_nftTokenId: uint256, _pool: address, _tokenA: address, _tokenB: address, _tickLower: int24, _tickUpper: int24, _amountA: uint256, _amountB: uint256, _minAmountA: uint256, _minAmountB: uint256, _recipient: address) -> (uint256, uint256, uint256, uint256): nonpayable
    def addLiquidity(_pool: address, _tokenA: address, _tokenB: address, _amountA: uint256, _amountB: uint256, _minAmountA: uint256, _minAmountB: uint256, _minLpAmount: uint256, _recipient: address) -> (address, uint256, uint256, uint256): nonpayable
    def removeLiquidityConcentrated(_nftTokenId: uint256, _pool: address, _tokenA: address, _tokenB: address, _liqToRemove: uint256, _minAmountA: uint256, _minAmountB: uint256, _recipient: address) -> (uint256, uint256, uint256, bool): nonpayable
    def removeLiquidity(_pool: address, _tokenA: address, _tokenB: address, _lpToken: address, _lpAmount: uint256, _minAmountA: uint256, _minAmountB: uint256, _recipient: address) -> (uint256, uint256, uint256): nonpayable
    def swapTokens(_amountIn: uint256, _minAmountOut: uint256, _tokenPath: DynArray[address, MAX_TOKEN_PATH], _poolPath: DynArray[address, MAX_TOKEN_PATH - 1], _recipient: address) -> (uint256, uint256): nonpayable
    def repayDebt(_paymentAsset: address, _paymentAmount: uint256, _extraAddr: address, _extraVal: uint256, _recipient: address) -> uint256: nonpayable
    def borrow(_borrowAsset: address, _amount: uint256, _extraAddr: address, _extraVal: uint256, _recipient: address) -> (address, uint256): nonpayable
    def removeCollateral(_asset: address, _amount: uint256, _extraAddr: address, _extraVal: uint256, _recipient: address) -> uint256: nonpayable
    def depositForYield(_asset: address, _amount: uint256, _vaultAddr: address, _recipient: address) -> (uint256, address, uint256): nonpayable
    def addCollateral(_asset: address, _amount: uint256, _extraAddr: address, _extraVal: uint256, _recipient: address) -> uint256: nonpayable
    def withdrawFromYield(_vaultToken: address, _amount: uint256, _recipient: address) -> (uint256, address, uint256): nonpayable
    def getAccessForLego(_user: address) -> (address, String[64], uint256): view

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
    def isBorrowLego(_legoId: uint256) -> bool: view

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
    EARN
    SWAP
    DEBT
    LIQUIDITY
    WETH_WRAP

struct CoreData:
    legoAddr: address
    owner: address
    isSignerAgent: bool
    wallet: address
    walletConfig: address
    undyHq: address
    agentFactory: address
    legoRegistry: address
    priceSheets: address
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
    vaultAddr: address

event YieldDeposit:
    asset: indexed(address)
    assetAmount: uint256
    vaultToken: indexed(address)
    vaultTokenAmount: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool

event YieldWithdrawal:
    vaultToken: indexed(address)
    vaultTokenAmountBurned: uint256
    underlyingAsset: indexed(address)
    underlyingAmountReceived: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool
        
event SwapPerformed:
    tokenIn: indexed(address)
    tokenInAmount: uint256
    tokenOut: indexed(address)
    tokenOutAmount: uint256
    numTokens: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool

event CollateralAdded:
    asset: indexed(address)
    amountDeposited: uint256
    extraAddr: indexed(address)
    extraVal: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool

event CollateralRemoved:
    asset: indexed(address)
    amountRemoved: uint256
    extraAddr: indexed(address)
    extraVal: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool

event NewBorrow:
    borrowAsset: indexed(address)
    borrowAmount: uint256
    extraAddr: indexed(address)
    extraVal: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool

event DebtRepayment:
    paymentAsset: indexed(address)
    repaidAmount: uint256
    extraAddr: indexed(address)
    extraVal: uint256
    legoId: uint256
    legoAddr: address
    signer: indexed(address)
    isSignerAgent: bool

event LiquidityAdded:
    pool: indexed(address)
    tokenA: indexed(address)
    amountA: uint256
    tokenB: indexed(address)
    amountB: uint256
    lpToken: address
    lpAmountReceived: uint256
    legoId: uint256
    legoAddr: address
    signer: address
    isSignerAgent: bool

event ConcentratedLiquidityAdded:
    nftTokenId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    amountA: uint256
    tokenB: indexed(address)
    amountB: uint256
    liqAdded: uint256
    legoId: uint256
    legoAddr: address
    signer: address
    isSignerAgent: bool

event LiquidityRemoved:
    pool: indexed(address)
    tokenA: indexed(address)
    amountAReceived: uint256
    tokenB: indexed(address)
    amountBReceived: uint256
    lpToken: address
    lpAmountBurned: uint256
    legoId: uint256
    legoAddr: address
    signer: address
    isSignerAgent: bool

event ConcentratedLiquidityRemoved:
    nftTokenId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    amountAReceived: uint256
    tokenB: indexed(address)
    amountBReceived: uint256
    liqRemoved: uint256
    legoId: uint256
    legoAddr: address
    signer: address
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

# event UserWalletFundsTransferred:
#     signer: indexed(address)
#     recipient: indexed(address)
#     asset: indexed(address)
#     amount: uint256
#     usdValue: uint256
#     isSignerAgent: bool

# event UserWalletRewardsClaimed:
#     signer: address
#     market: address
#     rewardToken: address
#     rewardAmount: uint256
#     usdValue: uint256
#     proof: bytes32
#     legoId: uint256
#     legoAddr: address
#     isSignerAgent: bool

event EthWrapped:
    amount: uint256
    paidEth: uint256
    weth: indexed(address)
    signer: indexed(address)
    isSignerAgent: bool

event WethUnwrapped:
    amount: uint256
    weth: indexed(address)
    signer: indexed(address)
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

# registry ids
AGENT_FACTORY_ID: constant(uint256) = 1
LEGO_REGISTRY_ID: constant(uint256) = 2
PRICE_SHEETS_ID: constant(uint256) = 3

MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_TOKEN_PATH: constant(uint256) = 5
MAX_ASSETS: constant(uint256) = 25
MAX_LEGOS: constant(uint256) = 20
MAX_VAULTS_FOR_USER: constant(uint256) = 30
MAX_MIGRATION_ASSETS: constant(uint256) = 40
MAX_MIGRATION_WHITELIST: constant(uint256) = 20
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%

ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UnderscoreErc721"
API_VERSION: constant(String[28]) = "0.0.4"

UNDY_HQ: public(immutable(address))
WETH: public(immutable(address))


@deploy
def __init__(
    _undyHq: address,
    _wethAddr: address,
    _walletConfig: address,
    _trialFundsAsset: address,
    _trialFundsInitialAmount: uint256,
):
    assert empty(address) not in [_undyHq, _wethAddr, _walletConfig] # dev: invalid addrs
    self.walletConfig = _walletConfig

    UNDY_HQ = _undyHq
    WETH = _wethAddr

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
    return API_VERSION


@view
@external
def canBeAmbassador() -> bool:
    return staticcall WalletConfig(self.walletConfig).canWalletBeAmbassador()


#########
# Yield #
#########


# deposit


@nonreentrant
@external
def depositForYield(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address = empty(address),
    _amount: uint256 = max_value(uint256),
) -> (uint256, address, uint256):
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.EARN, [_asset], [_legoId], cd)
    return self._depositForYield(_legoId, _asset, _vaultAddr, _amount, msg.sender, True, cd)


@internal
def _depositForYield(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address,
    _amount: uint256,
    _signer: address,
    _shouldPerformHousekeeping: bool,
    _cd: CoreData,
) -> (uint256, address, uint256):
    amount: uint256 = self._getAmountAndApprove(_asset, _amount, _cd.legoAddr) # doing approval here

    # deposit for yield
    assetAmount: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    assetAmount, vaultToken, vaultTokenAmountReceived = extcall LegoPartner(_cd.legoAddr).depositForYield(_asset, amount, _vaultAddr, self)
    assert extcall IERC20(_asset).approve(_cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    if _shouldPerformHousekeeping:
        # inputs: _asset, assetAmount, vaultToken, vaultTokenAmountReceived
        pass # TODO: perform housekeeping

    log YieldDeposit(
        asset = _asset,
        assetAmount = assetAmount,
        vaultToken = vaultToken,
        vaultTokenAmount = vaultTokenAmountReceived,
        legoId = _legoId,
        legoAddr = _cd.legoAddr,
        signer = _signer,
        isSignerAgent = _cd.isSignerAgent,
    )
    return assetAmount, vaultToken, vaultTokenAmountReceived


# withdraw


@nonreentrant
@external
def withdrawFromYield(
    _legoId: uint256,
    _vaultToken: address,
    _amount: uint256 = max_value(uint256),
) -> (uint256, address, uint256):
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.EARN, [_vaultToken], [_legoId], cd)
    return self._withdrawFromYield(_legoId, _vaultToken, _amount, msg.sender, True, cd)


@internal
def _withdrawFromYield(
    _legoId: uint256,
    _vaultToken: address,
    _amount: uint256,
    _signer: address,
    _shouldPerformHousekeeping: bool,
    _cd: CoreData,
) -> (uint256, address, uint256):
    amount: uint256 = self._getAmountAndApprove(_vaultToken, _amount, empty(address)) # not approving here

    # some vault tokens require max value approval (comp v3)
    assert extcall IERC20(_vaultToken).approve(_cd.legoAddr, max_value(uint256), default_return_value=True) # dev: approval failed

    # withdraw from yield
    vaultTokenAmountBurned: uint256 = 0
    underlyingAsset: address = empty(address)
    underlyingAmount: uint256 = 0
    vaultTokenAmountBurned, underlyingAsset, underlyingAmount = extcall LegoPartner(_cd.legoAddr).withdrawFromYield(_vaultToken, amount, self)
    assert extcall IERC20(_vaultToken).approve(_cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    if _shouldPerformHousekeeping:
        # inputs: underlyingAsset, underlyingAmount, _vaultToken, vaultTokenAmountBurned
        pass # TODO: perform housekeeping

    log YieldWithdrawal(
        vaultToken = _vaultToken,
        vaultTokenAmountBurned = vaultTokenAmountBurned,
        underlyingAsset = underlyingAsset,
        underlyingAmountReceived = underlyingAmount,
        legoId = _legoId,
        legoAddr = _cd.legoAddr,
        signer = _signer,
        isSignerAgent = _cd.isSignerAgent,
    )
    return vaultTokenAmountBurned, underlyingAsset, underlyingAmount


# rebalance position


@nonreentrant
@external
def rebalanceYieldPosition(
    _fromLegoId: uint256,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVaultAddr: address = empty(address),
    _fromVaultAmount: uint256 = max_value(uint256),
) -> (uint256, address, uint256):
    cd: CoreData = self._getCoreData(_fromLegoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.EARN, [_fromVaultToken], [_fromLegoId, _toLegoId], cd)

    # withdraw
    vaultTokenAmountBurned: uint256 = 0
    underlyingAsset: address = empty(address)
    underlyingAmount: uint256 = 0
    vaultTokenAmountBurned, underlyingAsset, underlyingAmount = self._withdrawFromYield(_fromLegoId, _fromVaultToken, _fromVaultAmount, msg.sender, False, cd)

    # deposit
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    cd.legoAddr = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_toLegoId)
    underlyingAmount, vaultToken, vaultTokenAmountReceived = self._depositForYield(_toLegoId, underlyingAsset, _toVaultAddr, underlyingAmount, msg.sender, False, cd)

    # TODO: perform housekeeping
    # inputs: underlyingAsset, underlyingAmount, vaultToken, vaultTokenAmountReceived

    return underlyingAmount, vaultToken, vaultTokenAmountReceived


###################
# Swap / Exchange #
###################


@nonreentrant
@external
def swapTokens(_instructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, uint256, address, uint256):
    tokenIn: address = empty(address)
    origAmountIn: uint256 = 0
    cd: CoreData = empty(CoreData)
    tokenIn, origAmountIn, cd = self._validateAndGetSwapInfo(_instructions, msg.sender)

    amountIn: uint256 = origAmountIn
    lastTokenOut: address = empty(address)
    lastTokenOutAmount: uint256 = 0
    for i: SwapInstruction in _instructions:
        if lastTokenOut != empty(address):
            newTokenIn: address = i.tokenPath[0]
            assert lastTokenOut == newTokenIn # dev: must honor token path
            amountIn = min(lastTokenOutAmount, staticcall IERC20(newTokenIn).balanceOf(self))
        lastTokenOut, lastTokenOutAmount = self._performSwapInstruction(amountIn, i, msg.sender, cd)

    # handle tx fees
    if cd.isSignerAgent: # TODO: lastTokenOutAmount should reduce fees
        self._handleTransactionFees(ActionType.SWAP, lastTokenOut, lastTokenOutAmount, cd)

    # TODO: perform housekeeping
    # inputs: tokenIn, amountIn, tokenOut, lastTokenOutAmount

    return tokenIn, origAmountIn, lastTokenOut, lastTokenOutAmount


@internal
def _performSwapInstruction(
    _amountIn: uint256,
    _i: SwapInstruction,
    _signer: address,
    _cd: CoreData,
) -> (address, uint256):
    legoAddr: address = staticcall LegoRegistry(_cd.legoRegistry).getLegoAddr(_i.legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # tokens
    tokenIn: address = _i.tokenPath[0]
    tokenOut: address = _i.tokenPath[len(_i.tokenPath) - 1]
    tokenInAmount: uint256 = 0
    tokenOutAmount: uint256 = 0

    assert extcall IERC20(tokenIn).approve(legoAddr, _amountIn, default_return_value=True) # dev: approval failed
    tokenInAmount, tokenOutAmount = extcall LegoPartner(legoAddr).swapTokens(_amountIn, _i.minAmountOut, _i.tokenPath, _i.poolPath, self)
    assert extcall IERC20(tokenIn).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log SwapPerformed(
        tokenIn = tokenIn,
        tokenInAmount = tokenInAmount,
        tokenOut = tokenOut,
        tokenOutAmount = tokenOutAmount,
        numTokens = len(_i.tokenPath),
        legoId = _i.legoId,
        legoAddr = _cd.legoAddr,
        signer = _signer,
        isSignerAgent = _cd.isSignerAgent,
    )
    return tokenOut, tokenOutAmount


@internal
def _validateAndGetSwapInfo(_instructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS], _signer: address) -> (address, uint256, CoreData):
    numSwapInstructions: uint256 = len(_instructions)
    assert numSwapInstructions != 0 # dev: no swaps

    # lego ids, make sure token paths are valid
    legoIds: DynArray[uint256, MAX_LEGOS] = []
    for i: SwapInstruction in _instructions:
        assert len(i.tokenPath) >= 2 # dev: invalid token path
        if i.legoId not in legoIds:
            legoIds.append(i.legoId)

    # finalize tokens
    firstRoutePath: DynArray[address, MAX_TOKEN_PATH] = _instructions[0].tokenPath
    tokenIn: address = firstRoutePath[0]
    tokenOut: address = empty(address)

    if numSwapInstructions == 1:
        tokenOut = firstRoutePath[len(firstRoutePath) - 1]
    else:
        lastRoutePath: DynArray[address, MAX_TOKEN_PATH] = _instructions[numSwapInstructions - 1].tokenPath
        tokenOut = lastRoutePath[len(lastRoutePath) - 1]

    assert empty(address) not in [tokenIn, tokenOut] # dev: invalid token path
    cd: CoreData = self._getCoreData(0)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(_signer, ActionType.SWAP, [tokenIn, tokenOut], legoIds, cd)

    amountIn: uint256 = self._getAmountAndApprove(tokenIn, _instructions[0].amountIn, empty(address)) # not approving here
    return tokenIn, amountIn, cd


########
# Debt #
########


# NOTE: these functions assume there is no vault token involved (i.e. Ripe Protocol)
# You can also use `depositIntoProtocol` and `withdrawFromProtocol` if a vault token is involved


# add collateral


@nonreentrant
@external
def addCollateral(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _extraAddr: address = empty(address),
    _extraVal: uint256 = 0,
) -> uint256:
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.DEBT, [_asset], [_legoId], cd)

    # add collateral
    amount: uint256 = self._getAmountAndApprove(_asset, _amount, cd.legoAddr) # doing approval here
    amountDeposited: uint256 = extcall LegoPartner(cd.legoAddr).addCollateral(_asset, amount, _extraAddr, _extraVal, self)
    assert extcall IERC20(_asset).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    # TODO: perform housekeeping
    # inputs: _asset, amountDeposited

    log CollateralAdded(
        asset = _asset,
        amountDeposited = amountDeposited,
        extraAddr = _extraAddr,
        extraVal = _extraVal,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return amountDeposited


# remove collateral


@nonreentrant
@external
def removeCollateral(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _extraAddr: address = empty(address),
    _extraVal: uint256 = 0,
) -> uint256:
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.DEBT, [_asset], [_legoId], cd)

    # remove collateral
    amountRemoved: uint256 = extcall LegoPartner(cd.legoAddr).removeCollateral(_asset, _amount, _extraAddr, _extraVal, self)

    # TODO: perform housekeeping
    # inputs: _asset, assetRemoved

    log CollateralRemoved(
        asset = _asset,
        amountRemoved = amountRemoved,
        extraAddr = _extraAddr,
        extraVal = _extraVal,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return amountRemoved


# borrow


@nonreentrant
@external
def borrow(
    _legoId: uint256,
    _borrowAsset: address,
    _amount: uint256 = max_value(uint256),
    _extraAddr: address = empty(address),
    _extraVal: uint256 = 0,
) -> (address, uint256):
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.DEBT, [_borrowAsset], [_legoId], cd)

    # borrow
    borrowAsset: address = empty(address)
    borrowAmount: uint256 = 0
    borrowAsset, borrowAmount = extcall LegoPartner(cd.legoAddr).borrow(_borrowAsset, _amount, _extraAddr, _extraVal, self)

    # TODO: perform housekeeping
    # inputs: borrowAsset, borrowAmount

    log NewBorrow(
        borrowAsset = borrowAsset,
        borrowAmount = borrowAmount,
        extraAddr = _extraAddr,
        extraVal = _extraVal,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return borrowAsset, borrowAmount


# repay debt


@nonreentrant
@external
def repayDebt(
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _extraAddr: address = empty(address),
    _extraVal: uint256 = 0,
) -> uint256:
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.DEBT, [_paymentAsset], [_legoId], cd)

    amount: uint256 = self._getAmountAndApprove(_paymentAsset, _paymentAmount, cd.legoAddr) # doing approval here
    repaidAmount: uint256 = extcall LegoPartner(cd.legoAddr).repayDebt(_paymentAsset, amount, _extraAddr, _extraVal, self)
    assert extcall IERC20(_paymentAsset).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    # TODO: perform housekeeping
    # inputs: _paymentAsset, repaidAmount

    log DebtRepayment(
        paymentAsset = _paymentAsset,
        repaidAmount = repaidAmount,
        extraAddr = _extraAddr,
        extraVal = _extraVal,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return repaidAmount


#################
# Add Liquidity #
#################


@nonreentrant
@external
def addLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _minLpAmount: uint256 = 0,
) -> (uint256, uint256, uint256):
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.LIQUIDITY, [_tokenA, _tokenB], [_legoId], cd)

    # token approvals
    amountA: uint256 = self._getAmountAndApprove(_tokenA, _amountA, cd.legoAddr)
    amountB: uint256 = self._getAmountAndApprove(_tokenB, _amountB, cd.legoAddr)

    # add liquidity via lego partner
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    addedTokenA: uint256 = 0
    addedTokenB: uint256 = 0
    lpToken, lpAmountReceived, addedTokenA, addedTokenB = extcall LegoPartner(cd.legoAddr).addLiquidity(_pool, _tokenA, _tokenB, amountA, amountB, _minAmountA, _minAmountB, _minLpAmount, self)

    # remove approvals
    if amountA != 0:
        assert extcall IERC20(_tokenA).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed
    if amountB != 0:
        assert extcall IERC20(_tokenB).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    # TODO: perform housekeeping
    # inputs: _tokenA, _tokenB, addedTokenA, addedTokenB

    log LiquidityAdded(
        pool = _pool,
        tokenA = _tokenA,
        amountA = addedTokenA,
        tokenB = _tokenB,
        amountB = addedTokenB,
        lpToken = lpToken,
        lpAmountReceived = lpAmountReceived,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return lpAmountReceived, addedTokenA, addedTokenB


@nonreentrant
@external
def addLiquidityConcentrated(
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
) -> (uint256, uint256, uint256, uint256):
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.LIQUIDITY, [_tokenA, _tokenB], [_legoId], cd)

    # token approvals
    amountA: uint256 = self._getAmountAndApprove(_tokenA, _amountA, cd.legoAddr)
    amountB: uint256 = self._getAmountAndApprove(_tokenB, _amountB, cd.legoAddr)

    # transfer nft to lego (if applicable)
    hasNftLiqPosition: bool = _nftAddr != empty(address) and _nftTokenId != 0
    if hasNftLiqPosition:
        extcall IERC721(_nftAddr).safeTransferFrom(self, cd.legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # add liquidity via lego partner
    liqAdded: uint256 = 0
    addedTokenA: uint256 = 0
    addedTokenB: uint256 = 0
    nftTokenId: uint256 = 0
    liqAdded, addedTokenA, addedTokenB, nftTokenId = extcall LegoPartner(cd.legoAddr).addLiquidityConcentrated(_nftTokenId, _pool, _tokenA, _tokenB, _tickLower, _tickUpper, amountA, amountB, _minAmountA, _minAmountB, self)

    # make sure nft is back
    assert staticcall IERC721(_nftAddr).ownerOf(nftTokenId) == self # dev: nft not returned

    # remove approvals
    if amountA != 0:
        assert extcall IERC20(_tokenA).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed
    if amountB != 0:
        assert extcall IERC20(_tokenB).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    # TODO: perform housekeeping
    # inputs: _tokenA, _tokenB, addedTokenA, addedTokenB

    log ConcentratedLiquidityAdded(
        nftTokenId = nftTokenId,
        pool = _pool,
        tokenA = _tokenA,
        amountA = addedTokenA,
        tokenB = _tokenB,
        amountB = addedTokenB,
        liqAdded = liqAdded,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return liqAdded, addedTokenA, addedTokenB, nftTokenId


####################
# Remove Liquidity #
####################


@nonreentrant
@external
def removeLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _lpAmount: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
) -> (uint256, uint256, uint256):
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.LIQUIDITY, [_tokenA, _tokenB], [_legoId], cd)

    # remove liquidity via lego partner
    amountAReceived: uint256 = 0
    amountBReceived: uint256 = 0
    lpAmountBurned: uint256 = 0
    lpAmount: uint256 = self._getAmountAndApprove(_lpToken, _lpAmount, cd.legoAddr)
    amountAReceived, amountBReceived, lpAmountBurned = extcall LegoPartner(cd.legoAddr).removeLiquidity(_pool, _tokenA, _tokenB, _lpToken, lpAmount, _minAmountA, _minAmountB, self)
    assert extcall IERC20(_lpToken).approve(cd.legoAddr, 0, default_return_value=True) # dev: approval failed

    # TODO: perform housekeeping
    # inputs: _tokenA, _tokenB, amountAReceived, amountBReceived

    log LiquidityRemoved(
        pool = _pool,
        tokenA = _tokenA,
        amountAReceived = amountAReceived,
        tokenB = _tokenB,
        amountBReceived = amountBReceived,
        lpToken = _lpToken,
        lpAmountBurned = lpAmountBurned,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return amountAReceived, amountBReceived, lpAmountBurned


@nonreentrant
@external
def removeLiquidityConcentrated(
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
    cd: CoreData = self._getCoreData(_legoId)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.LIQUIDITY, [_tokenA, _tokenB], [_legoId], cd)

    # must have nft liq position
    assert _nftAddr != empty(address) # dev: invalid nft addr
    assert _nftTokenId != 0 # dev: invalid nft token id
    extcall IERC721(_nftAddr).safeTransferFrom(self, cd.legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # remove liquidity via lego partner
    amountAReceived: uint256 = 0
    amountBReceived: uint256 = 0
    liqRemoved: uint256 = 0
    isDepleted: bool = False
    amountAReceived, amountBReceived, liqRemoved, isDepleted = extcall LegoPartner(cd.legoAddr).removeLiquidityConcentrated(_nftTokenId, _pool, _tokenA, _tokenB, _liqToRemove, _minAmountA, _minAmountB, self)

    # validate the nft came back (if not depleted)
    if not isDepleted:
        assert staticcall IERC721(_nftAddr).ownerOf(_nftTokenId) == self # dev: nft not returned

    # TODO: perform housekeeping
    # inputs: _tokenA, _tokenB, amountAReceived, amountBReceived

    log ConcentratedLiquidityRemoved(
        nftTokenId = _nftTokenId,
        pool = _pool,
        tokenA = _tokenA,
        amountAReceived = amountAReceived,
        tokenB = _tokenB,
        amountBReceived = amountBReceived,
        liqRemoved = liqRemoved,
        legoId = _legoId,
        legoAddr = cd.legoAddr,
        signer = msg.sender,
        isSignerAgent = cd.isSignerAgent,
    )
    return amountAReceived, amountBReceived, liqRemoved, isDepleted


# #################
# # Claim Rewards #
# #################


# @nonreentrant
# @external
# def claimRewards(
#     _legoId: uint256,
#     _market: address = empty(address),
#     _rewardToken: address = empty(address),
#     _rewardAmount: uint256 = max_value(uint256),
#     _proof: bytes32 = empty(bytes32),
# ):
#     cd: CoreData = self._getCoreData()
#     isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.CLAIM_REWARDS, [_rewardToken], [_legoId], cd)

#     # get lego addr
#     legoAddr: address = staticcall LegoRegistry(cd.legoRegistry).getLegoAddr(_legoId)
#     assert legoAddr != empty(address) # dev: invalid lego

#     # make sure lego has access to claim rewards
#     self._checkLegoAccessForAction(legoAddr)

#     # pre reward balance
#     preRewardBalance: uint256 = 0
#     if _rewardToken != empty(address):
#         preRewardBalance = staticcall IERC20(_rewardToken).balanceOf(self)

#     # claim rewards
#     extcall LegoCommon(legoAddr).claimRewards(self, _market, _rewardToken, _rewardAmount, _proof)

#     # post reward balance
#     postRewardBalance: uint256 = 0
#     if _rewardToken != empty(address):
#         postRewardBalance = staticcall IERC20(_rewardToken).balanceOf(self)
#     rewardAmount: uint256 = postRewardBalance - preRewardBalance

#     # handle tx fees
#     if isSignerAgent:
#         self._handleTransactionFees(ActionType.CLAIM_REWARDS, _rewardToken, rewardAmount, cd.priceSheets, cd.agentFactory)

#     usdValue: uint256 = 0
#     if rewardAmount != 0:
#         usdValue = staticcall OracleRegistry(cd.oracleRegistry).getUsdValue(_rewardToken, rewardAmount)
#     log UserWalletRewardsClaimed(signer=msg.sender, market=_market, rewardToken=_rewardToken, rewardAmount=rewardAmount, usdValue=usdValue, proof=_proof, legoId=_legoId, legoAddr=legoAddr, isSignerAgent=isSignerAgent)


# ##################
# # Transfer Funds #
# ##################


# @nonreentrant
# @external
# def transferFunds(
#     _recipient: address,
#     _amount: uint256 = max_value(uint256),
#     _asset: address = empty(address),
# ) -> (uint256, uint256):
#     cd: CoreData = self._getCoreData()
#     isSignerAgent: bool = self._checkPermsAndHandleSubs(msg.sender, ActionType.TRANSFER, [_asset], [], cd)
#     return self._transferFunds(msg.sender, _recipient, _amount, _asset, isSignerAgent, cd)


# @internal
# def _transferFunds(
#     _signer: address,
#     _recipient: address,
#     _amount: uint256,
#     _asset: address,
#     _isSignerAgent: bool,
#     _cd: CoreData,
# ) -> (uint256, uint256):
#     transferAmount: uint256 = 0
#     usdValue: uint256 = 0

#     # validate recipient
#     if _recipient != _cd.owner:
#         assert staticcall WalletConfig(_cd.walletConfig).canTransferToRecipient(_recipient) # dev: recipient not allowed

#     # handle eth
#     if _asset == empty(address):
#         transferAmount = min(_amount, self.balance)
#         assert transferAmount != 0 # dev: nothing to transfer
#         send(_recipient, transferAmount)
#         usdValue = staticcall OracleRegistry(_cd.oracleRegistry).getEthUsdValue(transferAmount)

#     # erc20 tokens
#     else:

#         # check if vault token of trial funds asset
#         isTrialFundsVaultToken: bool = self._isTrialFundsVaultToken(_asset, _cd.trialFundsAsset, _cd.legoRegistry)
#         transferAmount = staticcall WalletConfig(_cd.walletConfig).getAvailableTxAmount(_asset, _amount, True, _cd)

#         assert extcall IERC20(_asset).transfer(_recipient, transferAmount, default_return_value=True) # dev: transfer failed
#         usdValue = staticcall OracleRegistry(_cd.oracleRegistry).getUsdValue(_asset, transferAmount)

#         # make sure they still have enough trial funds
#         self._checkTrialFundsPostTx(isTrialFundsVaultToken, _cd.trialFundsAsset, _cd.trialFundsInitialAmount, _cd.legoRegistry)

#         # yield tracking -- transferring out vault token
#         extcall WalletConfig(_cd.walletConfig).updateYieldTrackingOnExit(_asset, _cd.legoRegistry)

#     log UserWalletFundsTransferred(signer=_signer, recipient=_recipient, asset=_asset, amount=transferAmount, usdValue=usdValue, isSignerAgent=_isSignerAgent)
#     return transferAmount, usdValue


################
# Wrapped ETH #
################


# eth -> weth


@nonreentrant
@payable
@external
def convertEthToWeth(_amount: uint256 = max_value(uint256)) -> uint256:
    weth: address = WETH
    cd: CoreData = self._getCoreData(0)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.WETH_WRAP, [weth], [], cd)

    # convert eth to weth
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).deposit(value=amount)

    # TODO: perform housekeeping

    log EthWrapped(amount=amount, paidEth=msg.value, weth=weth, signer=msg.sender, isSignerAgent=cd.isSignerAgent)
    return amount


# weth -> eth


@nonreentrant
@external
def convertWethToEth(_amount: uint256 = max_value(uint256)) -> uint256:
    weth: address = WETH
    cd: CoreData = self._getCoreData(0)
    cd.isSignerAgent = self._checkPermsAndHandleSubs(msg.sender, ActionType.WETH_WRAP, [weth], [], cd)

    # convert weth to eth
    amount: uint256 = self._getAmountAndApprove(weth, _amount, empty(address)) # nothing to approve
    extcall WethContract(weth).withdraw(amount)

    # TODO: perform housekeeping

    log WethUnwrapped(amount=amount, weth=weth, signer=msg.sender, isSignerAgent=cd.isSignerAgent)
    return amount


#############
# Utilities #
#############


@internal
def _getAmountAndApprove(_token: address, _amount: uint256, _legoAddr: address) -> uint256:
    if _amount == 0:
        return 0
    amount: uint256 = min(_amount, staticcall IERC20(_token).balanceOf(self))
    assert amount != 0 # dev: no balance for _token
    if _legoAddr != empty(address):
        assert extcall IERC20(_token).approve(_legoAddr, amount, default_return_value=True) # dev: approval failed
    return amount


@view
@internal
def _getCoreData(_legoId: uint256) -> CoreData:
    undyHq: address = UNDY_HQ
    legoRegistry: address = staticcall AddyRegistry(undyHq).getAddy(LEGO_REGISTRY_ID)

    # lego details
    legoAddr: address = empty(address)
    if _legoId != 0:
        legoAddr = staticcall LegoRegistry(legoRegistry).getLegoAddr(_legoId)
        assert legoAddr != empty(address) # dev: invalid lego

    walletConfig: address = self.walletConfig
    return CoreData(
        legoAddr = legoAddr,
        owner = staticcall WalletConfig(walletConfig).owner(),
        isSignerAgent = False,
        wallet = self,
        walletConfig = walletConfig,
        undyHq = undyHq,
        agentFactory = staticcall AddyRegistry(undyHq).getAddy(AGENT_FACTORY_ID),
        legoRegistry = legoRegistry,
        priceSheets = staticcall AddyRegistry(undyHq).getAddy(PRICE_SHEETS_ID),
        trialFundsAsset = self.trialFundsAsset,
        trialFundsInitialAmount = self.trialFundsInitialAmount,
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

    # make sure lego can perform this action
    # TODO: only call this if specific action type
    self._checkLegoAccessForAction(_cd.legoAddr)

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
    _cd: CoreData,
) -> uint256:
    if _amount == 0 or _asset == empty(address):
        return 0

    # pay ambassador yield bonus first (we do early return once we get into tx fees)
    ambassadorRecipient: address = empty(address)
    if _action == ActionType.EARN:
        ambassadorRecipient = self._getAmbassadorProceedsAddr(empty(address))
        extcall AgentFactory(_cd.agentFactory).payAmbassadorYieldBonus(ambassadorRecipient, _asset, _amount)

    # get transaction fees
    fee: uint256 = 0
    protocolRecipient: address = empty(address)
    ambassadorRatio: uint256 = 0
    fee, protocolRecipient, ambassadorRatio = staticcall PriceSheets(_cd.priceSheets).getTransactionFeeDataWithAmbassadorRatio(self, _action)
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
    targetAddr, accessAbi, numInputs = staticcall LegoPartner(_legoAddr).getAccessForLego(self)

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
def clawBackTrialFunds() -> bool:
    cd: CoreData = self._getCoreData(0)
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
        na: uint256 = 0
        na2: address = empty(address)
        underlyingAmount: uint256 = 0
        na, na2, underlyingAmount = self._withdrawFromYield(v.legoId, v.vaultAddr, max_value(uint256), msg.sender, True, cd)

        # recover funds
        transferAmount: uint256 = min(underlyingAmount, targetRecoveryAmount)
        assert extcall IERC20(cd.trialFundsAsset).transfer(cd.agentFactory, transferAmount, default_return_value=True) # dev: trial funds transfer failed
        amountRecovered += transferAmount
        targetRecoveryAmount -= transferAmount

        # reached target recovery amount, deposit any extra balance back lego
        if targetRecoveryAmount == 0:
            depositAmount: uint256 = min(underlyingAmount - transferAmount, staticcall IERC20(cd.trialFundsAsset).balanceOf(self))
            if depositAmount != 0:
                self._depositForYield(v.legoId, cd.trialFundsAsset, v.vaultAddr, depositAmount, msg.sender, True, cd)
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
    cd: CoreData = self._getCoreData(0)
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

    # finish migration of new wallet
    newWalletConfig: address = staticcall UserWallet(_newWallet).walletConfig()
    assert extcall WalletConfig(newWalletConfig).finishMigrationIn(_whitelistToMigrate, assetsMigrated, vaultTokensMigrated) # dev: migration failed
    
    # update yield tracking for this wallet
    if len(vaultTokensMigrated) != 0:
        for vaultToken: address in vaultTokensMigrated:
            extcall WalletConfig(cd.walletConfig).updateYieldTrackingOnExit(vaultToken, cd.legoRegistry)

    return True
