# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface UniV3Factory:
    def getPool(_tokenA: address, _tokenB: address, _fee: uint24) -> address: view

interface UniV3SwapRouter:
    def exactInputSingle(_params: ExactInputSingleParams) -> uint256: payable

interface UniV3Pool:
    def liquidity() -> uint128: view

interface LegoRegistry:
    def governor() -> address: view

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

legoId: public(uint256)

LEGO_REGISTRY: public(immutable(address))
UNISWAP_V3_FACTORY: public(immutable(address))
UNISWAP_V3_SWAP_ROUTER: public(immutable(address))

FEE_TIERS: constant(uint24[4]) = [100, 500, 3000, 10000] # 0.01%, 0.05%, 0.3%, 1%


@deploy
def __init__(_uniswapV3Factory: address, _uniswapV3SwapRouter: address, _legoRegistry: address):
    assert empty(address) not in [_uniswapV3Factory, _uniswapV3SwapRouter, _legoRegistry] # dev: invalid addrs
    UNISWAP_V3_FACTORY = _uniswapV3Factory
    UNISWAP_V3_SWAP_ROUTER = _uniswapV3SwapRouter
    LEGO_REGISTRY = _legoRegistry


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [UNISWAP_V3_FACTORY, UNISWAP_V3_SWAP_ROUTER]


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
) -> (uint256, uint256, uint256, uint256):
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

    # TODO: add usd value
    # use the maximum of the two: either (_tokenIn, actualSwapAmount) or (_tokenOut, toAmount)
    usdValue: uint256 = 0

    log UniswapV3Swap(msg.sender, _tokenIn, _tokenOut, actualSwapAmount, toAmount, usdValue, _recipient)
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
    log UniswapV3LegoIdSet(_legoId)
    return True
