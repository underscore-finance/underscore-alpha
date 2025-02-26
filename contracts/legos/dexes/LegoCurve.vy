# @version 0.4.0
# pragma optimize codesize

implements: LegoDex
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed
from interfaces import LegoDex

interface CurveMetaRegistry:
    def get_coin_indices(_pool: address, _from: address, _to: address) -> (int128, int128, bool): view
    def find_pools_for_coins(_from: address, _to: address) -> DynArray[address, MAX_POOLS]: view
    def get_registry_handlers_from_pool(_pool: address) -> address[10]: view
    def get_pool_from_lp_token(_lpToken: address) -> address: view
    def get_base_registry(_addr: address) -> address: view
    def get_balances(_pool: address) -> uint256[8]: view
    def get_coins(_pool: address) -> address[8]: view
    def get_n_coins(_pool: address) -> uint256: view
    def get_lp_token(_pool: address) -> address: view
    def is_registered(_pool: address) -> bool: view
    def is_meta(_pool: address) -> bool: view

interface TwoCryptoPool:
    def remove_liquidity_one_coin(_lpBurnAmount: uint256, _index: uint256, _minAmountOut: uint256, _useEth: bool = False, _recipient: address = msg.sender) -> uint256: nonpayable
    def exchange(_i: uint256, _j: uint256, _dx: uint256, _min_dy: uint256, _use_eth: bool = False, _receiver: address = msg.sender) -> uint256: payable
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: uint256[2], _useEth: bool = False, _recipient: address = msg.sender): nonpayable
    def add_liquidity(_amounts: uint256[2], _minLpAmount: uint256, _useEth: bool = False, _recipient: address = msg.sender) -> uint256: payable
    def calc_withdraw_one_coin(_burnAmount: uint256, _index: uint256) -> uint256: view
    def calc_token_amount(_amounts: uint256[2]) -> uint256: view

