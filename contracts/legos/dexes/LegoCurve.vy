# @version 0.4.0

implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoDex

interface CurveMetaRegistry:
    def get_coin_indices(_pool: address, _from: address, _to: address) -> (int128, int128, bool): view
    def find_pools_for_coins(_from: address, _to: address) -> DynArray[address, MAX_POOLS]: view
    def get_registry_handlers_from_pool(_pool: address) -> address[10]: view
    def get_underlying_balances(_pool: address) -> uint256[8]: view
    def get_underlying_coins(_pool: address) -> address[8]: view
    def get_base_registry(_addr: address) -> address: view
    def is_registered(_pool: address) -> bool: view
    def is_meta(_pool: address) -> bool: view

interface TwoCryptoPool:
    def exchange(_i: uint256, _j: uint256, _dx: uint256, _min_dy: uint256, _use_eth: bool = False, _receiver: address = msg.sender) -> uint256: payable

interface CommonCurvePool:
    def exchange(_i: int128, _j: int128, _dx: uint256, _min_dy: uint256, _receiver: address = msg.sender) -> uint256: nonpayable

interface TwoCryptoNgPool:
    def exchange(i: uint256, j: uint256, dx: uint256, min_dy: uint256, receiver: address = msg.sender) -> uint256: nonpayable

interface CryptoLegacyPool:
    def exchange(_i: uint256, _j: uint256, _dx: uint256, _min_dy: uint256, _use_eth: bool = False) -> uint256: payable

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface CurveAddressProvider:
    def get_address(_id: uint256) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

flag PoolType:
    STABLESWAP_NG
    TWO_CRYPTO_NG
    TRICRYPTO_NG
    TWO_CRYPTO
    METAPOOL
    CRYPTO

struct PoolData:
    pool: address
    fromIndex: int128
    toIndex: int128
    poolType: PoolType

struct CurveRegistries:
    StableSwapNg: address
    TwoCryptoNg: address
    TricryptoNg: address
    TwoCrypto: address
    MetaPool: address

event CurveSwap:
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

event PreferredPoolsSet:
    numPools: uint256

event CurveLegoIdSet:
    legoId: uint256

event CurveActivated:
    isActivated: bool

preferredPools: public(DynArray[address, MAX_POOLS])

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

CURVE_META_REGISTRY: public(immutable(address))
CURVE_REGISTRIES: public(immutable(CurveRegistries))

# curve ids
METAPOOL_FACTORY_ID: constant(uint256) = 3 # 0x3093f9B57A428F3EB6285a589cb35bEA6e78c336
TWO_CRYPTO_FACTORY_ID: constant(uint256) = 6 # 0x5EF72230578b3e399E6C6F4F6360edF95e83BBfd
META_REGISTRY_ID: constant(uint256) = 7 # 0x87DD13Dd25a1DBde0E1EdcF5B8Fa6cfff7eABCaD
TRICRYPTO_NG_FACTORY_ID: constant(uint256) = 11 # 0xA5961898870943c68037F6848d2D866Ed2016bcB
STABLESWAP_NG_FACTORY_ID: constant(uint256) = 12 # 0xd2002373543Ce3527023C75e7518C274A51ce712
TWO_CRYPTO_NG_FACTORY_ID: constant(uint256) = 13 # 0xc9Fe0C63Af9A39402e8a5514f9c43Af0322b665F

MAX_POOLS: constant(uint256) = 50


@deploy
def __init__(_curveAddressProvider: address, _addyRegistry: address):
    assert empty(address) not in [_curveAddressProvider, _addyRegistry] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(_addyRegistry)

    CURVE_META_REGISTRY = staticcall CurveAddressProvider(_curveAddressProvider).get_address(META_REGISTRY_ID)
    CURVE_REGISTRIES = CurveRegistries(
        StableSwapNg= staticcall CurveAddressProvider(_curveAddressProvider).get_address(STABLESWAP_NG_FACTORY_ID),
        TwoCryptoNg= staticcall CurveAddressProvider(_curveAddressProvider).get_address(TWO_CRYPTO_NG_FACTORY_ID),
        TricryptoNg= staticcall CurveAddressProvider(_curveAddressProvider).get_address(TRICRYPTO_NG_FACTORY_ID),
        TwoCrypto= staticcall CurveAddressProvider(_curveAddressProvider).get_address(TWO_CRYPTO_FACTORY_ID),
        MetaPool= staticcall CurveAddressProvider(_curveAddressProvider).get_address(METAPOOL_FACTORY_ID),
    )


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [CURVE_META_REGISTRY]


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


