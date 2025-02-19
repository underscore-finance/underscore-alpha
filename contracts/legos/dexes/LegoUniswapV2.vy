# @version 0.4.0

implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoDex

interface IUniswapV2Pair:
    def swap(_amount0Out: uint256, _amount1Out: uint256, _to: address, _data: Bytes[256]): nonpayable
    def getReserves() -> (uint112, uint112, uint32): view
    def token0() -> address: view
    def token1() -> address: view

interface UniV2Router:
    def swapExactTokensForTokens(_amountIn: uint256, _amountOutMin: uint256, _path: DynArray[address, MAX_ASSETS], _to: address, _deadline: uint256) -> DynArray[uint256, MAX_ASSETS]: nonpayable 

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface UniV2Factory:
    def getPair(_tokenA: address, _tokenB: address) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

event UniswapV2Swap:
    sender: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    amountIn: uint256
    amountOut: uint256
    usdValue: uint256
    recipient: address

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event UniswapV2LegoIdSet:
    legoId: uint256

event UniswapV2Activated:
    isActivated: bool

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

UNISWAP_V2_FACTORY: public(immutable(address))
UNISWAP_V2_ROUTER: public(immutable(address))

MAX_ASSETS: constant(uint256) = 5


@deploy
def __init__(_uniswapV2Factory: address, _uniswapV2Router: address, _addyRegistry: address):
    assert empty(address) not in [_uniswapV2Factory, _uniswapV2Router, _addyRegistry] # dev: invalid addrs
    UNISWAP_V2_FACTORY = _uniswapV2Factory
    UNISWAP_V2_ROUTER = _uniswapV2Router
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(_addyRegistry)


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [UNISWAP_V2_FACTORY, UNISWAP_V2_ROUTER]


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
    log UniswapV2Swap(msg.sender, _tokenIn, _tokenOut, swapAmount, toAmount, usdValue, _recipient)
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
    tokens: address[2] = [staticcall IUniswapV2Pair(_pool).token0(), staticcall IUniswapV2Pair(_pool).token1()]
    assert _tokenIn in tokens # dev: invalid tokenIn
    assert _tokenOut in tokens # dev: invalid tokenOut
    assert _tokenIn != _tokenOut # dev: cannot use same token

    zeroForOne: bool = _tokenIn == tokens[0]
    preRecipientBalance: uint256 = staticcall IERC20(_tokenOut).balanceOf(_recipient)

    # get reserves
    reserve0: uint112 = 0
    reserve1: uint112 = 0
    na: uint32 = 0
    reserve0, reserve1, na = staticcall IUniswapV2Pair(_pool).getReserves()

    # determine reserves based on input and output tokens
    reserveIn: uint112 = reserve1
    reserveOut: uint112 = reserve0
    if zeroForOne:
        reserveIn = reserve0
        reserveOut = reserve1

    # finalize amount outs
    amountOut: uint256 = self._getAmountOut(_amountIn, convert(reserveIn, uint256), convert(reserveOut, uint256))
    assert amountOut >= _minAmountOut # dev: insufficient output

    amount0Out: uint256 = amountOut
    amount1Out: uint256 = 0
    if zeroForOne:
        amount0Out = 0
        amount1Out = amountOut

    # perform swap
    assert extcall IERC20(_tokenIn).transfer(_pool, _amountIn, default_return_value=True) # dev: transfer failed
    extcall IUniswapV2Pair(_pool).swap(amount0Out, amount1Out, _recipient, b"")

    # get post-swap recipient balance
    toAmount: uint256 = 0
    postRecipientBalance: uint256 = staticcall IERC20(_tokenOut).balanceOf(_recipient)
    if postRecipientBalance > preRecipientBalance:
        toAmount = postRecipientBalance - preRecipientBalance

    assert toAmount == amountOut # dev: incorrect amount out
    return toAmount


@view
@internal
def _getAmountOut(_amountIn: uint256, _reserveIn: uint256, _reserveOut: uint256) -> uint256:
    amountInWithFee: uint256 = _amountIn * 997 # 1000 - 3 (0.3% fee)
    numerator: uint256 = amountInWithFee * _reserveOut
    denominator: uint256 = (_reserveIn * 1000) + amountInWithFee
    return numerator // denominator


################
# Swap Generic #
################


@internal
def _swapTokensGeneric(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256, 
    _recipient: address,
) -> uint256:
    assert staticcall UniV2Factory(UNISWAP_V2_FACTORY).getPair(_tokenIn, _tokenOut) != empty(address) # dev: no pool found

    swapRouter: address = UNISWAP_V2_ROUTER
    assert extcall IERC20(_tokenIn).approve(swapRouter, _amountIn, default_return_value=True) # dev: approval failed
    amounts: DynArray[uint256, MAX_ASSETS] = extcall UniV2Router(swapRouter).swapExactTokensForTokens(_amountIn, _minAmountOut, [_tokenIn, _tokenOut], _recipient, block.timestamp)
    assert extcall IERC20(_tokenIn).approve(swapRouter, 0, default_return_value=True) # dev: approval failed
    return amounts[1]


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
    log UniswapV2LegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log UniswapV2Activated(_shouldActivate)