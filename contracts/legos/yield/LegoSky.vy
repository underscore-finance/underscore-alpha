# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

implements: LegoYield
implements: LegoCommon
initializes: gov
exports: gov.__interface__

import contracts.modules.Governable as gov
from ethereum.ercs import IERC20
from interfaces import LegoYield
from interfaces import LegoCommon

interface SkyPsm:
    def swapExactIn(_assetIn: address, _assetOut: address, _amountIn: uint256, _minAmountOut: uint256, _receiver: address, _referralCode: uint256) -> uint256: nonpayable
    def convertToAssets(_asset: address, _numShares: uint256) -> uint256: view
    def convertToShares(_asset: address, _amount: uint256) -> uint256: view
    def totalAssets() -> uint256: view
    def susds() -> address: view
    def usdc() -> address: view
    def usds() -> address: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

event SkyDeposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    usdValue: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event SkyWithdrawal:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    usdValue: uint256
    vaultTokenAmountBurned: uint256
    recipient: address

event AssetOpportunityAdded:
    asset: indexed(address)
    vaultToken: indexed(address)

event AssetOpportunityRemoved:
    asset: indexed(address)
    vaultToken: indexed(address)

event SkyFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    amount: uint256

event SkyLegoIdSet:
    legoId: uint256

event SkyActivated:
    isActivated: bool

# sky assets
usdc: public(address)
usds: public(address)
susds: public(address)
SKY_PSM: public(immutable(address))

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MIN_SLIPPAGE: constant(uint256) = 2_00 # 2%
MAX_VAULTS: constant(uint256) = 15
MAX_ASSETS: constant(uint256) = 25


@deploy
def __init__(_skyPsm: address, _addyRegistry: address):
    assert empty(address) not in [_skyPsm, _addyRegistry] # dev: invalid addrs
    SKY_PSM = _skyPsm
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(_addyRegistry)

    # sky assets
    usdc: address = staticcall SkyPsm(_skyPsm).usdc()
    if usdc != empty(address):
        assert extcall IERC20(usdc).approve(_skyPsm, max_value(uint256), default_return_value=True) # dev: max approval failed
        self.usdc = usdc
    usds: address = staticcall SkyPsm(_skyPsm).usds()
    if usds != empty(address):
        assert extcall IERC20(usds).approve(_skyPsm, max_value(uint256), default_return_value=True) # dev: max approval failed
        self.usds = usds
    susds: address = staticcall SkyPsm(_skyPsm).susds()
    if susds != empty(address):
        assert extcall IERC20(susds).approve(_skyPsm, max_value(uint256), default_return_value=True) # dev: max approval failed
        self.susds = susds


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [SKY_PSM]


@view
@external
def getAccessForLego(_user: address) -> (address, String[64], uint256):
    return empty(address), empty(String[64]), 0


#############
# Utilities #
#############


# assets and vault tokens


@view
@external
def getAssetOpportunities(_asset: address) -> DynArray[address, MAX_VAULTS]:
    if _asset not in [self.usdc, self.usds]:
        return []
    return [self.susds]


@view
@external
def getAssets() -> DynArray[address, MAX_ASSETS]:
    return [self.usdc, self.usds]


# underlying asset


@view
@external
def isVaultToken(_vaultToken: address) -> bool:
    return self._isVaultToken(_vaultToken)


@view
@internal
def _isVaultToken(_vaultToken: address) -> bool:
    return _vaultToken == self.susds


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    return self._getUnderlyingAsset(_vaultToken)


@view
@internal
def _getUnderlyingAsset(_vaultToken: address) -> address:
    if not self._isVaultToken(_vaultToken):
        return empty(address)
    return self.usds # treating usds as default underlying asset


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
    # treating usds as default underlying asset
    return staticcall SkyPsm(SKY_PSM).convertToAssets(self.usds, _vaultTokenAmount)


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    if _asset not in [self.usdc, self.usds]:
        return 0 # invalid asset
    if _vaultToken != self.susds:
        return 0 # invalid vault token
    return staticcall SkyPsm(SKY_PSM).convertToShares(_asset, _assetAmount)


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
    return staticcall SkyPsm(SKY_PSM).totalAssets()


@view
@external
def totalBorrows(_vaultToken: address) -> uint256:
    return 0


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

    assert _asset in [self.usdc, self.usds] # dev: invalid asset
    vaultToken: address = self.susds
    if _vault != empty(address):
        assert vaultToken == _vault # dev: invalid vault

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preRecipientVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(_recipient)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # calc min amount out
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    expectedShares: uint256 = staticcall SkyPsm(SKY_PSM).convertToShares(_asset, depositAmount)
    minAmountOut: uint256 = expectedShares * (HUNDRED_PERCENT - MIN_SLIPPAGE) // HUNDRED_PERCENT

    # deposit assets into lego partner
    vaultTokenAmountReceived: uint256 = extcall SkyPsm(SKY_PSM).swapExactIn(_asset, vaultToken, depositAmount, minAmountOut, _recipient, 0)
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        depositAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_asset, depositAmount, _oracleRegistry)
    log SkyDeposit(sender=msg.sender, asset=_asset, vaultToken=vaultToken, assetAmountDeposited=depositAmount, usdValue=usdValue, vaultTokenAmountReceived=vaultTokenAmountReceived, recipient=_recipient)
    return depositAmount, vaultToken, vaultTokenAmountReceived, refundAssetAmount, usdValue


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

    assert _asset in [self.usdc, self.usds] # dev: invalid asset
    vaultToken: address = self.susds
    if _vaultToken != empty(address):
        assert vaultToken == _vaultToken # dev: invalid vault

    # pre balances
    preLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    preRecipientAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # calc min amount out
    vaultTokenAmount: uint256 = min(transferVaultTokenAmount, staticcall IERC20(vaultToken).balanceOf(self))
    expectedAssetAmount: uint256 = staticcall SkyPsm(SKY_PSM).convertToAssets(_asset, vaultTokenAmount)
    minAmountOut: uint256 = expectedAssetAmount * (HUNDRED_PERCENT - MIN_SLIPPAGE) // HUNDRED_PERCENT

    # withdraw assets from lego partner
    assetAmountReceived: uint256 = extcall SkyPsm(SKY_PSM).swapExactIn(vaultToken, _asset, vaultTokenAmount, minAmountOut, _recipient, 0)
    assert assetAmountReceived != 0 # dev: no asset amount received

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed
        vaultTokenAmount -= refundVaultTokenAmount

    usdValue: uint256 = self._getUsdValue(_asset, assetAmountReceived, _oracleRegistry)
    log SkyWithdrawal(sender=msg.sender, asset=_asset, vaultToken=vaultToken, assetAmountReceived=assetAmountReceived, usdValue=usdValue, vaultTokenAmountBurned=vaultTokenAmount, recipient=_recipient)
    return assetAmountReceived, vaultTokenAmount, refundVaultTokenAmount, usdValue


#################
# Claim Rewards #
#################


@external
def claimRewards(
    _user: address,
    _market: address,
    _rewardToken: address,
    _rewardAmount: uint256,
    _proof: bytes32,
):
    pass


@view
@external
def hasClaimableRewards(_user: address) -> bool:
    return False


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
    log SkyFundsRecovered(asset=_asset, recipient=_recipient, amount=balance)
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
    log SkyLegoIdSet(legoId=_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._isGovernor(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log SkyActivated(isActivated=_shouldActivate)
