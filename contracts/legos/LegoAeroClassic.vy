# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface AeroRouter:
    def swapExactTokensForTokens(_amountIn: uint256, _amountOutMin: uint256, _path: DynArray[Route, MAX_ASSETS], _to: address, _deadline: uint256) -> DynArray[uint256, MAX_ASSETS]: nonpayable 

interface AeroFactory:
    def getPool(_tokenA: address, _tokenB: address, _isStable: bool) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governor() -> address: view

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

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AerodromeLegoIdSet:
    legoId: uint256

legoId: public(uint256)

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


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [AERODROME_FACTORY, AERODROME_ROUTER]


########
# Swap #
########


@view
@internal
def _getBestPoolData(_tokenA: address, _tokenB: address, _factory: address) -> bool:
    pool: address = staticcall AeroFactory(_factory).getPool(_tokenA, _tokenB, True)
    if pool != empty(address):
        return True

    pool = staticcall AeroFactory(_factory).getPool(_tokenA, _tokenB, False)
    assert pool != empty(address) # dev: no pool found
    return False


@external
def swapTokens(
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256, 
    _recipient: address,
) -> (uint256, uint256, uint256, uint256):
    factory: address = AERODROME_FACTORY
    isStable: bool = self._getBestPoolData(_tokenIn, _tokenOut, factory)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amountIn, staticcall IERC20(_tokenIn).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenIn).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # swap assets via lego partner
    swapRouter: address = AERODROME_ROUTER
    fromAmount: uint256 = min(transferAmount, staticcall IERC20(_tokenIn).balanceOf(self))
    assert extcall IERC20(_tokenIn).approve(swapRouter, fromAmount, default_return_value=True) # dev: approval failed
    route: Route = Route(
        from_=_tokenIn,
        to=_tokenOut,
        stable=isStable,
        factory=factory,
    )
    amounts: DynArray[uint256, MAX_ASSETS] = extcall AeroRouter(swapRouter).swapExactTokensForTokens(fromAmount, _minAmountOut, [route], _recipient, block.timestamp)
    
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

    log AerodromeSwap(msg.sender, _tokenIn, _tokenOut, actualSwapAmount, toAmount, usdValue, _recipient)
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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

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
    assert self.legoId == 0 # dev: already set
    self.legoId = _legoId
    log AerodromeLegoIdSet(_legoId)
    return True