interface TwoCryptoNgPool:
    def remove_liquidity_one_coin(_lpBurnAmount: uint256, _index: uint256, _minAmountOut: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: uint256[2], _recipient: address = msg.sender) -> uint256[2]: nonpayable
    def exchange(i: uint256, j: uint256, dx: uint256, min_dy: uint256, receiver: address = msg.sender) -> uint256: nonpayable
    def add_liquidity(_amounts: uint256[2], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_withdraw_one_coin(_burnAmount: uint256, _index: uint256) -> uint256: view
    def calc_token_amount(_amounts: uint256[2], _isDeposit: bool) -> uint256: view

interface StableNgTwo:
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: DynArray[uint256, 2], _recipient: address = msg.sender, _claimAdminFees: bool = True) -> DynArray[uint256, 2]: nonpayable
    def remove_liquidity_one_coin(_lpBurnAmount: uint256, _index: int128, _minAmountOut: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def add_liquidity(_amounts: DynArray[uint256, 2], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_token_amount(_amounts: DynArray[uint256, 2], _isDeposit: bool) -> uint256: view
    def calc_withdraw_one_coin(_burnAmount: uint256, _index: int128) -> uint256: view

interface TriCryptoPool:
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: uint256[3], _useEth: bool = False, _recipient: address = msg.sender, _claimAdminFees: bool = True) -> uint256[3]: nonpayable
    def remove_liquidity_one_coin(_lpBurnAmount: uint256, _index: uint256, _minAmountOut: uint256, _useEth: bool = False, _recipient: address = msg.sender) -> uint256: nonpayable
    def add_liquidity(_amounts: uint256[3], _minLpAmount: uint256, _useEth: bool = False, _recipient: address = msg.sender) -> uint256: payable
    def calc_withdraw_one_coin(_burnAmount: uint256, _index: uint256) -> uint256: view
    def calc_token_amount(_amounts: uint256[3], _isDeposit: bool) -> uint256: view

interface MetaPoolTwo:
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: uint256[2], _recipient: address = msg.sender) -> uint256[2]: nonpayable
    def add_liquidity(_amounts: uint256[2], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_token_amount(_amounts: uint256[2], _isDeposit: bool) -> uint256: view

interface MetaPoolThree:
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: uint256[3], _recipient: address = msg.sender) -> uint256[3]: nonpayable
    def add_liquidity(_amounts: uint256[3], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_token_amount(_amounts: uint256[3], _isDeposit: bool) -> uint256: view

interface MetaPoolFour:
    def remove_liquidity(_lpBurnAmount: uint256, _minAmountsOut: uint256[4], _recipient: address = msg.sender) -> uint256[4]: nonpayable
    def add_liquidity(_amounts: uint256[4], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_token_amount(_amounts: uint256[4], _isDeposit: bool) -> uint256: view

interface MetaPoolCommon:
    def remove_liquidity_one_coin(_lpBurnAmount: uint256, _index: int128, _minAmountOut: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_withdraw_one_coin(_burnAmount: uint256, _index: int128) -> uint256: view

interface StableNgThree:
    def add_liquidity(_amounts: DynArray[uint256, 3], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_token_amount(_amounts: DynArray[uint256, 3], _isDeposit: bool) -> uint256: view

interface StableNgFour:
    def add_liquidity(_amounts: DynArray[uint256, 4], _minLpAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def calc_token_amount(_amounts: DynArray[uint256, 4], _isDeposit: bool) -> uint256: view

interface CommonCurvePool:
    def exchange(_i: int128, _j: int128, _dx: uint256, _min_dy: uint256, _receiver: address = msg.sender) -> uint256: nonpayable
    def fee() -> uint256: view

interface CryptoLegacyPool:
    def exchange(_i: uint256, _j: uint256, _dx: uint256, _min_dy: uint256, _use_eth: bool = False) -> uint256: payable

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface CurveAddressProvider:
    def get_address(_id: uint256) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

interface CurveRateProvider:
    def get_quotes(_tokenIn: address, _tokenOut: address, _amountIn: uint256) -> DynArray[Quote, MAX_QUOTES]: view
    def get_aggregated_rate(_tokenIn: address, _tokenOut: address) -> uint256: view


flag PoolType:
    STABLESWAP_NG
    TWO_CRYPTO_NG
    TRICRYPTO_NG
    TWO_CRYPTO
    METAPOOL
    CRYPTO

struct Quote:
    source_token_index: uint256
    dest_token_index: uint256
    is_underlying: bool
    amount_out: uint256
    pool: address
    source_token_pool_balance: uint256
    dest_token_pool_balance: uint256
    pool_type: uint8

struct PoolData:
    pool: address
    indexTokenA: uint256
    indexTokenB: uint256
    poolType: PoolType
    numCoins: uint256

struct BestPool:
    pool: address
    fee: uint256
    liquidity: uint256
    numCoins: uint256

struct CurveRegistries:
    StableSwapNg: address
    TwoCryptoNg: address
    TricryptoNg: address
    TwoCrypto: address
    MetaPool: address
    RateProvider: address
event CurveSwap:
    sender: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    amountIn: uint256
    amountOut: uint256
    usdValue: uint256
    recipient: address

event CurveLiquidityAdded:
    sender: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    amountA: uint256
    amountB: uint256
    lpAmountReceived: uint256
    usdValue: uint256
    recipient: address

event CurveLiquidityRemoved:
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
RATE_PROVIDER_ID: constant(uint256) = 18 # 0x33e72383472f77B0C6d8F791D1613C75aE2C5915

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_POOLS: constant(uint256) = 50
MAX_QUOTES: constant(uint256) = 100


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
        RateProvider= staticcall CurveAddressProvider(_curveAddressProvider).get_address(RATE_PROVIDER_ID),
    )


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
        p = self._getPoolData(_pool, _tokenIn, _tokenOut, CURVE_META_REGISTRY)
    else:
        p = self._getBestPoolForSwap(_tokenIn, _tokenOut, CURVE_META_REGISTRY)

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

    usdValue: uint256 = self._getUsdValue(_tokenIn, swapAmount, _tokenOut, toAmount, True, _oracleRegistry)
    log CurveSwap(msg.sender, _tokenIn, _tokenOut, swapAmount, toAmount, usdValue, _recipient)
    return swapAmount, toAmount, refundAssetAmount, usdValue


# swap in pool


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
        toAmount = extcall CommonCurvePool(_p.pool).exchange(convert(_p.indexTokenA, int128), convert(_p.indexTokenB, int128), _amountIn, _minAmountOut, _recipient)

    # two crypto ng
    elif _p.poolType == PoolType.TWO_CRYPTO_NG:
        toAmount = extcall TwoCryptoNgPool(_p.pool).exchange(_p.indexTokenA, _p.indexTokenB, _amountIn, _minAmountOut, _recipient)

    # two crypto + tricrypto ng pools
    elif _p.poolType == PoolType.TRICRYPTO_NG or _p.poolType == PoolType.TWO_CRYPTO:
        toAmount = extcall TwoCryptoPool(_p.pool).exchange(_p.indexTokenA, _p.indexTokenB, _amountIn, _minAmountOut, False, _recipient)

    # meta pools
    elif _p.poolType == PoolType.METAPOOL:
        if staticcall CurveMetaRegistry(CURVE_META_REGISTRY).is_meta(_p.pool):
            raise "Not Implemented"
        else:
            toAmount = extcall CommonCurvePool(_p.pool).exchange(convert(_p.indexTokenA, int128), convert(_p.indexTokenB, int128), _amountIn, _minAmountOut, _recipient)

    # crypto v1
    else:
        toAmount = extcall CryptoLegacyPool(_p.pool).exchange(_p.indexTokenA, _p.indexTokenB, _amountIn, _minAmountOut, False)
        assert extcall IERC20(_tokenOut).transfer(_recipient, toAmount, default_return_value=True) # dev: transfer failed

    # reset approvals
    assert extcall IERC20(_tokenIn).approve(_p.pool, 0, default_return_value=True) # dev: approval failed

    assert toAmount != 0 # dev: no tokens swapped
    return toAmount


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

    assert empty(address) not in [_tokenA, _tokenB] # dev: invalid tokens
    assert _tokenA != _tokenB # dev: invalid tokens

    # pre balances
    preLegoBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    preLegoBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)

    # token a
    liqAmountA: uint256 = min(_amountA, staticcall IERC20(_tokenA).balanceOf(msg.sender))
    if liqAmountA != 0:
        assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, liqAmountA, default_return_value=True) # dev: transfer failed
        liqAmountA = min(liqAmountA, staticcall IERC20(_tokenA).balanceOf(self))
        assert extcall IERC20(_tokenA).approve(_pool, liqAmountA, default_return_value=True) # dev: approval failed

    # token b
    liqAmountB: uint256 = min(_amountB, staticcall IERC20(_tokenB).balanceOf(msg.sender))
    if liqAmountB != 0:
        assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, liqAmountB, default_return_value=True) # dev: transfer failed
        liqAmountB = min(liqAmountB, staticcall IERC20(_tokenB).balanceOf(self))
        assert extcall IERC20(_tokenB).approve(_pool, liqAmountB, default_return_value=True) # dev: approval failed

    assert liqAmountA != 0 or liqAmountB != 0 # dev: need at least one token amount

    # pool data
    metaRegistry: address = CURVE_META_REGISTRY
    p: PoolData = self._getPoolData(_pool, _tokenA, _tokenB, metaRegistry)

    # add liquidity
    lpAmountReceived: uint256 = 0
    if p.poolType == PoolType.STABLESWAP_NG:
        lpAmountReceived = self._addLiquidityStableNg(p, liqAmountA, liqAmountB, _minLpAmount, _recipient)
    elif p.poolType == PoolType.TWO_CRYPTO_NG:
        lpAmountReceived = self._addLiquidityTwoCryptoNg(p, liqAmountA, liqAmountB, _minLpAmount, _recipient)
    elif p.poolType == PoolType.TWO_CRYPTO:
        lpAmountReceived = self._addLiquidityTwoCrypto(p, liqAmountA, liqAmountB, _minLpAmount, _recipient)
    elif p.poolType == PoolType.TRICRYPTO_NG:
        lpAmountReceived = self._addLiquidityTricrypto(p, liqAmountA, liqAmountB, _minLpAmount, _recipient)
    elif p.poolType == PoolType.METAPOOL and not staticcall CurveMetaRegistry(metaRegistry).is_meta(p.pool):
        lpAmountReceived = self._addLiquidityMetaPool(p, liqAmountA, liqAmountB, _minLpAmount, _recipient)
    assert lpAmountReceived != 0 # dev: no liquidity added

    # handle token a refunds / approvals
    refundAssetAmountA: uint256 = 0
    if liqAmountA != 0:
        assert extcall IERC20(_tokenA).approve(_pool, 0, default_return_value=True) # dev: approval failed

        currentLegoBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
        if currentLegoBalanceA > preLegoBalanceA:
            refundAssetAmountA = currentLegoBalanceA - preLegoBalanceA
            assert extcall IERC20(_tokenA).transfer(msg.sender, refundAssetAmountA, default_return_value=True) # dev: transfer failed
            liqAmountA -= refundAssetAmountA

    # handle token b refunds / approvals
    refundAssetAmountB: uint256 = 0
    if liqAmountB != 0:
        assert extcall IERC20(_tokenB).approve(_pool, 0, default_return_value=True) # dev: approval failed

        currentLegoBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)
        if currentLegoBalanceB > preLegoBalanceB:
            refundAssetAmountB = currentLegoBalanceB - preLegoBalanceB
            assert extcall IERC20(_tokenB).transfer(msg.sender, refundAssetAmountB, default_return_value=True) # dev: transfer failed
            liqAmountB -= refundAssetAmountB

    usdValue: uint256 = self._getUsdValue(_tokenA, liqAmountA, _tokenB, liqAmountB, False, _oracleRegistry)
    log CurveLiquidityAdded(msg.sender, _tokenA, _tokenB, liqAmountA, liqAmountB, lpAmountReceived, usdValue, _recipient)
    return lpAmountReceived, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, 0


