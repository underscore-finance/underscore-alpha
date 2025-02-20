# @version 0.4.0

implements: IUniswapV3Callback
implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoDex

interface UniV3Pool:
    def swap(_recipient: address, _zeroForOne: bool, _amountSpecified: int256, _sqrtPriceLimitX96: uint160, _data: Bytes[256]) -> (int256, int256): nonpayable
    def liquidity() -> uint128: view
    def token0() -> address: view
    def token1() -> address: view

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

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

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

FEE_TIERS: constant(uint24[4]) = [100, 500, 3000, 10000] # 0.01%, 0.05%, 0.3%, 1%
MIN_SQRT_RATIO_PLUS_ONE: constant(uint160) = 4295128740
MAX_SQRT_RATIO_MINUS_ONE: constant(uint160) = 1461446703485210103287273052203988822378723970341


@deploy
def __init__(_uniswapV3Factory: address, _uniswapV3SwapRouter: address, _addyRegistry: address):
    assert empty(address) not in [_uniswapV3Factory, _uniswapV3SwapRouter, _addyRegistry] # dev: invalid addrs
    UNISWAP_V3_FACTORY = _uniswapV3Factory
    UNISWAP_V3_SWAP_ROUTER = _uniswapV3SwapRouter
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(_addyRegistry)


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [UNISWAP_V3_FACTORY, UNISWAP_V3_SWAP_ROUTER]


@view
@internal
def _getUsdValue(
    _tokenIn: address,
    _tokenInAmount: uint256,
    _tokenOut: address,
    _tokenOutAmount: uint256,
    _oracleRegistry: address,
) -> uint256:
    oracleRegistry: address = _oracleRegistry
    if _oracleRegistry == empty(address):
        oracleRegistry = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)
    tokenInUsdValue: uint256 = staticcall OracleRegistry(oracleRegistry).getUsdValue(_tokenIn, _tokenInAmount)
    tokenOutUsdValue: uint256 = staticcall OracleRegistry(oracleRegistry).getUsdValue(_tokenOut, _tokenOutAmount)
    return max(tokenInUsdValue, tokenOutUsdValue)


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

    usdValue: uint256 = self._getUsdValue(_tokenIn, swapAmount, _tokenOut, toAmount, _oracleRegistry)
    log UniswapV3SwapInPool(msg.sender, _pool, _tokenIn, _tokenOut, swapAmount, toAmount, usdValue, _recipient)
    return swapAmount, toAmount, refundAssetAmount, usdValue


################
# Swap In Pool #
################


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


################
# Swap Generic #
################


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

    swapRouter: address = UNISWAP_V3_SWAP_ROUTER
    assert extcall IERC20(_tokenIn).approve(swapRouter, _amountIn, default_return_value=True) # dev: approval failed
    toAmount: uint256 = extcall UniV3SwapRouter(swapRouter).exactInputSingle(
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
    assert extcall IERC20(_tokenIn).approve(swapRouter, 0, default_return_value=True) # dev: approval failed
    return toAmount


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