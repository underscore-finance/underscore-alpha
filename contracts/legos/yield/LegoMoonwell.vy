# @version 0.4.0

implements: LegoYield
implements: LegoCommon
initializes: yld
initializes: gov

exports: yld.__interface__
exports: gov.__interface__

import contracts.modules.YieldLegoData as yld
import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoYield
from interfaces import LegoCommon

interface CompoundV2:
    def redeem(_ctokenAmount: uint256) -> uint256: nonpayable
    def mint(_amount: uint256) -> uint256: nonpayable
    def exchangeRateStored() -> uint256: view
    def totalBorrows() -> uint256: view
    def totalSupply() -> uint256: view
    def underlying() -> address: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface MoonwellComptroller:
    def getAllMarkets() -> DynArray[address, MAX_MARKETS]: view
    def claimReward(_holder: address): nonpayable
    def rewardDistributor() -> address: view

interface MoonwellRewardDistributor:
    def getOutstandingRewardsForUser(_user: address) -> DynArray[RewardWithMToken, MAX_MARKETS]: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

interface WethContract:
    def deposit(): payable

struct RewardWithMToken:
    mToken: address
    rewards: DynArray[RewardInfo, MAX_ASSETS]

struct RewardInfo:
    emissionToken: address
    totalAmount: uint256
    supplySide: uint256
    borrowSide: uint256

event MoonwellDeposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    usdValue: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event MoonwellWithdrawal:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    usdValue: uint256
    vaultTokenAmountBurned: uint256
    recipient: address

event MoonwellFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event MoonwellLegoIdSet:
    legoId: uint256

event MoonwellActivated:
    isActivated: bool

# moonwell
MOONWELL_COMPTROLLER: public(immutable(address))

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))
WETH: public(immutable(address))

MAX_MARKETS: constant(uint256) = 50
MAX_ASSETS: constant(uint256) = 25


@deploy
def __init__(_moonwellComptroller: address, _addyRegistry: address, _wethAddr: address):
    assert empty(address) not in [_moonwellComptroller, _addyRegistry, _wethAddr] # dev: invalid addrs
    MOONWELL_COMPTROLLER = _moonwellComptroller
    ADDY_REGISTRY = _addyRegistry
    WETH = _wethAddr
    self.isActivated = True
    gov.__init__(_addyRegistry)
    yld.__init__()


@payable
@external
def __default__():
    pass


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [MOONWELL_COMPTROLLER]


@view
@external
def getAccessForLego(_user: address) -> (address, String[64], uint256):
    return empty(address), empty(String[64]), 0


#############
# Utilities #
#############


# underlying asset


@view
@external
def isVaultToken(_vaultToken: address) -> bool:
    return self._isVaultToken(_vaultToken)


@view
@internal
def _isVaultToken(_vaultToken: address) -> bool:
    if yld.vaultToAsset[_vaultToken] != empty(address):
        return True
    return self._isValidCToken(_vaultToken)


@view
@internal
def _isValidCToken(_cToken: address) -> bool:
    compMarkets: DynArray[address, MAX_MARKETS] = staticcall MoonwellComptroller(MOONWELL_COMPTROLLER).getAllMarkets()
    return _cToken in compMarkets


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    return self._getUnderlyingAsset(_vaultToken)


@view
@internal
def _getUnderlyingAsset(_vaultToken: address) -> address:
    asset: address = yld.vaultToAsset[_vaultToken]
    if asset == empty(address) and self._isValidCToken(_vaultToken):
        asset = staticcall CompoundV2(_vaultToken).underlying()
    return asset


# underlying amount


@view
@external
def getUnderlyingAmount(_vaultToken: address, _vaultTokenAmount: uint256) -> uint256:
    if not self._isVaultToken(_vaultToken) or _vaultTokenAmount == 0:
        return 0 # invalid vault token or amount
    return self._getUnderlyingAmount(_vaultToken, _vaultTokenAmount)


@view
@internal
def _getUnderlyingAmount(_vaultToken: address, _vaultTokenAmount: uint256) -> uint256:
    return _vaultTokenAmount * staticcall CompoundV2(_vaultToken).exchangeRateStored() // (10 ** 18)


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    if yld.vaultToAsset[_vaultToken] != _asset:
        return 0 # invalid vault token
    return _assetAmount * (10 ** 18) // staticcall CompoundV2(_vaultToken).exchangeRateStored()


# usd value


@view
@external
def getUsdValueOfVaultToken(_vaultToken: address, _vaultTokenAmount: uint256, _oracleRegistry: address = empty(address)) -> uint256:
    return self._getUsdValueOfVaultToken(_vaultToken, _vaultTokenAmount, _oracleRegistry)


@view
@internal
def _getUsdValueOfVaultToken(_vaultToken: address, _vaultTokenAmount: uint256, _oracleRegistry: address) -> uint256:
    asset: address = empty(address)
    underlyingAmount: uint256 = 0
    usdValue: uint256 = 0
    asset, underlyingAmount, usdValue = self._getUnderlyingData(_vaultToken, _vaultTokenAmount, _oracleRegistry)
    return usdValue


# all underlying data together


@view
@external
def getUnderlyingData(_vaultToken: address, _vaultTokenAmount: uint256, _oracleRegistry: address = empty(address)) -> (address, uint256, uint256):
    return self._getUnderlyingData(_vaultToken, _vaultTokenAmount, _oracleRegistry)


