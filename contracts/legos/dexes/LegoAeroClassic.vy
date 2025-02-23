# @version 0.4.0

implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoDex

interface AeroClassicPool:
    def swap(_amount0Out: uint256, _amount1Out: uint256, _recipient: address, _data: Bytes[256]): nonpayable
    def getAmountOut(_amountIn: uint256, _tokenIn: address) -> uint256: view
    def tokens() -> (address, address): view
    def stable() -> bool: view

interface AeroRouter:
    def addLiquidity(_tokenA: address, _tokenB: address, _isStable: bool, _amountADesired: uint256, _amountBDesired: uint256, _amountAMin: uint256, _amountBMin: uint256, _recipient: address, _deadline: uint256) -> (uint256, uint256, uint256): nonpayable
    def removeLiquidity(_tokenA: address, _tokenB: address, _isStable: bool, _lpAmount: uint256, _amountAMin: uint256, _amountBMin: uint256, _recipient: address, _deadline: uint256) -> (uint256, uint256): nonpayable
    def swapExactTokensForTokens(_amountIn: uint256, _amountOutMin: uint256, _path: DynArray[Route, MAX_ASSETS], _to: address, _deadline: uint256) -> DynArray[uint256, MAX_ASSETS]: nonpayable 

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface AeroFactory:
    def getPool(_tokenA: address, _tokenB: address, _isStable: bool) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

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

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AerodromeLegoIdSet:
    legoId: uint256

event AerodromeActivated:
    isActivated: bool

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

AERODROME_FACTORY: public(immutable(address))
AERODROME_ROUTER: public(immutable(address))

MAX_ASSETS: constant(uint256) = 5


@deploy
def __init__(_aerodromeFactory: address, _aerodromeRouter: address, _addyRegistry: address):
    assert empty(address) not in [_aerodromeFactory, _aerodromeRouter, _addyRegistry] # dev: invalid addrs
    AERODROME_FACTORY = _aerodromeFactory
    AERODROME_ROUTER = _aerodromeRouter
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(_addyRegistry)


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [AERODROME_FACTORY, AERODROME_ROUTER]


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
    # in uniswap v2, the lp token is the pool address
    return _pool


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
    log AerodromeSwap(msg.sender, _tokenIn, _tokenOut, swapAmount, toAmount, usdValue, _recipient)
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
    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_pool).tokens()

    tokens: address[2] = [token0, token1]
    assert _tokenIn in tokens # dev: invalid tokenIn
    assert _tokenOut in tokens # dev: invalid tokenOut

    zeroForOne: bool = _tokenIn == token0
    preRecipientBalance: uint256 = staticcall IERC20(_tokenOut).balanceOf(_recipient)

    # finalize amount out
    amountOut: uint256 = staticcall AeroClassicPool(_pool).getAmountOut(_amountIn, _tokenIn)
    assert amountOut >= _minAmountOut # dev: insufficient output

    amount0Out: uint256 = amountOut
    amount1Out: uint256 = 0
    if zeroForOne:
        amount0Out = 0
        amount1Out = amountOut

    # perform swap
    assert extcall IERC20(_tokenIn).transfer(_pool, _amountIn, default_return_value=True) # dev: transfer failed
    extcall AeroClassicPool(_pool).swap(amount0Out, amount1Out, _recipient, b"")

    # get post-swap recipient balance
    toAmount: uint256 = 0
    postRecipientBalance: uint256 = staticcall IERC20(_tokenOut).balanceOf(_recipient)
    if postRecipientBalance > preRecipientBalance:
        toAmount = postRecipientBalance - preRecipientBalance

    assert toAmount == amountOut # dev: incorrect amount out
    return toAmount


# generic swap


@internal
def _swapTokensGeneric(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256, 
    _recipient: address,
) -> uint256:
    factory: address = AERODROME_FACTORY
    swapRouter: address = AERODROME_ROUTER
    assert extcall IERC20(_tokenIn).approve(swapRouter, _amountIn, default_return_value=True) # dev: approval failed

    # perform swap
    route: Route = Route(
        from_=_tokenIn,
        to=_tokenOut,
        stable=self._isStablePair(_tokenIn, _tokenOut, factory),
        factory=factory,
    )
    amounts: DynArray[uint256, MAX_ASSETS] = extcall AeroRouter(swapRouter).swapExactTokensForTokens(_amountIn, _minAmountOut, [route], _recipient, block.timestamp)

    assert extcall IERC20(_tokenIn).approve(swapRouter, 0, default_return_value=True) # dev: approval failed
    return amounts[1]


@view
@internal
def _isStablePair(_tokenA: address, _tokenB: address, _factory: address) -> bool:
    pool: address = staticcall AeroFactory(_factory).getPool(_tokenA, _tokenB, True)
    if pool != empty(address):
        return True

    pool = staticcall AeroFactory(_factory).getPool(_tokenA, _tokenB, False)
    assert pool != empty(address) # dev: no pool found
    return False


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
    log AerodromeLegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log AerodromeActivated(_shouldActivate)
