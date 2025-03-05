

implements: LegoDex
implements: LegoCommon
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed
from interfaces import LegoDex
from interfaces import LegoCommon

interface AeroRouter:
    def addLiquidity(_tokenA: address, _tokenB: address, _isStable: bool, _amountADesired: uint256, _amountBDesired: uint256, _amountAMin: uint256, _amountBMin: uint256, _recipient: address, _deadline: uint256) -> (uint256, uint256, uint256): nonpayable
    def removeLiquidity(_tokenA: address, _tokenB: address, _isStable: bool, _lpAmount: uint256, _amountAMin: uint256, _amountBMin: uint256, _recipient: address, _deadline: uint256) -> (uint256, uint256): nonpayable
    def swapExactTokensForTokens(_amountIn: uint256, _amountOutMin: uint256, _path: DynArray[Route, MAX_SWAP_HOPS + 2], _to: address, _deadline: uint256) -> DynArray[uint256, MAX_SWAP_HOPS + 2]: nonpayable 
    def quoteAddLiquidity(_tokenA: address, _tokenB: address, _isStable: bool, _factory: address, _amountADesired: uint256, _amountBDesired: uint256) -> (uint256, uint256, uint256): view
    def quoteRemoveLiquidity(_tokenA: address, _tokenB: address, _isStable: bool, _factory: address, _liquidity: uint256) -> (uint256, uint256): view

interface AeroClassicPool:
    def swap(_amount0Out: uint256, _amount1Out: uint256, _recipient: address, _data: Bytes[256]): nonpayable
    def getAmountOut(_amountIn: uint256, _tokenIn: address) -> uint256: view
    def getReserves() -> (uint256, uint256, uint256): view
    def tokens() -> (address, address): view
    def stable() -> bool: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface AeroFactory:
    def getPool(_tokenA: address, _tokenB: address, _isStable: bool) -> address: view
    def getFee(_pool: address, _isStable: bool) -> uint256: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct BestPool:
    pool: address
    fee: uint256
    liquidity: uint256
    numCoins: uint256
    legoId: uint256

struct Route:
    from_: address
    to: address 
    stable: bool
    factory: address

event AerodromeSwap:
    sender: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    amountIn: uint256
    amountOut: uint256
    usdValue: uint256
    numTokens: uint256
    recipient: address

event AerodromeLiquidityAdded:
    sender: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    amountA: uint256
    amountB: uint256
    lpAmountReceived: uint256
    usdValue: uint256
    recipient: address

event AerodromeLiquidityRemoved:
    sender: address
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    amountA: uint256
    amountB: uint256
    lpToken: address
    lpAmountBurned: uint256
    usdValue: uint256
    recipient: address

event AeroClassicCoreRouterPoolSet:
    pool: indexed(address)

event AeroClassicFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AerodromeLegoIdSet:
    legoId: uint256

event AerodromeActivated:
    isActivated: bool

# aero
coreRouterPool: public(address)
AERODROME_FACTORY: public(immutable(address))
AERODROME_ROUTER: public(immutable(address))

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

MAX_SWAP_HOPS: constant(uint256) = 5
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_TOKEN_PATH: constant(uint256) = 5


@deploy
def __init__(
    _aerodromeFactory: address,
    _aerodromeRouter: address,
    _addyRegistry: address,
    _coreRouterPool: address,
):
    assert empty(address) not in [_aerodromeFactory, _aerodromeRouter, _addyRegistry, _coreRouterPool] # dev: invalid addrs
    AERODROME_FACTORY = _aerodromeFactory
    AERODROME_ROUTER = _aerodromeRouter
    ADDY_REGISTRY = _addyRegistry
    self.coreRouterPool = _coreRouterPool
    self.isActivated = True
    gov.__init__(_addyRegistry)


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [AERODROME_FACTORY, AERODROME_ROUTER]


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

    # transfer initial amount to first pool
    assert extcall IERC20(tokenIn).transfer(_poolPath[0], initialAmountIn, default_return_value=True) # dev: transfer failed

    aeroFactory: address = AERODROME_FACTORY

    # iterate through swap routes
    tempAmountIn: uint256 = initialAmountIn
    for i: uint256 in range(numTokens - 1, bound=MAX_TOKEN_PATH):
        tempTokenIn: address = _tokenPath[i]
        tempTokenOut: address = _tokenPath[i + 1]
        tempPool: address = _poolPath[i]

        # transfer to next pool (or to recipient if last swap)
        recipient: address = _recipient
        if i < numTokens - 2:
            recipient = _poolPath[i + 1]

        # swap
        tempAmountIn = self._swapTokensInPool(tempPool, tempTokenIn, tempTokenOut, tempAmountIn, recipient, aeroFactory)

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
    log AerodromeSwap(msg.sender, tokenIn, tokenOut, initialAmountIn, toAmount, usdValue, numTokens, _recipient)
    return initialAmountIn, toAmount, refundAssetAmount, usdValue


