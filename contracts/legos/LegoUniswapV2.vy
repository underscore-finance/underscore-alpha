# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface UniV2Router:
    def swapExactTokensForTokens(_amountIn: uint256, _amountOutMin: uint256, _path: DynArray[address, MAX_ASSETS], _to: address, _deadline: uint256) -> DynArray[uint256, MAX_ASSETS]: nonpayable 

interface UniV2Factory:
    def getPair(_tokenA: address, _tokenB: address) -> address: view

interface LegoRegistry:
    def governor() -> address: view

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

legoId: public(uint256)

LEGO_REGISTRY: public(immutable(address))
UNISWAP_V2_FACTORY: public(immutable(address))
UNISWAP_V2_ROUTER: public(immutable(address))

MAX_ASSETS: constant(uint256) = 5


@deploy
def __init__(_uniswapV2Factory: address, _uniswapV2Router: address, _legoRegistry: address):
    assert empty(address) not in [_uniswapV2Factory, _uniswapV2Router, _legoRegistry] # dev: invalid addrs
    UNISWAP_V2_FACTORY = _uniswapV2Factory
    UNISWAP_V2_ROUTER = _uniswapV2Router
    LEGO_REGISTRY = _legoRegistry


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [UNISWAP_V2_FACTORY, UNISWAP_V2_ROUTER]


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
) -> (uint256, uint256, uint256, uint256):
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

    # TODO: add usd value
    # use the maximum of the two: either (_tokenIn, actualSwapAmount) or (_tokenOut, toAmount)
    usdValue: uint256 = 0 

    log UniswapV2Swap(msg.sender, _tokenIn, _tokenOut, actualSwapAmount, toAmount, usdValue, _recipient)
    return actualSwapAmount, toAmount, refundAssetAmount, usdValue


###################
# Not Implemented #
###################


@external
def depositTokens(_asset: address, _amount: uint256, _vault: address, _recipient: address) -> (uint256, address, uint256, uint256, uint256):
    raise "Not Implemented"


@external
def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address, _recipient: address) -> (uint256, uint256, uint256, uint256):
    raise "Not Implemented"


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms

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
    assert msg.sender == LEGO_REGISTRY # dev: no perms
    assert self.legoId == 0 # dev: already set
    self.legoId = _legoId
    log UniswapV2LegoIdSet(_legoId)
    return True