#############
# Liquidity #
#############


@external
def addLiquidity(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountOut: uint256,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256, uint256, uint256):
    # not implemented
    return 0, 0, 0, 0, 0, 0


# remove liq


@external
def removeLiquidity(
    _lpToken: address,
    _lpAmount: uint256,
    _tokenA: address,
    _tokenB: address,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256, uint256):
    # not implemented
    return 0, 0, 0, 0, 0


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

    # get pool data
    p: PoolData = empty(PoolData)
    if _pool != empty(address):
        p = self._getPoolData(_pool, _tokenIn, _tokenOut)
    else:
        p = self._findBestPool(_tokenIn, _tokenOut)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amountIn, staticcall IERC20(_tokenIn).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenIn).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed
    swapAmount: uint256 = min(transferAmount, staticcall IERC20(_tokenIn).balanceOf(self))

    # swap assets via lego partner
    toAmount: uint256 = self._swapTokensInPool(p, _tokenIn, _tokenOut, swapAmount, _minAmountOut, _recipient)

    # refund if full swap didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_tokenIn).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_tokenIn).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        swapAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_tokenIn, swapAmount, _tokenOut, toAmount, _oracleRegistry)
    log CurveSwap(msg.sender, _tokenIn, _tokenOut, swapAmount, toAmount, usdValue, _recipient)
    return swapAmount, toAmount, refundAssetAmount, usdValue


################
# Swap In Pool #
################


@internal
def _swapTokensInPool(
    _p: PoolData,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _recipient: address,
) -> uint256:
    toAmount: uint256 = 0

    # approve token in
    assert extcall IERC20(_tokenIn).approve(_p.pool, _amountIn, default_return_value=True) # dev: approval failed

    # stable ng
    if _p.poolType == PoolType.STABLESWAP_NG:
        toAmount = extcall CommonCurvePool(_p.pool).exchange(_p.fromIndex, _p.toIndex, _amountIn, _minAmountOut, _recipient)

    # two crypto ng
    elif _p.poolType == PoolType.TWO_CRYPTO_NG:
        toAmount = extcall TwoCryptoNgPool(_p.pool).exchange(convert(_p.fromIndex, uint256), convert(_p.toIndex, uint256), _amountIn, _minAmountOut, _recipient)

    # two crypto + tricrypto ng pools
    elif _p.poolType == PoolType.TRICRYPTO_NG or _p.poolType == PoolType.TWO_CRYPTO:
        toAmount = extcall TwoCryptoPool(_p.pool).exchange(convert(_p.fromIndex, uint256), convert(_p.toIndex, uint256), _amountIn, _minAmountOut, False, _recipient)

    # meta pools
    elif _p.poolType == PoolType.METAPOOL:
        if staticcall CurveMetaRegistry(CURVE_META_REGISTRY).is_meta(_p.pool):
            raise "Not Implemented"
        else:
            toAmount = extcall CommonCurvePool(_p.pool).exchange(_p.fromIndex, _p.toIndex, _amountIn, _minAmountOut, _recipient)

    # crypto v1
    else:
        toAmount = extcall CryptoLegacyPool(_p.pool).exchange(convert(_p.fromIndex, uint256), convert(_p.toIndex, uint256), _amountIn, _minAmountOut, False)
        assert extcall IERC20(_tokenOut).transfer(_recipient, toAmount, default_return_value=True) # dev: transfer failed

    # reset approvals
    assert extcall IERC20(_tokenIn).approve(_p.pool, 0, default_return_value=True) # dev: approval failed

    assert toAmount != 0 # dev: no tokens swapped
    return toAmount


#############
# Pool Data #
#############


@view
@external
def findBestPool(_tokenIn: address, _tokenOut: address) -> PoolData:
    return self._findBestPool(_tokenIn, _tokenOut)