# swap in pool


@internal
def _swapTokensInPool(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _recipient: address,
    _aeroFactory: address,
) -> uint256:
    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_pool).tokens()

    tokens: address[2] = [token0, token1]
    assert _tokenIn in tokens # dev: invalid tokenIn
    assert _tokenOut in tokens # dev: invalid tokenOut
    assert _tokenIn != _tokenOut # dev: invalid tokens

    # verify actual aerodrome pool
    assert staticcall AeroFactory(_aeroFactory).getPool(_tokenIn, _tokenOut, staticcall AeroClassicPool(_pool).stable()) == _pool # dev: invalid pool

    zeroForOne: bool = _tokenIn == token0
    amountOut: uint256 = staticcall AeroClassicPool(_pool).getAmountOut(_amountIn, _tokenIn)
    assert amountOut != 0 # dev: no tokens swapped

    # put in correct order
    amount0Out: uint256 = amountOut
    amount1Out: uint256 = 0
    if zeroForOne:
        amount0Out = 0
        amount1Out = amountOut

    extcall AeroClassicPool(_pool).swap(amount0Out, amount1Out, _recipient, b"")
    return amountOut


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
    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_pool).tokens()

    tokens: address[2] = [token0, token1]
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
    router: address = AERODROME_ROUTER
    assert extcall IERC20(_tokenA).approve(router, liqAmountA, default_return_value=True) # dev: approval failed
    assert extcall IERC20(_tokenB).approve(router, liqAmountB, default_return_value=True) # dev: approval failed

    # add liquidity
    lpAmountReceived: uint256 = 0
    liqAmountA, liqAmountB, lpAmountReceived = extcall AeroRouter(router).addLiquidity(
        _tokenA,
        _tokenB,
        staticcall AeroClassicPool(_pool).stable(),
        liqAmountA,
        liqAmountB,
        _minAmountA,
        _minAmountB,
        _recipient,
        block.timestamp,
    )
    assert lpAmountReceived != 0 # dev: no liquidity added
    if _minLpAmount != 0:
        assert lpAmountReceived >= _minLpAmount # dev: insufficient liquidity added

    # reset approvals
    assert extcall IERC20(_tokenA).approve(router, 0, default_return_value=True) # dev: approval failed
    assert extcall IERC20(_tokenB).approve(router, 0, default_return_value=True) # dev: approval failed

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

    usdValue: uint256 = self._getUsdValue(_tokenA, liqAmountA, _tokenB, liqAmountB, False, _oracleRegistry)
    log AerodromeLiquidityAdded(msg.sender, _tokenA, _tokenB, liqAmountA, liqAmountB, lpAmountReceived, usdValue, _recipient)
    return lpAmountReceived, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, 0


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

    # validate tokens
    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_pool).tokens()

    tokens: address[2] = [token0, token1]
    assert _tokenA in tokens # dev: invalid tokenA
    assert _tokenB in tokens # dev: invalid tokenB
    assert _tokenA != _tokenB # dev: invalid tokens

    # pre balance
    preLegoBalance: uint256 = staticcall IERC20(_lpToken).balanceOf(self)

    # lp token
    transferAmount: uint256 = min(_liqToRemove, staticcall IERC20(_lpToken).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_lpToken).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed
    lpAmount: uint256 = min(transferAmount, staticcall IERC20(_lpToken).balanceOf(self))

    # approvals
    router: address = AERODROME_ROUTER
    assert extcall IERC20(_lpToken).approve(router, lpAmount, default_return_value=True) # dev: approval failed

    # remove liquidity
    amountA: uint256 = 0
    amountB: uint256 = 0
    amountA, amountB = extcall AeroRouter(router).removeLiquidity(
        _tokenA,
        _tokenB,
        staticcall AeroClassicPool(_pool).stable(),
        lpAmount,
        _minAmountA,
        _minAmountB,
        _recipient,
        block.timestamp,
    )
    assert amountA != 0 # dev: no amountA removed
    assert amountB != 0 # dev: no amountB removed

    # reset approvals
    assert extcall IERC20(_lpToken).approve(router, 0, default_return_value=True) # dev: approval failed

    # refund if full liquidity was not removed
    currentLegoBalance: uint256 = staticcall IERC20(_lpToken).balanceOf(self)
    refundedLpAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundedLpAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_lpToken).transfer(msg.sender, refundedLpAmount, default_return_value=True) # dev: transfer failed
        lpAmount -= refundedLpAmount

    usdValue: uint256 = self._getUsdValue(_tokenA, amountA, _tokenB, amountB, False, _oracleRegistry)
    log AerodromeLiquidityRemoved(msg.sender, _pool, _tokenA, _tokenB, amountA, amountB, _lpToken, lpAmount, usdValue, _recipient)
    return amountA, amountB, usdValue, lpAmount, refundedLpAmount, refundedLpAmount != 0


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
    # in uniswap v2, the lp token is the pool address
    return _pool


