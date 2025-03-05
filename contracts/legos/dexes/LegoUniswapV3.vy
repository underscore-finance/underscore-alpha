# @version 0.4.0

implements: IUniswapV3Callback
implements: LegoCommon
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from ethereum.ercs import IERC721
from ethereum.ercs import IERC20Detailed
from interfaces import LegoCommon

# `getSwapAmountOut()` and `getSwapAmountIn()` cannot be view functions, sadly
# keeping here to uncomment to test all other functions
# implements: LegoDex
# from interfaces import LegoDex

interface UniV3Pool:
    def slot0() -> (uint160, int24, uint16, uint16, uint16, uint8, bool): view
    def swap(_recipient: address, _zeroForOne: bool, _amountSpecified: int256, _sqrtPriceLimitX96: uint160, _data: Bytes[256]) -> (int256, int256): nonpayable
    def liquidity() -> uint128: view
    def tickSpacing() -> int24: view
    def token0() -> address: view
    def token1() -> address: view
    def fee() -> uint24: view

interface UniV3NftPositionManager:
    def increaseLiquidity(_params: IncreaseLiquidityParams) -> (uint128, uint256, uint256): nonpayable
    def decreaseLiquidity(_params: DecreaseLiquidityParams) -> (uint256, uint256): nonpayable
    def mint(_params: MintParams) -> (uint256, uint128, uint256, uint256): nonpayable
    def collect(_params: CollectParams) -> (uint256, uint256): nonpayable
    def positions(_tokenId: uint256) -> PositionData: view
    def burn(_tokenId: uint256): nonpayable

interface UniV3Quoter:
    def quoteExactOutputSingle(_params: QuoteExactOutputSingleParams) -> (uint256, uint160, uint32, uint256): nonpayable
    def quoteExactInputSingle(_params: QuoteExactInputSingleParams) -> (uint256, uint160, uint32, uint256): nonpayable
    def quoteExactInput(_path: Bytes[1024], _amountIn: uint256) -> uint256: nonpayable
  
interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface IUniswapV3Callback:
    def uniswapV3SwapCallback(_amount0Delta: int256, _amount1Delta: int256, _data: Bytes[256]): nonpayable

interface UniV3Factory:
    def getPool(_tokenA: address, _tokenB: address, _fee: uint24) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct QuoteExactInputSingleParams:
    tokenIn: address
    tokenOut: address
    amountIn: uint256
    fee: uint24
    sqrtPriceLimitX96: uint160

struct QuoteExactOutputSingleParams:
    tokenIn: address
    tokenOut: address
    amount: uint256
    fee: uint24
    sqrtPriceLimitX96: uint160

struct BestPool:
    pool: address
    fee: uint256
    liquidity: uint256
    numCoins: uint256
    legoId: uint256

struct MintParams:
    token0: address
    token1: address
    fee: uint24
    tickLower: int24
    tickUpper: int24
    amount0Desired: uint256
    amount1Desired: uint256
    amount0Min: uint256
    amount1Min: uint256
    recipient: address
    deadline: uint256

struct IncreaseLiquidityParams:
    tokenId: uint256
    amount0Desired: uint256
    amount1Desired: uint256
    amount0Min: uint256
    amount1Min: uint256
    deadline: uint256

struct DecreaseLiquidityParams:
    tokenId: uint256
    liquidity: uint128
    amount0Min: uint256
    amount1Min: uint256
    deadline: uint256

struct CollectParams:
    tokenId: uint256
    recipient: address
    amount0Max: uint128
    amount1Max: uint128

struct PositionData:
    nonce: uint96
    operator: address
    token0: address
    token1: address
    fee: uint24
    tickLower: int24
    tickUpper: int24
    liquidity: uint128
    feeGrowthInside0LastX128: uint256
    feeGrowthInside1LastX128: uint256
    tokensOwed0: uint128
    tokensOwed1: uint128

struct PoolSwapData:
    pool: address
    tokenIn: address
    amountIn: uint256

event UniswapV3Swap:
    sender: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    amountIn: uint256
    amountOut: uint256
    usdValue: uint256
    numTokens: uint256
    recipient: address

event UniswapV3SwapInPool:
    sender: indexed(address)
    pool: indexed(address)
    tokenIn: indexed(address)
    tokenOut: address
    amountIn: uint256
    amountOut: uint256
    usdValue: uint256
    recipient: address