@internal
def _addLiquidityStableNg(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
    _minLpAmount: uint256,
    _recipient: address,
) -> uint256:
    lpAmountReceived: uint256 = 0

    if _p.numCoins == 2:
        amounts: DynArray[uint256, 2] = [0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        lpAmountReceived = extcall StableNgTwo(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)

    elif _p.numCoins == 3:
        amounts: DynArray[uint256, 3] = [0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        lpAmountReceived = extcall StableNgThree(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)

    elif _p.numCoins == 4:
        amounts: DynArray[uint256, 4] = [0, 0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        lpAmountReceived = extcall StableNgFour(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)

    return lpAmountReceived


@internal
def _addLiquidityTwoCryptoNg(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
    _minLpAmount: uint256,
    _recipient: address,
) -> uint256:
    amounts: uint256[2] = [0, 0]
    amounts[_p.indexTokenA] = _liqAmountA
    amounts[_p.indexTokenB] = _liqAmountB
    return extcall TwoCryptoNgPool(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)


@internal
def _addLiquidityTwoCrypto(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
    _minLpAmount: uint256,
    _recipient: address,
) -> uint256:
    amounts: uint256[2] = [0, 0]
    amounts[_p.indexTokenA] = _liqAmountA
    amounts[_p.indexTokenB] = _liqAmountB
    return extcall TwoCryptoPool(_p.pool).add_liquidity(amounts, _minLpAmount, False, _recipient)


@internal
def _addLiquidityTricrypto(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
    _minLpAmount: uint256,
    _recipient: address,
) -> uint256:
    amounts: uint256[3] = [0, 0, 0]
    amounts[_p.indexTokenA] = _liqAmountA
    amounts[_p.indexTokenB] = _liqAmountB
    return extcall TriCryptoPool(_p.pool).add_liquidity(amounts, _minLpAmount, False, _recipient)


@internal
def _addLiquidityMetaPool(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
    _minLpAmount: uint256,
    _recipient: address,
) -> uint256:
    lpAmountReceived: uint256 = 0

    if _p.numCoins == 2:
        amounts: uint256[2] = [0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        lpAmountReceived = extcall MetaPoolTwo(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)

    elif _p.numCoins == 3:
        amounts: uint256[3] = [0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        lpAmountReceived = extcall MetaPoolThree(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)

    elif _p.numCoins == 4:
        amounts: uint256[4] = [0, 0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        lpAmountReceived = extcall MetaPoolFour(_p.pool).add_liquidity(amounts, _minLpAmount, _recipient)

    return lpAmountReceived


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

    # if one of the tokens is empty, it means they only want to remove liquidity for one token
    assert _tokenA != empty(address) or _tokenB != empty(address) # dev: invalid tokens
    assert _tokenA != _tokenB # dev: invalid tokens

    isEmptyTokenA: bool = _tokenA == empty(address)
    isOneCoinRemoval: bool = isEmptyTokenA or _tokenB == empty(address)

    # pre balance
    preLegoBalance: uint256 = staticcall IERC20(_lpToken).balanceOf(self)

    # lp token amount
    lpAmount: uint256 = min(_liqToRemove, staticcall IERC20(_lpToken).balanceOf(msg.sender))
    assert lpAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_lpToken).transferFrom(msg.sender, self, lpAmount, default_return_value=True) # dev: transfer failed
    lpAmount = min(lpAmount, staticcall IERC20(_lpToken).balanceOf(self))

    # approvals
    assert extcall IERC20(_lpToken).approve(_pool, lpAmount, default_return_value=True) # dev: approval failed

    # pool data
    metaRegistry: address = CURVE_META_REGISTRY
    p: PoolData = self._getPoolData(_pool, _tokenA, _tokenB, metaRegistry)

    # remove liquidity
    amountA: uint256 = 0
    amountB: uint256 = 0
    if p.poolType == PoolType.STABLESWAP_NG:
        if isOneCoinRemoval:
            amountA, amountB = self._removeLiquidityStableNgOneCoin(p, isEmptyTokenA, lpAmount, _minAmountA, _minAmountB, _recipient)
        else:
            amountA, amountB = self._removeLiquidityStableNg(p, lpAmount, _minAmountA, _minAmountB, _recipient)
    elif p.poolType == PoolType.TWO_CRYPTO_NG:
        if isOneCoinRemoval:
            amountA, amountB = self._removeLiquidityTwoCryptoNgOneCoin(p, isEmptyTokenA, lpAmount, _minAmountA, _minAmountB, _recipient)
        else:
            amountA, amountB = self._removeLiquidityTwoCryptoNg(p, lpAmount, _minAmountA, _minAmountB, _recipient)
    elif p.poolType == PoolType.TWO_CRYPTO:
        if isOneCoinRemoval:
            amountA, amountB = self._removeLiquidityTwoCryptoOneCoin(p, isEmptyTokenA, lpAmount, _minAmountA, _minAmountB, _recipient)
        else:
            amountA, amountB = self._removeLiquidityTwoCrypto(p, lpAmount, _tokenA, _tokenB, _minAmountA, _minAmountB, _recipient)
    elif p.poolType == PoolType.TRICRYPTO_NG:
        if isOneCoinRemoval:
            amountA, amountB = self._removeLiquidityTricryptoOneCoin(p, isEmptyTokenA, lpAmount, _minAmountA, _minAmountB, _recipient)
        else:
            amountA, amountB = self._removeLiquidityTricrypto(p, lpAmount, _minAmountA, _minAmountB, _recipient)
    elif p.poolType == PoolType.METAPOOL and not staticcall CurveMetaRegistry(metaRegistry).is_meta(p.pool):
        if isOneCoinRemoval:
            amountA, amountB = self._removeLiquidityMetaPoolOneCoin(p, isEmptyTokenA, lpAmount, _minAmountA, _minAmountB, _recipient)
        else:
            amountA, amountB = self._removeLiquidityMetaPool(p, lpAmount, _minAmountA, _minAmountB, _recipient)
    assert amountA != 0 or amountB != 0 # dev: nothing removed

    # reset approvals
    assert extcall IERC20(_lpToken).approve(_pool, 0, default_return_value=True) # dev: approval failed

    # refund if full liquidity was not removed
    currentLegoBalance: uint256 = staticcall IERC20(_lpToken).balanceOf(self)
    refundedLpAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundedLpAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_lpToken).transfer(msg.sender, refundedLpAmount, default_return_value=True) # dev: transfer failed
        lpAmount -= refundedLpAmount

    usdValue: uint256 = self._getUsdValue(_tokenA, amountA, _tokenB, amountB, False, _oracleRegistry)
    log CurveLiquidityRemoved(msg.sender, _pool, _tokenA, _tokenB, amountA, amountB, _lpToken, lpAmount, usdValue, _recipient)
    return amountA, amountB, usdValue, lpAmount, refundedLpAmount, refundedLpAmount != 0


# stable ng


@internal
def _removeLiquidityStableNgOneCoin(
    _p: PoolData,
    _isEmptyTokenA: bool,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    tokenIndex: uint256 = 0
    minAmountOut: uint256 = 0
    tokenIndex, minAmountOut = self._getTokenIndexAndMinAmountOut(_isEmptyTokenA, _p.indexTokenA, _p.indexTokenB, _minAmountA, _minAmountB)
    amountOut: uint256 = extcall StableNgTwo(_p.pool).remove_liquidity_one_coin(_lpAmount, convert(tokenIndex, int128), minAmountOut, _recipient)
    return self._getTokenAmounts(_isEmptyTokenA, amountOut)


@internal
def _removeLiquidityStableNg(
    _p: PoolData,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):

    # only supporting 2-coin pools, can't give minAmountsOut for other coins
    assert _p.numCoins == 2 # dev: invalid pool

    minAmountsOut: DynArray[uint256, 2] = [0, 0]
    minAmountsOut[_p.indexTokenA] = _minAmountA
    minAmountsOut[_p.indexTokenB] = _minAmountB

    # remove liquidity
    amountsOut: DynArray[uint256, 2] = extcall StableNgTwo(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, _recipient, False)
    return amountsOut[_p.indexTokenA], amountsOut[_p.indexTokenB]


# two crypto ng


@internal
def _removeLiquidityTwoCryptoNgOneCoin(
    _p: PoolData,
    _isEmptyTokenA: bool,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    tokenIndex: uint256 = 0
    minAmountOut: uint256 = 0
    tokenIndex, minAmountOut = self._getTokenIndexAndMinAmountOut(_isEmptyTokenA, _p.indexTokenA, _p.indexTokenB, _minAmountA, _minAmountB)
    amountOut: uint256 = extcall TwoCryptoNgPool(_p.pool).remove_liquidity_one_coin(_lpAmount, tokenIndex, minAmountOut, _recipient)
    return self._getTokenAmounts(_isEmptyTokenA, amountOut)


@internal
def _removeLiquidityTwoCryptoNg(
    _p: PoolData,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):

    # only supporting 2-coin pools, can't give minAmountsOut for other coins
    assert _p.numCoins == 2 # dev: invalid pool

    minAmountsOut: uint256[2] = [0, 0]
    minAmountsOut[_p.indexTokenA] = _minAmountA
    minAmountsOut[_p.indexTokenB] = _minAmountB

    # remove liquidity
    amountsOut: uint256[2] = extcall TwoCryptoNgPool(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, _recipient)
    return amountsOut[_p.indexTokenA], amountsOut[_p.indexTokenB]


# two crypto


@internal
def _removeLiquidityTwoCryptoOneCoin(
    _p: PoolData,
    _isEmptyTokenA: bool,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    tokenIndex: uint256 = 0
    minAmountOut: uint256 = 0
    tokenIndex, minAmountOut = self._getTokenIndexAndMinAmountOut(_isEmptyTokenA, _p.indexTokenA, _p.indexTokenB, _minAmountA, _minAmountB)
    amountOut: uint256 = extcall TwoCryptoPool(_p.pool).remove_liquidity_one_coin(_lpAmount, tokenIndex, minAmountOut, False, _recipient)
    return self._getTokenAmounts(_isEmptyTokenA, amountOut)


@internal
def _removeLiquidityTwoCrypto(
    _p: PoolData,
    _lpAmount: uint256,
    _tokenA: address,
    _tokenB: address,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):

    # only supporting 2-coin pools
    assert _p.numCoins == 2 # dev: invalid pool

    # pre balances
    preBalTokenA: uint256 = staticcall IERC20(_tokenA).balanceOf(_recipient)
    preBalTokenB: uint256 = staticcall IERC20(_tokenB).balanceOf(_recipient)

    # organize min amounts out
    minAmountsOut: uint256[2] = [0, 0]
    minAmountsOut[_p.indexTokenA] = _minAmountA
    minAmountsOut[_p.indexTokenB] = _minAmountB

    # remove liquidity
    extcall TwoCryptoPool(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, False, _recipient)

    # get amounts
    amountA: uint256 = 0
    postBalTokenA: uint256 = staticcall IERC20(_tokenA).balanceOf(_recipient)
    if postBalTokenA > preBalTokenA:
        amountA = postBalTokenA - preBalTokenA

    amountB: uint256 = 0
    postBalTokenB: uint256 = staticcall IERC20(_tokenB).balanceOf(_recipient)
    if postBalTokenB > preBalTokenB:
        amountB = postBalTokenB - preBalTokenB

    return amountA, amountB


# tricrypto ng


@internal
def _removeLiquidityTricryptoOneCoin(
    _p: PoolData,
    _isEmptyTokenA: bool,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    tokenIndex: uint256 = 0
    minAmountOut: uint256 = 0
    tokenIndex, minAmountOut = self._getTokenIndexAndMinAmountOut(_isEmptyTokenA, _p.indexTokenA, _p.indexTokenB, _minAmountA, _minAmountB)
    amountOut: uint256 = extcall TriCryptoPool(_p.pool).remove_liquidity_one_coin(_lpAmount, tokenIndex, minAmountOut, False, _recipient)
    return self._getTokenAmounts(_isEmptyTokenA, amountOut)


@internal
def _removeLiquidityTricrypto(
    _p: PoolData,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    minAmountsOut: uint256[3] = [0, 0, 0]
    minAmountsOut[_p.indexTokenA] = _minAmountA
    minAmountsOut[_p.indexTokenB] = _minAmountB

    # NOTE: user can only specify two min amounts out, the third will be set to zero

    # remove liquidity
    amountsOut: uint256[3] = extcall TriCryptoPool(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, False, _recipient, False)
    return amountsOut[_p.indexTokenA], amountsOut[_p.indexTokenB]


# meta pool


@internal
def _removeLiquidityMetaPoolOneCoin(
    _p: PoolData,
    _isEmptyTokenA: bool,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    tokenIndex: uint256 = 0
    minAmountOut: uint256 = 0
    tokenIndex, minAmountOut = self._getTokenIndexAndMinAmountOut(_isEmptyTokenA, _p.indexTokenA, _p.indexTokenB, _minAmountA, _minAmountB)
    amountOut: uint256 = extcall MetaPoolCommon(_p.pool).remove_liquidity_one_coin(_lpAmount, convert(tokenIndex, int128), minAmountOut, _recipient)
    return self._getTokenAmounts(_isEmptyTokenA, amountOut)


@internal
def _removeLiquidityMetaPool(
    _p: PoolData,
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _recipient: address,
) -> (uint256, uint256):
    amountA: uint256 = 0
    amountB: uint256 = 0

    # NOTE: user can only specify two min amounts out, the third/fourth will be set to zero

    if _p.numCoins == 2:
        minAmountsOut: uint256[2] = [0, 0]
        minAmountsOut[_p.indexTokenA] = _minAmountA
        minAmountsOut[_p.indexTokenB] = _minAmountB
        amountsOut: uint256[2] = extcall MetaPoolTwo(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, _recipient)
        amountA = amountsOut[_p.indexTokenA]
        amountB = amountsOut[_p.indexTokenB]

    elif _p.numCoins == 3:
        minAmountsOut: uint256[3] = [0, 0, 0]
        minAmountsOut[_p.indexTokenA] = _minAmountA
        minAmountsOut[_p.indexTokenB] = _minAmountB
        amountsOut: uint256[3] = extcall MetaPoolThree(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, _recipient)
        amountA = amountsOut[_p.indexTokenA]
        amountB = amountsOut[_p.indexTokenB]

    elif _p.numCoins == 4:
        minAmountsOut: uint256[4] = [0, 0, 0, 0]
        minAmountsOut[_p.indexTokenA] = _minAmountA
        minAmountsOut[_p.indexTokenB] = _minAmountB
        amountsOut: uint256[4] = extcall MetaPoolFour(_p.pool).remove_liquidity(_lpAmount, minAmountsOut, _recipient)
        amountA = amountsOut[_p.indexTokenA]
        amountB = amountsOut[_p.indexTokenB]

    else:
        raise "meta pool: pools beyond 4-coin are not supported"

    return amountA, amountB


# utils


@pure
@internal
def _getTokenIndexAndMinAmountOut(
    _isEmptyTokenA: bool,
    _indexTokenA: uint256,
    _indexTokenB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
) -> (uint256, uint256):
    tokenIndex: uint256 = _indexTokenA
    minAmountOut: uint256 = _minAmountA
    if _isEmptyTokenA:
        tokenIndex = _indexTokenB
        minAmountOut = _minAmountB
    return tokenIndex, minAmountOut


@pure
@internal
def _getTokenAmounts(_isEmptyTokenA: bool, _amountOut: uint256) -> (uint256, uint256):
    amountA: uint256 = 0
    amountB: uint256 = 0
    if _isEmptyTokenA:
        amountB = _amountOut
    else:
        amountA = _amountOut
    return amountA, amountB


#############
# Utilities #
#############


@view
@external
def getBestPool(_tokenA: address, _tokenB: address) -> BestPool:
    metaRegistry: address = CURVE_META_REGISTRY

    # all pools with tokens
    allPools: DynArray[address, MAX_POOLS] = staticcall CurveMetaRegistry(metaRegistry).find_pools_for_coins(_tokenA, _tokenB)
    if len(allPools) == 0:
        return empty(BestPool)

    # get deepest liquidity pool
    bestPoolAddr: address = empty(address)
    na1: int128 = 0
    na2: int128 = 0
    bestLiquidity: uint256 = 0
    bestPoolAddr, na1, na2, bestLiquidity = self._getDeepestLiqPool(_tokenA, _tokenB, allPools, metaRegistry)

    if bestPoolAddr == empty(address):
        return empty(BestPool)

    return BestPool(
        pool=bestPoolAddr,
        fee=staticcall CommonCurvePool(bestPoolAddr).fee() // 1000000, # normalize to have 100_00 denominator
        liquidity=bestLiquidity,
        numCoins=staticcall CurveMetaRegistry(metaRegistry).get_n_coins(bestPoolAddr),
    )


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [CURVE_META_REGISTRY]


@view
@external
def getLpToken(_pool: address) -> address:
    return staticcall CurveMetaRegistry(CURVE_META_REGISTRY).get_lp_token(_pool)


@view
@external
def getPoolForLpToken(_lpToken: address) -> address:
    return staticcall CurveMetaRegistry(CURVE_META_REGISTRY).get_pool_from_lp_token(_lpToken)


@view
@external
def getSwapAmountOut(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
) -> uint256:
    quotes: DynArray[Quote, MAX_QUOTES] = staticcall CurveRateProvider(CURVE_REGISTRIES.RateProvider).get_quotes(_tokenIn, _tokenOut, _amountIn)
    bestAmountOut: uint256 = 0
    for quote: Quote in quotes:
        if quote.amount_out > bestAmountOut:
            bestAmountOut = quote.amount_out
    return bestAmountOut


@view
@external
def getSwapAmountIn(
    _pool: address,
    _tokenIn: address,
    _tokenOut: address,
    _amountOut: uint256,
) -> uint256:
    rate: uint256 = staticcall CurveRateProvider(CURVE_REGISTRIES.RateProvider).get_aggregated_rate(_tokenIn, _tokenOut)
    if rate == 0:
        return 0
    decimalsTokenIn: uint256 = convert(staticcall IERC20Detailed(_tokenIn).decimals(), uint256)
    return _amountOut * (10 ** decimalsTokenIn) // rate


@view
@external
def getAddLiqAmountsIn(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _availAmountA: uint256,
    _availAmountB: uint256,
) -> (uint256, uint256, uint256):
    metaRegistry: address = CURVE_META_REGISTRY
    p: PoolData = self._getPoolData(_pool, _tokenA, _tokenB, metaRegistry)

    balances: uint256[8] = staticcall CurveMetaRegistry(metaRegistry).get_balances(_pool)
    reserveA: uint256 = balances[p.indexTokenA]
    reserveB: uint256 = balances[p.indexTokenB]

    # insufficient liquidity
    if reserveA == 0 or reserveB == 0:
        return 0, 0, 0

    # calculate optimal amounts
    amountA: uint256 = 0
    amountB: uint256 = 0
    amountA, amountB = self._getCorrectRatioAmounts(_availAmountA, _availAmountB, reserveA, reserveB)

    expectedLpAmount: uint256 = 0
    if p.poolType == PoolType.STABLESWAP_NG:
        expectedLpAmount = self._getAddLiqAmountsInStableNg(p, amountA, amountB)
    elif p.poolType == PoolType.TWO_CRYPTO_NG:
        expectedLpAmount = self._getAddLiqAmountsInCryptoNg(p, amountA, amountB)
    elif p.poolType == PoolType.TWO_CRYPTO:
        expectedLpAmount = self._getAddLiqAmountsInTwoCrypto(p, amountA, amountB)
    elif p.poolType == PoolType.TRICRYPTO_NG:
        expectedLpAmount = self._getAddLiqAmountsInTricrypto(p, amountA, amountB)
    elif p.poolType == PoolType.METAPOOL and not staticcall CurveMetaRegistry(metaRegistry).is_meta(p.pool):
        expectedLpAmount = self._getAddLiqAmountsInMetaPool(p, amountA, amountB)

    if expectedLpAmount == 0:
        return 0, 0, 0

    return amountA, amountB, expectedLpAmount


@view
@external
def getRemoveLiqAmountsOut(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpAmount: uint256,
) -> (uint256, uint256):
    metaRegistry: address = CURVE_META_REGISTRY
    p: PoolData = self._getPoolData(_pool, _tokenA, _tokenB, metaRegistry)

    # NOTE: in this case, allowing 0x0 for one token, signifying desire to withdraw just one token

    # normal scenario, 2-coin pool
    if _tokenA != empty(address) and _tokenB != empty(address):
        return self._getRemoveLiqAmountsOutTwoCoinPool(p, _tokenA, _tokenB, _lpAmount, metaRegistry)

    # withdraw just one token
    amountOut: uint256 = 0
    tokenIndex: uint256 = p.indexTokenA
    if _tokenA == empty(address):
        tokenIndex = p.indexTokenB

    # perform calculation
    if p.poolType == PoolType.STABLESWAP_NG:
        amountOut = staticcall StableNgTwo(p.pool).calc_withdraw_one_coin(_lpAmount, convert(tokenIndex, int128))
    elif p.poolType == PoolType.TWO_CRYPTO_NG:
        amountOut = staticcall TwoCryptoNgPool(p.pool).calc_withdraw_one_coin(_lpAmount, tokenIndex)
    elif p.poolType == PoolType.TWO_CRYPTO:
        amountOut = staticcall TwoCryptoPool(p.pool).calc_withdraw_one_coin(_lpAmount, tokenIndex)
    elif p.poolType == PoolType.TRICRYPTO_NG:
        amountOut = staticcall TriCryptoPool(p.pool).calc_withdraw_one_coin(_lpAmount, tokenIndex)
    elif p.poolType == PoolType.METAPOOL and not staticcall CurveMetaRegistry(metaRegistry).is_meta(p.pool):
        amountOut = staticcall MetaPoolCommon(p.pool).calc_withdraw_one_coin(_lpAmount, convert(tokenIndex, int128))

    # get in correct order
    amountA: uint256 = amountOut
    amountB: uint256 = 0
    if _tokenA == empty(address):
        amountA = 0
        amountB = amountOut

    return amountA, amountB


@view
@external
def getPriceUnsafe(_pool: address, _targetToken: address, _oracleRegistry: address = empty(address)) -> uint256:
    return 0


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
    usdValueA: uint256 = 0
    if _tokenA != empty(address) and _amountA != 0:
        usdValueA = staticcall OracleRegistry(oracleRegistry).getUsdValue(_tokenA, _amountA)
    usdValueB: uint256 = 0
    if _tokenB != empty(address) and _amountB != 0:
        usdValueB = staticcall OracleRegistry(oracleRegistry).getUsdValue(_tokenB, _amountB)
    if _isSwap:
        return max(usdValueA, usdValueB)
    else:
        return usdValueA + usdValueB


@view
@internal
def _getDeepestLiqPool(_tokenA: address, _tokenB: address, _allPools: DynArray[address, MAX_POOLS], _metaRegistry: address) -> (address, int128, int128, uint256):
    bestPoolAddr: address = empty(address)
    bestTokenAIndex: int128 = 0
    bestTokenBIndex: int128 = 0
    bestLiquidity: uint256 = 0

    for i: uint256 in range(len(_allPools), bound=MAX_POOLS):
        pool: address = _allPools[i]
        if pool == empty(address):
            continue

        # balances
        balances: uint256[8] = staticcall CurveMetaRegistry(_metaRegistry).get_balances(pool)
        if balances[0] == 0:
            continue

        # token indexes 
        indexTokenA: int128 = 0
        indexTokenB: int128 = 0
        na: bool = False
        indexTokenA, indexTokenB, na = staticcall CurveMetaRegistry(_metaRegistry).get_coin_indices(pool, _tokenA, _tokenB)

        # compare liquidity
        liquidity: uint256 = balances[indexTokenA] + balances[indexTokenB]
        if liquidity > bestLiquidity:
            bestPoolAddr = pool
            bestTokenAIndex = indexTokenA
            bestTokenBIndex = indexTokenB
            bestLiquidity = liquidity

    return bestPoolAddr, bestTokenAIndex, bestTokenBIndex, bestLiquidity


@view
@internal
def _getBestPoolForSwap(_tokenA: address, _tokenB: address, _metaRegistry: address) -> PoolData:
    allPools: DynArray[address, MAX_POOLS] = staticcall CurveMetaRegistry(_metaRegistry).find_pools_for_coins(_tokenA, _tokenB)
    if len(allPools) == 0:
        return empty(PoolData)

    bestPoolAddr: address = empty(address)
    bestTokenAIndex: int128 = 0
    bestTokenBIndex: int128 = 0

    # check preferred pools first
    preferredPools: DynArray[address, MAX_POOLS] = self.preferredPools
    for i: uint256 in range(len(preferredPools), bound=MAX_POOLS):
        preferredPool: address = preferredPools[i]
        if preferredPool in allPools:
            bestPoolAddr = preferredPool
            break

    # get missing data on preferred pool
    if bestPoolAddr != empty(address):
        na: bool = False
        bestTokenAIndex, bestTokenBIndex, na = staticcall CurveMetaRegistry(_metaRegistry).get_coin_indices(bestPoolAddr, _tokenA, _tokenB)

    # get deepest liquidity pool
    else:
        na: uint256 = 0
        bestPoolAddr, bestTokenAIndex, bestTokenBIndex, na = self._getDeepestLiqPool(_tokenA, _tokenB, allPools, _metaRegistry)

    if bestPoolAddr == empty(address):
        return empty(PoolData)

    return PoolData(
        pool=bestPoolAddr,
        indexTokenA=convert(bestTokenAIndex, uint256),
        indexTokenB=convert(bestTokenBIndex, uint256),
        poolType=self._getPoolType(bestPoolAddr, _metaRegistry),
        numCoins=staticcall CurveMetaRegistry(_metaRegistry).get_n_coins(bestPoolAddr),
    )


@view
@internal
def _getPoolData(_pool: address, _tokenA: address, _tokenB: address, _metaRegistry: address) -> PoolData:
    coins: address[8] = staticcall CurveMetaRegistry(_metaRegistry).get_coins(_pool)
    
    # validate tokens
    if _tokenA != empty(address):
        assert _tokenA in coins # dev: invalid tokens
    if _tokenB != empty(address):
        assert _tokenB in coins # dev: invalid tokens

    # get indices
    indexTokenA: uint256 = max_value(uint256)
    indexTokenB: uint256 = max_value(uint256)
    numCoins: uint256 = 0
    for coin: address in coins:
        if coin == empty(address):
            break
        if coin == _tokenA:
            indexTokenA = numCoins
        elif coin == _tokenB:
            indexTokenB = numCoins
        numCoins += 1

    return PoolData(
        pool=_pool,
        indexTokenA=indexTokenA,
        indexTokenB=indexTokenB,
        poolType=self._getPoolType(_pool, _metaRegistry),
        numCoins=numCoins,
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


@view
@internal
def _getAddLiqAmountsInStableNg(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
) -> uint256:
    expLpAmount: uint256 = 0

    if _p.numCoins == 2:
        amounts: DynArray[uint256, 2] = [0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        expLpAmount = staticcall StableNgTwo(_p.pool).calc_token_amount(amounts, True)

    elif _p.numCoins == 3:
        amounts: DynArray[uint256, 3] = [0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        expLpAmount = staticcall StableNgThree(_p.pool).calc_token_amount(amounts, True)

    elif _p.numCoins == 4:
        amounts: DynArray[uint256, 4] = [0, 0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        expLpAmount = staticcall StableNgFour(_p.pool).calc_token_amount(amounts, True)

    return expLpAmount


@view
@internal
def _getAddLiqAmountsInCryptoNg(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
) -> uint256:
    amounts: uint256[2] = [0, 0]
    amounts[_p.indexTokenA] = _liqAmountA
    amounts[_p.indexTokenB] = _liqAmountB
    return staticcall TwoCryptoNgPool(_p.pool).calc_token_amount(amounts, True)


@view
@internal
def _getAddLiqAmountsInTwoCrypto(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
) -> uint256:
    amounts: uint256[2] = [0, 0]
    amounts[_p.indexTokenA] = _liqAmountA
    amounts[_p.indexTokenB] = _liqAmountB
    return staticcall TwoCryptoPool(_p.pool).calc_token_amount(amounts)


@view
@internal
def _getAddLiqAmountsInTricrypto(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
) -> uint256:
    amounts: uint256[3] = [0, 0, 0]
    amounts[_p.indexTokenA] = _liqAmountA
    amounts[_p.indexTokenB] = _liqAmountB
    return staticcall TriCryptoPool(_p.pool).calc_token_amount(amounts, True)


@view
@internal
def _getAddLiqAmountsInMetaPool(
    _p: PoolData,
    _liqAmountA: uint256,
    _liqAmountB: uint256,
) -> uint256:
    expLpAmount: uint256 = 0

    if _p.numCoins == 2:
        amounts: uint256[2] = [0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        expLpAmount = staticcall MetaPoolTwo(_p.pool).calc_token_amount(amounts, True)

    elif _p.numCoins == 3:
        amounts: uint256[3] = [0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        expLpAmount = staticcall MetaPoolThree(_p.pool).calc_token_amount(amounts, True)

    elif _p.numCoins == 4:
        amounts: uint256[4] = [0, 0, 0, 0]
        amounts[_p.indexTokenA] = _liqAmountA
        amounts[_p.indexTokenB] = _liqAmountB
        expLpAmount = staticcall MetaPoolFour(_p.pool).calc_token_amount(amounts, True)

    return expLpAmount


@view
@internal
def _getRemoveLiqAmountsOutTwoCoinPool(
    _p: PoolData,
    _tokenA: address,
    _tokenB: address,
    _lpAmount: uint256,
    _metaRegistry: address,
) -> (uint256, uint256):

    # only supporting 2-coin pools
    if _p.numCoins > 2:
        return max_value(uint256), max_value(uint256)

    # get balances
    balances: uint256[8] = staticcall CurveMetaRegistry(_metaRegistry).get_balances(_p.pool)
    reserveA: uint256 = balances[_p.indexTokenA]
    reserveB: uint256 = balances[_p.indexTokenB]

    # insufficient liquidity
    if reserveA == 0 or reserveB == 0:
        return max_value(uint256), max_value(uint256)

    # calculate expected amounts out
    lpToken: address = staticcall CurveMetaRegistry(_metaRegistry).get_lp_token(_p.pool)
    totalSupply: uint256 = staticcall IERC20(lpToken).totalSupply()
    expectedAmountA: uint256 = _lpAmount * reserveA // totalSupply
    expectedAmountB: uint256 = _lpAmount * reserveB // totalSupply
    return expectedAmountA, expectedAmountB


@view
@internal
def _getCorrectRatioAmounts(
    _availAmountA: uint256,
    _availAmountB: uint256,
    _reserveA: uint256,
    _reserveB: uint256,
) -> (uint256, uint256):
    amountA: uint256 = _availAmountA
    amountB: uint256 = self._quote(_availAmountA, _reserveA, _reserveB)
    if amountB > _availAmountB:
        maybeAmountA: uint256 = self._quote(_availAmountB, _reserveB, _reserveA)
        if maybeAmountA <= _availAmountA:
            amountA = maybeAmountA
            amountB = _availAmountB
    return amountA, amountB


@view
@internal
def _quote(_amountA: uint256, _reserveA: uint256, _reserveB: uint256) -> uint256:
    return (_amountA * _reserveB) // _reserveA


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