@view
@external
def getPoolForLpToken(_lpToken: address) -> address:
    # in uniswap v2, the pool is the lp token address
    return _lpToken


@view
@external
def getCoreRouterPool() -> address:
    return self.coreRouterPool


@view
@external
def getDeepestLiqPool(_tokenA: address, _tokenB: address) -> BestPool:
    factory: address = AERODROME_FACTORY
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    na: uint256 = 0

    # get pool options
    stablePool: address = staticcall AeroFactory(factory).getPool(_tokenA, _tokenB, True)
    volatilePool: address = staticcall AeroFactory(factory).getPool(_tokenA, _tokenB, False)

    # no pools found
    if stablePool == empty(address) and volatilePool == empty(address):
        return empty(BestPool)

    # stable pool
    stableLiquidity: uint256 = 0
    if stablePool != empty(address):
        reserve0, reserve1, na = staticcall AeroClassicPool(stablePool).getReserves()
        stableLiquidity = reserve0 + reserve1

    # volatile pool
    volatileLiquidity: uint256 = 0
    if volatilePool != empty(address):
        reserve0, reserve1, na = staticcall AeroClassicPool(volatilePool).getReserves()
        volatileLiquidity = reserve0 + reserve1

    # best pool determined by liquidity
    bestPoolAddr: address = stablePool
    bestLiquidity: uint256 = stableLiquidity
    isStable: bool = True
    if volatileLiquidity > stableLiquidity:
        bestPoolAddr = volatilePool
        bestLiquidity = volatileLiquidity
        isStable = False

    return BestPool(
        pool=bestPoolAddr,
        fee=staticcall AeroFactory(factory).getFee(bestPoolAddr, isStable),
        liquidity=bestLiquidity,
        numCoins=2,
        legoId=self.legoId,
    )