event UniswapV3LiquidityAdded:
    sender: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    amountA: uint256
    amountB: uint256
    liquidityAdded: uint256
    nftTokenId: uint256
    usdValue: uint256
    recipient: address

event UniswapV3LiquidityRemoved:
    sender: address
    pool: indexed(address)
    nftTokenId: uint256
    tokenA: indexed(address)
    tokenB: indexed(address)
    amountA: uint256
    amountB: uint256
    liquidityRemoved: uint256
    usdValue: uint256
    recipient: address

event UniV3FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event UniV3CoreRouterPoolSet:
    pool: indexed(address)

event UniV3NftRecovered:
    collection: indexed(address)
    nftTokenId: uint256
    recipient: indexed(address)

event UniswapV3LegoIdSet:
    legoId: uint256

event UniswapV3Activated:
    isActivated: bool

# transient
coreRouterPool: public(address)
poolSwapData: transient(PoolSwapData)

# uni
UNIV3_FACTORY: public(immutable(address))
UNIV3_NFT_MANAGER: public(immutable(address))
UNIV3_QUOTER: public(immutable(address))

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

FEE_TIERS: constant(uint24[4]) = [100, 500, 3000, 10000] # 0.01%, 0.05%, 0.3%, 1%
MIN_SQRT_RATIO_PLUS_ONE: constant(uint160) = 4295128740
MAX_SQRT_RATIO_MINUS_ONE: constant(uint160) = 1461446703485210103287273052203988822378723970341
TICK_LOWER: constant(int24) = -887272
TICK_UPPER: constant(int24) = 887272
ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UnderscoreErc721"
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
UNISWAP_Q96: constant(uint256) = 2 ** 96  # uniswap's fixed point scaling factor
MAX_TOKEN_PATH: constant(uint256) = 5

@deploy
def __init__(
    _uniswapV3Factory: address,
    _uniNftPositionManager: address,
    _uniV3Quoter: address,
    _addyRegistry: address,
    _coreRouterPool: address,
):
    assert empty(address) not in [_uniswapV3Factory, _uniNftPositionManager, _uniV3Quoter, _addyRegistry, _coreRouterPool] # dev: invalid addrs
    UNIV3_FACTORY = _uniswapV3Factory
    UNIV3_NFT_MANAGER = _uniNftPositionManager
    UNIV3_QUOTER = _uniV3Quoter
    ADDY_REGISTRY = _addyRegistry
    self.coreRouterPool = _coreRouterPool
    self.isActivated = True
    gov.__init__(_addyRegistry)


@view
@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    # must implement method for safe NFT transfers
    assert _data == ERC721_RECEIVE_DATA # dev: did not receive from within Underscore wallet
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [UNIV3_FACTORY, UNIV3_NFT_MANAGER, UNIV3_QUOTER]


@view
@external
def getAccessForLego(_user: address) -> (address, String[64], uint256):
    return empty(address), empty(String[64]), 0


########
# Swap #
########


