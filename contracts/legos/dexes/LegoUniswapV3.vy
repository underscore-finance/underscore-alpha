# @version 0.4.0

implements: IUniswapV3Callback
implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from ethereum.ercs import IERC721
from interfaces import LegoDex

interface UniV3NftPositionManager:
    def increaseLiquidity(_params: IncreaseLiquidityParams) -> (uint128, uint256, uint256): nonpayable
    def decreaseLiquidity(_params: DecreaseLiquidityParams) -> (uint256, uint256): nonpayable
    def mint(_params: MintParams) -> (uint256, uint128, uint256, uint256): nonpayable
    def collect(_params: CollectParams) -> (uint256, uint256): nonpayable
    def positions(_tokenId: uint256) -> PositionData: view
    def burn(_tokenId: uint256): nonpayable

interface UniV3Pool:
    def swap(_recipient: address, _zeroForOne: bool, _amountSpecified: int256, _sqrtPriceLimitX96: uint160, _data: Bytes[256]) -> (int256, int256): nonpayable
    def liquidity() -> uint128: view
    def tickSpacing() -> int24: view
    def token0() -> address: view
    def token1() -> address: view
    def fee() -> uint24: view

interface IUniswapV3Callback:
    def uniswapV3SwapCallback(_amount0Delta: int256, _amount1Delta: int256, _data: Bytes[256]): nonpayable

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface UniV3Factory:
    def getPool(_tokenA: address, _tokenB: address, _fee: uint24) -> address: view

interface UniV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct ExactInputSingleParams:
    tokenIn: address
    tokenOut: address
    fee: uint24
    recipient: address
    amountIn: uint256
    amountOutMinimum: uint256
    sqrtPriceLimitX96: uint160

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

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event NftRecovered:
    collection: indexed(address)
    nftTokenId: uint256
    recipient: indexed(address)

event UniswapV3LegoIdSet:
    legoId: uint256

event UniswapV3Activated:
    isActivated: bool

# transient
poolSwapData: transient(PoolSwapData)

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

UNISWAP_V3_FACTORY: public(immutable(address))
UNISWAP_V3_SWAP_ROUTER: public(immutable(address))
UNI_NFT_POSITION_MANAGER: public(immutable(address))

FEE_TIERS: constant(uint24[4]) = [100, 500, 3000, 10000] # 0.01%, 0.05%, 0.3%, 1%
MIN_SQRT_RATIO_PLUS_ONE: constant(uint160) = 4295128740
MAX_SQRT_RATIO_MINUS_ONE: constant(uint160) = 1461446703485210103287273052203988822378723970341
TICK_LOWER: constant(int24) = -887272
TICK_UPPER: constant(int24) = 887272
ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UnderscoreErc721"


@deploy
def __init__(_uniswapV3Factory: address, _uniswapV3SwapRouter: address, _uniNftPositionManager: address, _addyRegistry: address):
    assert empty(address) not in [_uniswapV3Factory, _uniswapV3SwapRouter, _uniNftPositionManager, _addyRegistry] # dev: invalid addrs
    UNISWAP_V3_FACTORY = _uniswapV3Factory
    UNISWAP_V3_SWAP_ROUTER = _uniswapV3SwapRouter
    UNI_NFT_POSITION_MANAGER = _uniNftPositionManager
    ADDY_REGISTRY = _addyRegistry
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
    return [UNISWAP_V3_FACTORY, UNISWAP_V3_SWAP_ROUTER, UNI_NFT_POSITION_MANAGER]


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
@external
def getLpToken(_pool: address) -> address:
    # no lp tokens for uniswap v3
    return empty(address)


########
# Swap #
########


@external
def swapTokens(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _pool: address,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated

    assert empty(address) not in [_tokenIn, _tokenOut] # dev: invalid tokens
    assert _tokenIn != _tokenOut # dev: invalid tokens

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amountIn, staticcall IERC20(_tokenIn).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenIn).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed
    swapAmount: uint256 = min(transferAmount, staticcall IERC20(_tokenIn).balanceOf(self))

    # perform swap
    toAmount: uint256 = 0
    if _pool != empty(address):
        toAmount = self._swapTokensInPool(_pool, _tokenIn, _tokenOut, swapAmount, _minAmountOut, _recipient)
    else:
        toAmount = self._swapTokensGeneric(_tokenIn, _tokenOut, swapAmount, _minAmountOut, _recipient)
    assert toAmount != 0 # dev: no tokens swapped

    # refund if full swap didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_tokenIn).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        swapAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_tokenIn, swapAmount, _tokenOut, toAmount, True, _oracleRegistry)
    log UniswapV3SwapInPool(msg.sender, _pool, _tokenIn, _tokenOut, swapAmount, toAmount, usdValue, _recipient)
    return swapAmount, toAmount, refundAssetAmount, usdValue