@view
@internal
def _findBestPool(_tokenIn: address, _tokenOut: address) -> PoolData:
    bestLiquidity: uint256 = 0
    bestPoolData: PoolData = empty(PoolData)
    metaRegistry: address = CURVE_META_REGISTRY

    pools: DynArray[address, MAX_POOLS] = staticcall CurveMetaRegistry(metaRegistry).find_pools_for_coins(_tokenIn, _tokenOut)
    assert len(pools) != 0 # dev: no pools found

    preferredPools: DynArray[address, MAX_POOLS] = self.preferredPools
    for i: uint256 in range(len(pools), bound=MAX_POOLS):
        pool: address = pools[i]
        if pool == empty(address):
            continue

        na: bool = False

        # check if pool is preferred
        if pool in preferredPools:
            bestPoolData = PoolData(pool=pool, fromIndex=0, toIndex=0, poolType=empty(PoolType))
            bestPoolData.fromIndex, bestPoolData.toIndex, na = staticcall CurveMetaRegistry(metaRegistry).get_coin_indices(pool, _tokenIn, _tokenOut)
            break

        # balances
        balances: uint256[8] = staticcall CurveMetaRegistry(metaRegistry).get_underlying_balances(pool)
        if balances[0] == 0:
            continue

        # token indexes 
        fromIndex: int128 = 0
        toIndex: int128 = 0
        fromIndex, toIndex, na = staticcall CurveMetaRegistry(metaRegistry).get_coin_indices(pool, _tokenIn, _tokenOut)
        
        # compare liquidity
        liquidity: uint256 = balances[fromIndex] + balances[toIndex]
        if liquidity > bestLiquidity:
            bestLiquidity = liquidity
            bestPoolData = PoolData(pool=pool, fromIndex=fromIndex, toIndex=toIndex, poolType=empty(PoolType))

    assert bestPoolData.pool != empty(address) # dev: no pool found
    bestPoolData.poolType = self._getPoolType(bestPoolData.pool, metaRegistry)
    return bestPoolData


@view
@external
def getPoolData(_pool: address, _tokenIn: address, _tokenOut: address) -> PoolData:
    return self._getPoolData(_pool, _tokenIn, _tokenOut)


@view
@internal
def _getPoolData(_pool: address, _tokenIn: address, _tokenOut: address) -> PoolData:
    metaRegistry: address = CURVE_META_REGISTRY

    # check if tokens are in pool
    coins: address[8] = staticcall CurveMetaRegistry(metaRegistry).get_underlying_coins(_pool)
    assert _tokenIn in coins and _tokenOut in coins # dev: invalid tokens

    # get indices
    fromIndex: int128 = 0
    toIndex: int128 = 0
    na: bool = False
    fromIndex, toIndex, na = staticcall CurveMetaRegistry(metaRegistry).get_coin_indices(_pool, _tokenIn, _tokenOut)

    return PoolData(
        pool=_pool,
        fromIndex=fromIndex,
        toIndex=toIndex,
        poolType=self._getPoolType(_pool, metaRegistry),
    )


@view
@internal
def _getPoolType(_pool: address, _metaRegistry: address) -> PoolType:
    # check what type of pool this is based on where it's registered on Curve
    registryHandlers: address[10] = staticcall CurveMetaRegistry(_metaRegistry).get_registry_handlers_from_pool(_pool)
    baseRegistry: address = staticcall CurveMetaRegistry(_metaRegistry).get_base_registry(registryHandlers[0])

    curveRegistries: CurveRegistries = CURVE_REGISTRIES
    poolType: PoolType = empty(PoolType)
    if baseRegistry == curveRegistries.StableSwapNg:
        poolType = PoolType.STABLESWAP_NG
    elif baseRegistry == curveRegistries.TwoCryptoNg:
        poolType = PoolType.TWO_CRYPTO_NG
    elif baseRegistry == curveRegistries.TricryptoNg:
        poolType = PoolType.TRICRYPTO_NG
    elif baseRegistry == curveRegistries.TwoCrypto:
        poolType = PoolType.TWO_CRYPTO
    elif baseRegistry == curveRegistries.MetaPool:
        poolType = PoolType.METAPOOL
    else:
        poolType = PoolType.CRYPTO
    return poolType


###################
# Preferred Pools #
###################


@external
def setPreferredPools(_pools: DynArray[address, MAX_POOLS]) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    pools: DynArray[address, MAX_POOLS] = []
    for i: uint256 in range(len(_pools), bound=MAX_POOLS):
        p: address = _pools[i]
        if p == empty(address):
            continue
        if p not in pools and staticcall CurveMetaRegistry(CURVE_META_REGISTRY).is_registered(p):
            pools.append(p)

    self.preferredPools = pools
    log PreferredPoolsSet(len(pools))
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
    log CurveLegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log CurveActivated(_shouldActivate)