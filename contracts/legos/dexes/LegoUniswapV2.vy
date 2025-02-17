# @version 0.4.0

implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoDex

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
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated

    assert staticcall UniV2Factory(UNISWAP_V2_FACTORY).getPair(_tokenIn, _tokenOut) != empty(address) # dev: no pool found

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amountIn, staticcall IERC20(_tokenIn).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenIn).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # swap assets via lego partner
    swapRouter: address = UNISWAP_V2_ROUTER
    fromAmount: uint256 = min(transferAmount, staticcall IERC20(_tokenIn).balanceOf(self))
    assert extcall IERC20(_tokenIn).approve(swapRouter, fromAmount, default_return_value=True) # dev: approval failed
    amounts: DynArray[uint256, MAX_ASSETS] = extcall UniV2Router(swapRouter).swapExactTokensForTokens(fromAmount, _minAmountOut, [_tokenIn, _tokenOut], _recipient, block.timestamp)
    
    toAmount: uint256 = amounts[1]
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

    log UniswapV2Swap(msg.sender, _tokenIn, _tokenOut, actualSwapAmount, toAmount, usdValue, _recipient)
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
    log UniswapV2LegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log UniswapV2Activated(_shouldActivate)