@external
def swapTokens(
    _amountIn: uint256,
    _minAmountOut: uint256,
    _tokenPath: DynArray[address, MAX_TOKEN_PATH],
    _poolPath: DynArray[address, MAX_TOKEN_PATH - 1],
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated

    # validate inputs
    numTokens: uint256 = len(_tokenPath)
    numPools: uint256 = len(_poolPath)
    assert numTokens >= 2 # dev: invalid path
    assert numPools == numTokens - 1 # dev: invalid path

    # get first token and last token
    tokenIn: address = _tokenPath[0]
    tokenOut: address = _tokenPath[numTokens - 1]

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(tokenIn).balanceOf(self)

    # transfer deposit asset to this contract
    initialAmountIn: uint256 = min(_amountIn, staticcall IERC20(tokenIn).balanceOf(msg.sender))
    assert initialAmountIn != 0 # dev: nothing to transfer
    assert extcall IERC20(tokenIn).transferFrom(msg.sender, self, initialAmountIn, default_return_value=True) # dev: transfer failed
    initialAmountIn = min(initialAmountIn, staticcall IERC20(tokenIn).balanceOf(self))

    uniswapV3Factory: address = UNIV3_FACTORY

    # iterate through swap routes
    tempAmountIn: uint256 = initialAmountIn
    for i: uint256 in range(numTokens - 1, bound=MAX_TOKEN_PATH):
        tempTokenIn: address = _tokenPath[i]
        tempTokenOut: address = _tokenPath[i + 1]
        tempPool: address = _poolPath[i]

        # transfer to self (or to recipient if last swap)
        recipient: address = _recipient
        if i < numTokens - 2:
            recipient = self

        # swap
        tempAmountIn = self._swapTokensInPool(tempPool, tempTokenIn, tempTokenOut, tempAmountIn, recipient, uniswapV3Factory)

    # final amount
    toAmount: uint256 = tempAmountIn
    assert toAmount >= _minAmountOut # dev: min amount out not met

    # refund if full swap didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(tokenIn).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(tokenIn).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        initialAmountIn -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(tokenIn, initialAmountIn, tokenOut, toAmount, True, _oracleRegistry)
    log UniswapV3Swap(msg.sender, tokenIn, tokenOut, initialAmountIn, toAmount, usdValue, numTokens, _recipient)
    return initialAmountIn, toAmount, refundAssetAmount, usdValue


# swap in pool


@internal
def _swapTokensInPool(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _recipient: address,
    _uniswapV3Factory: address,
) -> uint256:
    tokens: address[2] = [staticcall UniV3Pool(_pool).token0(), staticcall UniV3Pool(_pool).token1()]
    assert _tokenIn in tokens # dev: invalid tokenIn
    assert _tokenOut in tokens # dev: invalid tokenOut
    assert _tokenIn != _tokenOut # dev: invalid tokens

    # verify actual uniswap v3 pool
    assert staticcall UniV3Factory(_uniswapV3Factory).getPool(_tokenIn, _tokenOut, staticcall UniV3Pool(_pool).fee()) == _pool # dev: invalid pool

    # save in transient storage (for use in callback)
    self.poolSwapData = PoolSwapData(
        pool=_pool,
        tokenIn=_tokenIn,
        amountIn=_amountIn,
    )

    zeroForOne: bool = _tokenIn == tokens[0]
    sqrtPriceLimitX96: uint160 = MAX_SQRT_RATIO_MINUS_ONE
    if zeroForOne:
        sqrtPriceLimitX96 = MIN_SQRT_RATIO_PLUS_ONE

    # perform swap
    amount0: int256 = 0
    amount1: int256 = 0
    amount0, amount1 = extcall UniV3Pool(_pool).swap(_recipient, zeroForOne, convert(_amountIn, int256), sqrtPriceLimitX96, b"")

    toAmount: uint256 = 0
    if zeroForOne:
        toAmount = convert(-amount1, uint256)
    else:
        toAmount = convert(-amount0, uint256)
    
    assert toAmount != 0 # dev: no tokens swapped
    return toAmount


# callback


@external
def uniswapV3SwapCallback(_amount0Delta: int256, _amount1Delta: int256, _data: Bytes[256]):
    poolSwapData: PoolSwapData = self.poolSwapData
    assert msg.sender == poolSwapData.pool # dev: no perms

    # transfer tokens to pool
    assert extcall IERC20(poolSwapData.tokenIn).transfer(poolSwapData.pool, poolSwapData.amountIn, default_return_value=True) # dev: transfer failed
    self.poolSwapData = empty(PoolSwapData)


#################
# Add Liquidity #
#################


@external
def addLiquidity(
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _tickLower: int24,
    _tickUpper: int24,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated

    # validate tokens
    tokens: address[2] = [staticcall UniV3Pool(_pool).token0(), staticcall UniV3Pool(_pool).token1()]
    assert _tokenA in tokens # dev: invalid tokenA
    assert _tokenB in tokens # dev: invalid tokenB
    assert _tokenA != _tokenB # dev: invalid tokens

    # pre balances
    preLegoBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    preLegoBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)

    # token a
    transferAmountA: uint256 = min(_amountA, staticcall IERC20(_tokenA).balanceOf(msg.sender))
    assert transferAmountA != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, transferAmountA, default_return_value=True) # dev: transfer failed
    liqAmountA: uint256 = min(transferAmountA, staticcall IERC20(_tokenA).balanceOf(self))

    # token b
    transferAmountB: uint256 = min(_amountB, staticcall IERC20(_tokenB).balanceOf(msg.sender))
    assert transferAmountB != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, transferAmountB, default_return_value=True) # dev: transfer failed
    liqAmountB: uint256 = min(transferAmountB, staticcall IERC20(_tokenB).balanceOf(self))

    # approvals
    nftPositionManager: address = UNIV3_NFT_MANAGER
    assert extcall IERC20(_tokenA).approve(nftPositionManager, liqAmountA, default_return_value=True) # dev: approval failed
    assert extcall IERC20(_tokenB).approve(nftPositionManager, liqAmountB, default_return_value=True) # dev: approval failed

    # organized the index of tokens
    token0: address = _tokenA
    token1: address = _tokenB
    amount0: uint256 = liqAmountA
    amount1: uint256 = liqAmountB
    minAmount0: uint256 = _minAmountA
    minAmount1: uint256 = _minAmountB
    if tokens[0] != _tokenA:
        token0 = _tokenB
        token1 = _tokenA
        amount0 = liqAmountB
        amount1 = liqAmountA
        minAmount0 = _minAmountB
        minAmount1 = _minAmountA

    # add liquidity
    nftTokenId: uint256 = _nftTokenId
    liquidityAdded: uint256 = 0
    liquidityAddedInt128: uint128 = 0
    if _nftTokenId == 0:
        nftTokenId, liquidityAddedInt128, amount0, amount1 = self._mintNewPosition(nftPositionManager, _pool, token0, token1, _tickLower, _tickUpper, amount0, amount1, minAmount0, minAmount1, _recipient)
    else:
        liquidityAddedInt128, amount0, amount1 = self._increaseExistingPosition(nftPositionManager, _nftTokenId, amount0, amount1, minAmount0, minAmount1, _recipient)

    liquidityAdded = convert(liquidityAddedInt128, uint256)
    assert liquidityAdded != 0 # dev: no liquidity added

    # reset approvals
    assert extcall IERC20(_tokenA).approve(nftPositionManager, 0, default_return_value=True) # dev: approval failed
    assert extcall IERC20(_tokenB).approve(nftPositionManager, 0, default_return_value=True) # dev: approval failed

    # refund if full liquidity was not added
    currentLegoBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    refundAssetAmountA: uint256 = 0
    if currentLegoBalanceA > preLegoBalanceA:
        refundAssetAmountA = currentLegoBalanceA - preLegoBalanceA
        assert extcall IERC20(_tokenA).transfer(msg.sender, refundAssetAmountA, default_return_value=True) # dev: transfer failed

    currentLegoBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)
    refundAssetAmountB: uint256 = 0
    if currentLegoBalanceB > preLegoBalanceB:
        refundAssetAmountB = currentLegoBalanceB - preLegoBalanceB
        assert extcall IERC20(_tokenB).transfer(msg.sender, refundAssetAmountB, default_return_value=True) # dev: transfer failed

    # a/b amounts
    liqAmountA = amount0
    liqAmountB = amount1
    if tokens[0] != _tokenA:
        liqAmountA = amount1
        liqAmountB = amount0

    usdValue: uint256 = self._getUsdValue(_tokenA, liqAmountA, _tokenB, liqAmountB, False, _oracleRegistry)
    log UniswapV3LiquidityAdded(msg.sender, _tokenA, _tokenB, liqAmountA, liqAmountB, liquidityAdded, nftTokenId, usdValue, _recipient)
    return liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId


@internal
def _mintNewPosition(
    _nftPositionManager: address,
    _pool: address,
    _token0: address,
    _token1: address,
    _tickLower: int24,
    _tickUpper: int24,
    _amount0: uint256,
    _amount1: uint256,
    _minAmount0: uint256,
    _minAmount1: uint256,
    _recipient: address,
) -> (uint256, uint128, uint256, uint256):
    tickLower: int24 = 0
    tickUpper: int24 = 0
    tickLower, tickUpper = self._getTicks(_pool, _tickLower, _tickUpper)

    # mint new position
    params: MintParams = MintParams(
        token0=_token0,
        token1=_token1,
        fee=staticcall UniV3Pool(_pool).fee(),
        tickLower=tickLower,
        tickUpper=tickUpper,
        amount0Desired=_amount0,
        amount1Desired=_amount1,
        amount0Min=_minAmount0,
        amount1Min=_minAmount1,
        recipient=_recipient,
        deadline=block.timestamp,
    )
    return extcall UniV3NftPositionManager(_nftPositionManager).mint(params)


@view
@internal
def _getTicks(_pool: address, _tickLower: int24, _tickUpper: int24) -> (int24, int24):
    tickSpacing: int24 = 0
    if _tickLower == min_value(int24) or _tickUpper == max_value(int24):
        tickSpacing = staticcall UniV3Pool(_pool).tickSpacing()

    tickLower: int24 = _tickLower
    if _tickLower == min_value(int24):
        tickLower = (TICK_LOWER // tickSpacing) * tickSpacing

    tickUpper: int24 = _tickUpper
    if _tickUpper == max_value(int24):
        tickUpper = (TICK_UPPER // tickSpacing) * tickSpacing

    return tickLower, tickUpper


@internal
def _increaseExistingPosition(
    _nftPositionManager: address,
    _tokenId: uint256,
    _amount0: uint256,
    _amount1: uint256,
    _minAmount0: uint256,
    _minAmount1: uint256,
    _recipient: address,
) -> (uint128, uint256, uint256):
    assert staticcall IERC721(_nftPositionManager).ownerOf(_tokenId) == self # dev: nft not here

    liquidityAddedInt128: uint128 = 0
    amount0: uint256 = 0
    amount1: uint256 = 0
    params: IncreaseLiquidityParams = IncreaseLiquidityParams(
        tokenId=_tokenId,
        amount0Desired=_amount0,
        amount1Desired=_amount1,
        amount0Min=_minAmount0,
        amount1Min=_minAmount1,
        deadline=block.timestamp,
    )
    liquidityAddedInt128, amount0, amount1 = extcall UniV3NftPositionManager(_nftPositionManager).increaseLiquidity(params)

    # collect fees (if applicable) -- must be done before transferring nft
    positionData: PositionData = staticcall UniV3NftPositionManager(_nftPositionManager).positions(_tokenId)
    self._collectFees(_nftPositionManager, _tokenId, _recipient, positionData)

    # transfer nft to recipient
    extcall IERC721(_nftPositionManager).safeTransferFrom(self, _recipient, _tokenId)

    return liquidityAddedInt128, amount0, amount1


@internal
def _collectFees(_nftPositionManager: address, _tokenId: uint256, _recipient: address, _positionData: PositionData) -> (uint256, uint256):
    if _positionData.tokensOwed0 == 0 and _positionData.tokensOwed1 == 0:
        return 0, 0

    params: CollectParams = CollectParams(
        tokenId=_tokenId,
        recipient=_recipient,
        amount0Max=max_value(uint128),
        amount1Max=max_value(uint128),
    )
    return extcall UniV3NftPositionManager(_nftPositionManager).collect(params)


####################
# Remove Liquidity #
####################


@external
def removeLiquidity(
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _liqToRemove: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256, uint256, bool):
    assert self.isActivated # dev: not activated

    # make sure nft is here
    nftPositionManager: address = UNIV3_NFT_MANAGER
    assert staticcall IERC721(nftPositionManager).ownerOf(_nftTokenId) == self # dev: nft not here

    # get position data
    positionData: PositionData = staticcall UniV3NftPositionManager(nftPositionManager).positions(_nftTokenId)
    originalLiquidity: uint128 = positionData.liquidity

    # validate tokens
    tokens: address[2] = [positionData.token0, positionData.token1]
    assert _tokenA in tokens # dev: invalid tokenA
    assert _tokenB in tokens # dev: invalid tokenB
    assert _tokenA != _tokenB # dev: invalid tokens

    # organized the index of tokens
    minAmount0: uint256 = _minAmountA
    minAmount1: uint256 = _minAmountB
    if _tokenA != tokens[0]:
        minAmount0 = _minAmountB
        minAmount1 = _minAmountA

    # decrease liquidity
    liqToRemove: uint256 = min(_liqToRemove, convert(positionData.liquidity, uint256))
    assert liqToRemove != 0 # dev: no liquidity to remove

    params: DecreaseLiquidityParams = DecreaseLiquidityParams(
        tokenId=_nftTokenId,
        liquidity=convert(liqToRemove, uint128),
        amount0Min=minAmount0,
        amount1Min=minAmount1,
        deadline=block.timestamp,
    )
    amount0: uint256 = 0
    amount1: uint256 = 0
    amount0, amount1 = extcall UniV3NftPositionManager(nftPositionManager).decreaseLiquidity(params)
    assert amount0 != 0 and amount1 != 0 # dev: no liquidity removed

    # a/b amounts
    amountA: uint256 = amount0
    amountB: uint256 = amount1
    if _tokenA != tokens[0]:
        amountA = amount1
        amountB = amount0

    # get latest position data -- collect withdrawn tokens AND any fees (if applicable)
    positionData = staticcall UniV3NftPositionManager(nftPositionManager).positions(_nftTokenId)
    self._collectFees(nftPositionManager, _nftTokenId, _recipient, positionData)

    # burn nft (if applicable)
    isDepleted: bool = False
    if positionData.liquidity == 0:
        isDepleted = True
        extcall UniV3NftPositionManager(nftPositionManager).burn(_nftTokenId)

    # transfer nft to recipient
    else:
        extcall IERC721(nftPositionManager).safeTransferFrom(self, _recipient, _nftTokenId)

    usdValue: uint256 = self._getUsdValue(_tokenA, amountA, _tokenB, amountB, False, _oracleRegistry)
    liquidityRemoved: uint256 = convert(originalLiquidity - positionData.liquidity, uint256)
    log UniswapV3LiquidityRemoved(msg.sender, _pool, _nftTokenId, _tokenA, _tokenB, amountA, amountB, liquidityRemoved, usdValue, _recipient)
    return amountA, amountB, usdValue, liquidityRemoved, 0, isDepleted


#################
# Claim Rewards #
#################


@external
def claimRewards(
    _user: address,
    _market: address,
    _rewardToken: address,
    _rewardAmount: uint256,
    _proof: bytes32,
):
    pass


@view
@external
def hasClaimableRewards(_user: address) -> bool:
    return False


#############
# Utilities #
#############


@view
@external
def getLpToken(_pool: address) -> address:
    # no lp tokens for uniswap v3
    return empty(address)


@view
@external
def getPoolForLpToken(_lpToken: address) -> address:
    # no lp tokens for uniswap v3
    return empty(address)


@view
@external
def getCoreRouterPool() -> address:
    return self.coreRouterPool


@view
@external
def getDeepestLiqPool(_tokenA: address, _tokenB: address) -> BestPool:
    bestPoolAddr: address = empty(address)
    bestFeeTier: uint24 = 0
    bestPoolAddr, bestFeeTier = self._getDeepestLiqPool(_tokenA, _tokenB)

    if bestPoolAddr == empty(address):
        return empty(BestPool)

    # get token balances
    tokenABal: uint256 = staticcall IERC20(_tokenA).balanceOf(bestPoolAddr)
    tokenBBal: uint256 = staticcall IERC20(_tokenB).balanceOf(bestPoolAddr)

    return BestPool(
        pool=bestPoolAddr,
        fee=convert(bestFeeTier // 100, uint256), # normalize to have 100_00 denominator
        liquidity=tokenABal + tokenBBal, # not exactly "liquidity" but this comparable to "reserves"
        numCoins=2,
        legoId=self.legoId,
    )


# annoying that this cannot be view function, thanks uni v3
@external
def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> (address, uint256):
    bestPoolAddr: address = empty(address)
    bestFeeTier: uint24 = 0
    bestPoolAddr, bestFeeTier = self._getDeepestLiqPool(_tokenIn, _tokenOut)

    if bestPoolAddr == empty(address):
        return empty(address), 0

    amountOut: uint256 = 0
    na1: uint160 = 0
    na2: uint32 = 0
    na3: uint256 = 0
    amountOut, na1, na2, na3 = extcall UniV3Quoter(UNIV3_QUOTER).quoteExactInputSingle(
        QuoteExactInputSingleParams(
            tokenIn=_tokenIn,
            tokenOut=_tokenOut,
            amountIn=_amountIn,
            fee=bestFeeTier,
            sqrtPriceLimitX96=0,
        )
    )
    return bestPoolAddr, amountOut


# annoying that this cannot be view function, thanks uni v3
@external
def getSwapAmountOut(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
) -> uint256:
    amountOut: uint256 = 0
    na1: uint160 = 0
    na2: uint32 = 0
    na3: uint256 = 0
    amountOut, na1, na2, na3 = extcall UniV3Quoter(UNIV3_QUOTER).quoteExactInputSingle(
        QuoteExactInputSingleParams(
            tokenIn=_tokenIn,
            tokenOut=_tokenOut,
            amountIn=_amountIn,
            fee=staticcall UniV3Pool(_pool).fee(),
            sqrtPriceLimitX96=0,
        )
    )
    return amountOut


# annoying that this cannot be view function, thanks uni v3
@external
def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (address, uint256):
    bestPoolAddr: address = empty(address)
    bestFeeTier: uint24 = 0
    bestPoolAddr, bestFeeTier = self._getDeepestLiqPool(_tokenIn, _tokenOut)

    if bestPoolAddr == empty(address):
        return empty(address), 0

    amountIn: uint256 = 0
    na1: uint160 = 0
    na2: uint32 = 0
    na3: uint256 = 0
    amountIn, na1, na2, na3 = extcall UniV3Quoter(UNIV3_QUOTER).quoteExactOutputSingle(
        QuoteExactOutputSingleParams(
            tokenIn=_tokenIn,
            tokenOut=_tokenOut,
            amount=_amountOut,
            fee=bestFeeTier,
            sqrtPriceLimitX96=0,
        )
    )
    return bestPoolAddr, amountIn


# annoying that this cannot be view function, thanks uni v3
@external
def getSwapAmountIn(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
) -> uint256:
    amountIn: uint256 = 0
    na1: uint160 = 0
    na2: uint32 = 0
    na3: uint256 = 0
    amountIn, na1, na2, na3 = extcall UniV3Quoter(UNIV3_QUOTER).quoteExactOutputSingle(
        QuoteExactOutputSingleParams(
            tokenIn=_tokenIn,
            tokenOut=_tokenOut,
            amount=_amountOut,
            fee=staticcall UniV3Pool(_pool).fee(),
            sqrtPriceLimitX96=0,
        )
    )
    return amountIn


@view
@external
def getAddLiqAmountsIn(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _availAmountA: uint256,
    _availAmountB: uint256,
) -> (uint256, uint256, uint256):
    token0: address = staticcall UniV3Pool(_pool).token0()

    # get correct numerator and denominator
    numerator: uint256 = 0
    denominator: uint256 = 0
    sqrtPriceX96Squared: uint256 = self._getSqrtPriceX96(_pool) ** 2
    if _tokenA == token0:
        numerator = sqrtPriceX96Squared
        denominator = UNISWAP_Q96 ** 2
    else:
        numerator = UNISWAP_Q96 ** 2
        denominator = sqrtPriceX96Squared

    # calculate optimal amounts
    amountA: uint256 = _availAmountA
    amountB: uint256 = _availAmountA * numerator // denominator
    if amountB > _availAmountB:
        maybeAmountA: uint256 = _availAmountB * denominator // numerator
        if maybeAmountA <= _availAmountA:
            amountA = maybeAmountA
            amountB = _availAmountB
    return amountA, amountB, 0


@view
@external
def getRemoveLiqAmountsOut(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpAmount: uint256,
) -> (uint256, uint256):
    token0: address = staticcall UniV3Pool(_pool).token0()

    # calculate expected amounts out
    sqrtPriceX96: uint256 = self._getSqrtPriceX96(_pool)
    amount0Out: uint256 = _lpAmount * UNISWAP_Q96 // sqrtPriceX96
    amount1Out: uint256 = _lpAmount * sqrtPriceX96 // UNISWAP_Q96

    # return amounts out
    if _tokenA == token0:
        return amount0Out, amount1Out
    else:
        return amount1Out, amount0Out


@view
@external
def getPriceUnsafe(_pool: address, _targetToken: address, _oracleRegistry: address = empty(address)) -> uint256:
    token0: address = staticcall UniV3Pool(_pool).token0()
    token1: address = staticcall UniV3Pool(_pool).token1()

    # oracle registry
    oracleRegistry: address = _oracleRegistry
    if _oracleRegistry == empty(address):
        oracleRegistry = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)

    # alt price
    altPrice: uint256 = 0
    if _targetToken == token0:
        altPrice = staticcall OracleRegistry(oracleRegistry).getPrice(token1, False)
    else:
        altPrice = staticcall OracleRegistry(oracleRegistry).getPrice(token0, False)

    # return early if no alt price
    if altPrice == 0:
        return 0

    # price of token0 in token1
    sqrtPriceX96: uint256 = self._getSqrtPriceX96(_pool)
    numerator: uint256 = sqrtPriceX96 ** 2 * EIGHTEEN_DECIMALS
    priceZeroToOne: uint256 = numerator // (UNISWAP_Q96 ** 2)

    # adjust for decimals: price should be in 18 decimals
    decimals0: uint256 = convert(staticcall IERC20Detailed(token0).decimals(), uint256)
    decimals1: uint256 = convert(staticcall IERC20Detailed(token1).decimals(), uint256)
    if decimals0 > decimals1:
        scaleFactor: uint256 = 10 ** (decimals0 - decimals1)
        priceZeroToOne = priceZeroToOne * scaleFactor
    elif decimals1 > decimals0:
        scaleFactor: uint256 = 10 ** (decimals1 - decimals0)
        priceZeroToOne = priceZeroToOne // scaleFactor

    # if _targetToken is token1, make price inverse
    priceToOther: uint256 = priceZeroToOne
    if _targetToken == token1:
        priceToOther = EIGHTEEN_DECIMALS * EIGHTEEN_DECIMALS // priceZeroToOne

    return altPrice * priceToOther // EIGHTEEN_DECIMALS


# internal utils


@view
@internal
def _getDeepestLiqPool(_tokenA: address, _tokenB: address) -> (address, uint24):
    bestPoolAddr: address = empty(address)
    bestFeeTier: uint24 = 0
    bestLiquidity: uint128 = 0

    factory: address = UNIV3_FACTORY
    for i: uint256 in range(4):
        fee: uint24 = FEE_TIERS[i]
        pool: address = staticcall UniV3Factory(factory).getPool(_tokenA, _tokenB, fee)
        if pool == empty(address):
            continue
        liquidity: uint128 = staticcall UniV3Pool(pool).liquidity()
        if liquidity > bestLiquidity:
            bestPoolAddr = pool
            bestFeeTier = fee
            bestLiquidity = liquidity

    return bestPoolAddr, bestFeeTier


@view
@internal
def _getUsdValue(
    _tokenA: address,
    _amountA: uint256,
    _tokenB: address,
    _amountB: uint256,
    _isSwap: bool,
    _oracleRegistry: address,
) -> uint256:
    oracleRegistry: address = _oracleRegistry
    if _oracleRegistry == empty(address):
        oracleRegistry = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)
    usdValueA: uint256 = staticcall OracleRegistry(oracleRegistry).getUsdValue(_tokenA, _amountA)
    usdValueB: uint256 = staticcall OracleRegistry(oracleRegistry).getUsdValue(_tokenB, _amountB)
    if _isSwap:
        return max(usdValueA, usdValueB)
    else:
        return usdValueA + usdValueB


@view
@internal
def _getSqrtPriceX96(_pool: address) -> uint256:
    sqrtPriceX96: uint160 = 0
    tick: int24 = 0
    observationIndex: uint16 = 0
    observationCardinality: uint16 = 0
    observationCardinalityNext: uint16 = 0
    feeProtocol: uint8 = 0
    unlocked: bool = False
    sqrtPriceX96, tick, observationIndex, observationCardinality, observationCardinalityNext, feeProtocol, unlocked = staticcall UniV3Pool(_pool).slot0()
    return convert(sqrtPriceX96, uint256)


####################
# Core Router Pool #
####################


@external
def setCoreRouterPool(_addr: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.coreRouterPool = _addr
    log UniV3CoreRouterPoolSet(_addr)
    return True


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log UniV3FundsRecovered(_asset, _recipient, balance)
    return True


@external
def recoverNft(_collection: address, _nftTokenId: uint256, _recipient: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    if staticcall IERC721(_collection).ownerOf(_nftTokenId) != self:
        return False

    extcall IERC721(_collection).safeTransferFrom(self, _recipient, _nftTokenId)
    log UniV3NftRecovered(_collection, _nftTokenId, _recipient)
    return True


###########
# Lego Id #
###########


@external
def setLegoId(_legoId: uint256) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2) # dev: no perms
    prevLegoId: uint256 = self.legoId
    assert prevLegoId == 0 or prevLegoId == _legoId # dev: invalid lego id
    self.legoId = _legoId
    log UniswapV3LegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log UniswapV3Activated(_shouldActivate)