@view
@external
def getBestSwapAmountOut(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> (address, uint256):
    factory: address = AERODROME_FACTORY
    stablePool: address = staticcall AeroFactory(factory).getPool(_tokenIn, _tokenOut, True)
    volatilePool: address = staticcall AeroFactory(factory).getPool(_tokenIn, _tokenOut, False)
    if stablePool == empty(address) and volatilePool == empty(address):
        return empty(address), 0

    # stable pool
    stableAmountOut: uint256 = 0
    if stablePool != empty(address):
        stableAmountOut = staticcall AeroClassicPool(stablePool).getAmountOut(_amountIn, _tokenIn)

    # volatile pool
    volatileAmountOut: uint256 = 0
    if volatilePool != empty(address):
        volatileAmountOut = staticcall AeroClassicPool(volatilePool).getAmountOut(_amountIn, _tokenIn)

    if stableAmountOut == 0 and volatileAmountOut == 0:
        return empty(address), 0

    pool: address = stablePool
    amountOut: uint256 = stableAmountOut
    if volatileAmountOut > stableAmountOut:
        pool = volatilePool
        amountOut = volatileAmountOut

    return pool, amountOut


@view
@external
def getSwapAmountOut(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
) -> uint256:
    return staticcall AeroClassicPool(_pool).getAmountOut(_amountIn, _tokenIn)


@view
@external
def getBestSwapAmountIn(_tokenIn: address, _tokenOut: address, _amountOut: uint256) -> (address, uint256):
    # TODO: implement stable pools
    pool: address = staticcall AeroFactory(AERODROME_FACTORY).getPool(_tokenIn, _tokenOut, False)
    if pool == empty(address):
        return empty(address), 0
    return pool, self._getAmountInForVolatilePools(pool, _tokenIn, _tokenOut, _amountOut)


@view
@external
def getSwapAmountIn(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
) -> uint256:
    if not staticcall AeroClassicPool(_pool).stable():
        return self._getAmountInForVolatilePools(_pool, _tokenIn, _tokenOut, _amountOut)
    else:
        return 0 # TODO: implement stable pools


@view
@external
def getAddLiqAmountsIn(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _availAmountA: uint256,
    _availAmountB: uint256,
) -> (uint256, uint256, uint256):
    return staticcall AeroRouter(AERODROME_ROUTER).quoteAddLiquidity(_tokenA, _tokenB, staticcall AeroClassicPool(_pool).stable(), AERODROME_FACTORY, _availAmountA, _availAmountB)


@view
@external
def getRemoveLiqAmountsOut(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpAmount: uint256,
) -> (uint256, uint256):
    return staticcall AeroRouter(AERODROME_ROUTER).quoteRemoveLiquidity(_tokenA, _tokenB, staticcall AeroClassicPool(_pool).stable(), AERODROME_FACTORY, _lpAmount)


@view
@external
def getPriceUnsafe(_pool: address, _targetToken: address, _oracleRegistry: address = empty(address)) -> uint256:
    if not staticcall AeroClassicPool(_pool).stable():
        return self._getPriceUnsafeVolatilePool(_pool, _targetToken, _oracleRegistry)
    else:
        return 0 # TODO: implement stable pools


# internal utils


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
def _getPriceUnsafeVolatilePool(_pool: address, _targetToken: address, _oracleRegistry: address) -> uint256:
    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_pool).tokens()

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

    # reserves
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    na: uint256 = 0
    reserve0, reserve1, na = staticcall AeroClassicPool(_pool).getReserves()

    # avoid division by zero
    if reserve0 == 0 or reserve1 == 0:
        return 0  

    # price of token0 in token1
    priceZeroToOne: uint256 = reserve1 * EIGHTEEN_DECIMALS // reserve0

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


@view
@internal
def _getAmountInForVolatilePools(_pool: address, _tokenIn: address, _tokenOut: address, _amountOut: uint256) -> uint256:
    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_pool).tokens()

    reserve0: uint256 = 0
    reserve1: uint256 = 0
    na: uint256 = 0
    reserve0, reserve1, na = staticcall AeroClassicPool(_pool).getReserves()

    # determine which token is which
    reserveIn: uint256 = reserve0
    reserveOut: uint256 = reserve1
    if _tokenIn != token0:
        reserveIn = reserve1
        reserveOut = reserve0

    if _amountOut > reserveOut:
        return max_value(uint256)

    fee: uint256 = staticcall AeroFactory(AERODROME_FACTORY).getFee(_pool, False)
    numerator: uint256 = reserveIn * _amountOut * 100_00
    denominator: uint256 = (reserveOut - _amountOut) * (100_00 - fee)
    return (numerator // denominator) + 1


####################
# Core Router Pool #
####################


@external
def setCoreRouterPool(_addr: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.coreRouterPool = _addr
    log AeroClassicCoreRouterPoolSet(_addr)
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
    log AeroClassicFundsRecovered(_asset, _recipient, balance)
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
    log AerodromeLegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log AerodromeActivated(_shouldActivate)
