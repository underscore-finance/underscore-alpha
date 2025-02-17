# @version 0.4.0

implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoDex

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface UniV3Factory:
    def getPool(_tokenA: address, _tokenB: address, _fee: uint24) -> address: view

interface UniV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

interface UniV3Pool:
    def liquidity() -> uint128: view

struct ExactInputSingleParams:
    tokenIn: address
    tokenOut: address
    fee: uint24
    recipient: address
    amountIn: uint256
    amountOutMinimum: uint256
    sqrtPriceLimitX96: uint160

event UniswapV3Swap:
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

event UniswapV3LegoIdSet:
    legoId: uint256

event UniswapV3Activated:
    isActivated: bool

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

UNISWAP_V3_FACTORY: public(immutable(address))
UNISWAP_V3_SWAP_ROUTER: public(immutable(address))

FEE_TIERS: constant(uint24[4]) = [100, 500, 3000, 10000] # 0.01%, 0.05%, 0.3%, 1%


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


@external
def swapTokens(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256, 
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated

    bestFeeTier: uint24 = self._getBestFeeTier(_tokenIn, _tokenOut)
    assert bestFeeTier != 0 # dev: no pool found

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amountIn, staticcall IERC20(_tokenIn).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenIn).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # swap assets via lego partner
    swapRouter: address = UNISWAP_V3_SWAP_ROUTER
    fromAmount: uint256 = min(transferAmount, staticcall IERC20(_tokenIn).balanceOf(self))
    assert extcall IERC20(_tokenIn).approve(swapRouter, fromAmount, default_return_value=True) # dev: approval failed
    toAmount: uint256 = extcall UniV3SwapRouter(swapRouter).exactInputSingle(
        ExactInputSingleParams(
            tokenIn=_tokenIn,
            tokenOut=_tokenOut,
            fee=bestFeeTier,
            recipient=_recipient,
            amountIn=fromAmount,
            amountOutMinimum=_minAmountOut,
            sqrtPriceLimitX96=0,
        )
    )
    assert toAmount != 0 # dev: no tokens swapped
    assert extcall IERC20(_tokenIn).approve(swapRouter, 0, default_return_value=True) # dev: approval failed

    # refund if full swap didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_tokenIn).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    actualSwapAmount: uint256 = fromAmount - refundAssetAmount
    usdValue: uint256 = self._getUsdValue(_tokenIn, actualSwapAmount, _tokenOut, toAmount, _oracleRegistry)

    log UniswapV3Swap(msg.sender, _tokenIn, _tokenOut, actualSwapAmount, toAmount, usdValue, _recipient)
    return actualSwapAmount, toAmount, refundAssetAmount, usdValue


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