# swap in pool


@internal
def _swapTokensInPool(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _recipient: address,
) -> uint256:
    tokens: address[2] = [staticcall UniV3Pool(_pool).token0(), staticcall UniV3Pool(_pool).token1()]
    assert _tokenIn in tokens # dev: invalid tokenIn
    assert _tokenOut in tokens # dev: invalid tokenOut

    # params
    zeroForOne: bool = True
    sqrtPriceLimitX96: uint160 = MIN_SQRT_RATIO_PLUS_ONE
    if _tokenIn != tokens[0]:
        zeroForOne = False
        sqrtPriceLimitX96 = MAX_SQRT_RATIO_MINUS_ONE

    # save in transient storage (for use in callback)
    self.poolSwapData = PoolSwapData(
        pool=_pool,
        tokenIn=_tokenIn,
        amountIn=_amountIn,
    )

    # perform swap
    amount0: int256 = 0
    amount1: int256 = 0
    amount0, amount1 = extcall UniV3Pool(_pool).swap(_recipient, zeroForOne, convert(_amountIn, int256), sqrtPriceLimitX96, b"")

    # check swap results
    toAmount: uint256 = 0
    if zeroForOne:
        toAmount = convert(-amount1, uint256)
    else:
        toAmount = convert(-amount0, uint256)

    assert toAmount >= _minAmountOut # dev: insufficient output
    return toAmount


@external
def uniswapV3SwapCallback(_amount0Delta: int256, _amount1Delta: int256, _data: Bytes[256]):
    poolSwapData: PoolSwapData = self.poolSwapData
    assert msg.sender == poolSwapData.pool # dev: no perms

    # transfer tokens to pool
    assert extcall IERC20(poolSwapData.tokenIn).transfer(poolSwapData.pool, poolSwapData.amountIn, default_return_value=True) # dev: transfer failed


# generic swap


@view
@internal
def _getBestFeeTier(_tokenA: address, _tokenB: address) -> uint24:
    bestLiquidity: uint128 = 0
    bestFeeTier: uint24 = 0

    factory: address = UNISWAP_V3_FACTORY
    for i: uint256 in range(4):
        fee: uint24 = FEE_TIERS[i]
        pool: address = staticcall UniV3Factory(factory).getPool(_tokenA, _tokenB, fee)
        if pool != empty(address):
            liquidity: uint128 = staticcall UniV3Pool(pool).liquidity()
            if liquidity > bestLiquidity:
                bestLiquidity = liquidity
                bestFeeTier = fee

    return bestFeeTier


@internal
def _swapTokensGeneric(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256, 
    _recipient: address,
) -> uint256:
    bestFeeTier: uint24 = self._getBestFeeTier(_tokenIn, _tokenOut)
    assert bestFeeTier != 0 # dev: no pool found

    router: address = UNISWAP_V3_SWAP_ROUTER
    assert extcall IERC20(_tokenIn).approve(router, _amountIn, default_return_value=True) # dev: approval failed
    toAmount: uint256 = extcall UniV3SwapRouter(router).exactInputSingle(
        ExactInputSingleParams(
            tokenIn=_tokenIn,
            tokenOut=_tokenOut,
            fee=bestFeeTier,
            recipient=_recipient,
            amountIn=_amountIn,
            amountOutMinimum=_minAmountOut,
            sqrtPriceLimitX96=0,
        )
    )
    assert extcall IERC20(_tokenIn).approve(router, 0, default_return_value=True) # dev: approval failed
    return toAmount


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
    nftPositionManager: address = UNI_NFT_POSITION_MANAGER
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
    nftPositionManager: address = UNI_NFT_POSITION_MANAGER
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
# Recover Funds #
#################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log FundsRecovered(_asset, _recipient, balance)
    return True


@external
def recoverNft(_collection: address, _nftTokenId: uint256, _recipient: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    if staticcall IERC721(_collection).ownerOf(_nftTokenId) != self:
        return False

    extcall IERC721(_collection).safeTransferFrom(self, _recipient, _nftTokenId)
    log NftRecovered(_collection, _nftTokenId, _recipient)
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