@view
@internal
def _getUnderlyingData(_vaultToken: address, _vaultTokenAmount: uint256, _oracleRegistry: address) -> (address, uint256, uint256):
    if _vaultTokenAmount == 0 or _vaultToken == empty(address):
        return empty(address), 0, 0 # bad inputs
    asset: address = self._getUnderlyingAsset(_vaultToken)
    if asset == empty(address):
        return empty(address), 0, 0 # invalid vault token
    underlyingAmount: uint256 = self._getUnderlyingAmount(_vaultToken, _vaultTokenAmount)
    usdValue: uint256 = self._getUsdValue(asset, underlyingAmount, _oracleRegistry)
    return asset, underlyingAmount, usdValue


@view
@internal
def _getUsdValue(_asset: address, _amount: uint256, _oracleRegistry: address) -> uint256:
    oracleRegistry: address = _oracleRegistry
    if _oracleRegistry == empty(address):
        oracleRegistry = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)
    return staticcall OracleRegistry(oracleRegistry).getUsdValue(_asset, _amount)


# other


@view
@external
def totalAssets(_vaultToken: address) -> uint256:
    if not self._isVaultToken(_vaultToken):
        return 0 # invalid vault token
    return staticcall CompoundV2(_vaultToken).totalSupply() * staticcall CompoundV2(_vaultToken).exchangeRateStored() // (10 ** 18)


@view
@external
def totalBorrows(_vaultToken: address) -> uint256:
    if not self._isVaultToken(_vaultToken):
        return 0 # invalid vault token
    return staticcall CompoundV2(_vaultToken).totalBorrows()


###########
# Deposit #
###########


@external
def depositTokens(
    _asset: address,
    _amount: uint256,
    _vault: address,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, address, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated
    assert yld.indexOfAssetOpportunity[_asset][_vault] != 0 # dev: asset + vault not supported

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall CompoundV2(_vault).mint(depositAmount) == 0 # dev: could not deposit into moonwell

    # validate received vault tokens, transfer back to user
    vaultTokenAmountReceived: uint256 = staticcall IERC20(_vault).balanceOf(self) - preLegoVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received
    assert extcall IERC20(_vault).transfer(_recipient, vaultTokenAmountReceived, default_return_value=True) # dev: transfer failed

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        depositAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_asset, depositAmount, _oracleRegistry)
    log MoonwellDeposit(msg.sender, _asset, _vault, depositAmount, usdValue, vaultTokenAmountReceived, _recipient)
    return depositAmount, _vault, vaultTokenAmountReceived, refundAssetAmount, usdValue


############
# Withdraw #
############


@external
def withdrawTokens(
    _asset: address,
    _amount: uint256,
    _vaultToken: address,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated
    assert yld.indexOfAssetOpportunity[_asset][_vaultToken] != 0 # dev: asset + vault not supported

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)

    # transfer vaults tokens to this contract
    vaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(msg.sender))
    assert vaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, vaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    assert extcall CompoundV2(_vaultToken).redeem(max_value(uint256)) == 0 # dev: could not withdraw from moonwell

    # when withdrawing weth, they give eth
    if _asset == WETH:
        extcall WethContract(WETH).deposit(value=self.balance)

    # validate received asset , transfer back to user
    assetAmountReceived: uint256 = staticcall IERC20(_asset).balanceOf(self) - preLegoBalance
    assert assetAmountReceived != 0 # dev: no asset amount received
    assert extcall IERC20(_asset).transfer(_recipient, assetAmountReceived, default_return_value=True) # dev: transfer failed

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(_vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed
        vaultTokenAmount -= refundVaultTokenAmount

    usdValue: uint256 = self._getUsdValue(_asset, assetAmountReceived, _oracleRegistry)
    log MoonwellWithdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, usdValue, vaultTokenAmount, _recipient)
    return assetAmountReceived, vaultTokenAmount, refundVaultTokenAmount, usdValue


#################
# Claim Rewards #
#################


@external
def claimRewards(
    _user: address,
    _markets: DynArray[address, MAX_ASSETS] = [],
    _rewardTokens: DynArray[address, MAX_ASSETS] = [],
    _rewardAmounts: DynArray[uint256, MAX_ASSETS] = [],
    _proofs: DynArray[bytes32, MAX_ASSETS] = [],
):
    extcall MoonwellComptroller(MOONWELL_COMPTROLLER).claimReward(_user)


@view
@external
def hasClaimableRewards(_user: address) -> bool:
    rewardDistributor: address = staticcall MoonwellComptroller(MOONWELL_COMPTROLLER).rewardDistributor()
    rewardsWithMToken: DynArray[RewardWithMToken, MAX_MARKETS] = staticcall MoonwellRewardDistributor(rewardDistributor).getOutstandingRewardsForUser(_user)
    for i: uint256 in range(len(rewardsWithMToken), bound=MAX_MARKETS):
        rewardsInfo: DynArray[RewardInfo, MAX_ASSETS] = rewardsWithMToken[i].rewards
        for j: uint256 in range(len(rewardsInfo), bound=MAX_ASSETS):
            if rewardsInfo[j].totalAmount > 0:
                return True
    return False


##################
# Asset Registry #
##################


@external
def addAssetOpportunity(_asset: address, _vault: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    # specific to lego
    assert self._getUnderlyingAsset(_vault) == _asset # dev: invalid vault and/or asset
    assert extcall IERC20(_asset).approve(_vault, max_value(uint256), default_return_value=True) # dev: max approval failed

    yld._addAssetOpportunity(_asset, _vault)
    return True


@external
def removeAssetOpportunity(_asset: address, _vault: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    yld._removeAssetOpportunity(_asset, _vault)
    assert extcall IERC20(_asset).approve(_vault, 0, default_return_value=True) # dev: approval failed
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
    log MoonwellFundsRecovered(_asset, _recipient, balance)
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
    log MoonwellLegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log MoonwellActivated(_shouldActivate)
