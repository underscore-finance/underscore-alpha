# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

implements: LegoYield
initializes: yld
initializes: gov

exports: yld.__interface__
exports: gov.__interface__

import contracts.modules.YieldLegoData as yld
import contracts.modules.LocalGov as gov
from ethereum.ercs import IERC20
from interfaces import LegoYield

# `hasClaimableRewards()` is not a view function, sadly due to compound v3 constraints
# keeping here to uncomment to test all other functions
# implements: LegoCommon 
# from interfaces import LegoCommon

interface CompoundV3:
    def withdrawTo(_recipient: address, _asset: address, _amount: uint256): nonpayable
    def supplyTo(_recipient: address, _asset: address, _amount: uint256): nonpayable
    def totalSupply() -> uint256: view
    def totalBorrow() -> uint256: view
    def baseToken() -> address: view

interface CompoundV3Rewards:
    def getRewardOwed(_comet: address, _user: address) -> RewardOwed: nonpayable
    def claim(_comet: address, _user: address, _shouldAccrue: bool): nonpayable

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface CompoundV3Configurator:
    def factory(_cometAsset: address) -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct RewardOwed:
    token: address
    owed: uint256

event CompoundV3Deposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    usdValue: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event CompoundV3Withdrawal:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    usdValue: uint256
    vaultTokenAmountBurned: uint256
    recipient: address

event CompoundV3FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    amount: uint256

event CompoundV3RewardsAddrSet:
    addr: address

event CompoundV3LegoIdSet:
    legoId: uint256

event CompoundV3Activated:
    isActivated: bool

# compound v3
compoundRewards: public(address)
COMPOUND_V3_CONFIGURATOR: public(immutable(address))

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_configurator: address, _addyRegistry: address):
    assert empty(address) not in [_configurator, _addyRegistry] # dev: invalid addrs
    COMPOUND_V3_CONFIGURATOR = _configurator
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(empty(address), _addyRegistry, 0, 0)
    yld.__init__()


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [COMPOUND_V3_CONFIGURATOR]


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
    return self._isValidCometAddr(_vaultToken)


@view
@internal
def _isValidCometAddr(_cometAddr: address) -> bool:
    return staticcall CompoundV3Configurator(COMPOUND_V3_CONFIGURATOR).factory(_cometAddr) != empty(address)


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    return self._getUnderlyingAsset(_vaultToken)


@view
@internal
def _getUnderlyingAsset(_vaultToken: address) -> address:
    asset: address = yld.vaultToAsset[_vaultToken]
    if asset == empty(address) and self._isValidCometAddr(_vaultToken):
        asset = staticcall CompoundV3(_vaultToken).baseToken()
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
    # treated as 1:1
    return _vaultTokenAmount


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    if yld.vaultToAsset[_vaultToken] != _asset:
        return 0 # invalid vault token
    # treated as 1:1
    return _assetAmount


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
    return staticcall CompoundV3(_vaultToken).totalSupply()


@view
@external
def totalBorrows(_vaultToken: address) -> uint256:
    if not self._isVaultToken(_vaultToken):
        return 0 # invalid vault token
    return staticcall CompoundV3(_vaultToken).totalBorrow()


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
    preRecipientVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(_recipient)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    extcall CompoundV3(_vault).supplyTo(_recipient, _asset, depositAmount) # dev: could not deposit into compound v3

    # validate vault token transfer
    vaultTokenAmountReceived: uint256 = staticcall IERC20(_vault).balanceOf(_recipient) - preRecipientVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        depositAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_asset, depositAmount, _oracleRegistry)
    log CompoundV3Deposit(sender=msg.sender, asset=_asset, vaultToken=_vault, assetAmountDeposited=depositAmount, usdValue=usdValue, vaultTokenAmountReceived=vaultTokenAmountReceived, recipient=_recipient)
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
    preRecipientBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)

    # transfer vaults tokens to this contract
    vaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(msg.sender))
    assert vaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, vaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    extcall CompoundV3(_vaultToken).withdrawTo(_recipient, _asset, max_value(uint256)) # dev: could not withdraw from compound v3

    # validate received asset , transfer back to user
    assetAmountReceived: uint256 = staticcall IERC20(_asset).balanceOf(_recipient) - preRecipientBalance
    assert assetAmountReceived != 0 # dev: no asset amount received

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(_vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed
        vaultTokenAmount -= refundVaultTokenAmount

    usdValue: uint256 = self._getUsdValue(_asset, assetAmountReceived, _oracleRegistry)
    log CompoundV3Withdrawal(sender=msg.sender, asset=_asset, vaultToken=_vaultToken, assetAmountReceived=assetAmountReceived, usdValue=usdValue, vaultTokenAmountBurned=vaultTokenAmount, recipient=_recipient)
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
    compRewards: address = self.compoundRewards
    assert compRewards != empty(address) # dev: no comp rewards addr set
    if _market != empty(address):
        extcall CompoundV3Rewards(compRewards).claim(_market, _user, True)
    else:
        self._hasClaimableOrShouldClaim(_user, True, compRewards)


# sadly, this is not a view function because of `getRewardOwed()`
@external
def hasClaimableRewards(_user: address) -> bool:
    return self._hasClaimableOrShouldClaim(_user, False, self.compoundRewards)


@internal
def _hasClaimableOrShouldClaim(_user: address, _shouldClaim: bool, _compRewards: address) -> bool:
    hasClaimable: bool = False
    numAssets: uint256 = yld.numAssets
    for i: uint256 in range(1, numAssets, bound=max_value(uint256)):
        asset: address = yld.assets[i]
        comet: address = yld.assetOpportunities[asset][1] # only a single "vault token" (comet) per asset

        rewardOwed: RewardOwed = extcall CompoundV3Rewards(_compRewards).getRewardOwed(comet, _user)
        if rewardOwed.owed != 0:
            hasClaimable = True
            if _shouldClaim:
                extcall CompoundV3Rewards(_compRewards).claim(comet, _user, True)
            else:
                break

    return hasClaimable


# set rewards addr


@external
def setCompRewardsAddr(_addr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _addr != empty(address) # dev: invalid addr
    self.compoundRewards = _addr
    log CompoundV3RewardsAddrSet(addr=_addr)
    return True


##################
# Asset Registry #
##################


@external
def addAssetOpportunity(_asset: address, _vault: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # specific to lego
    assert self._getUnderlyingAsset(_vault) == _asset # dev: invalid asset or vault
    assert extcall IERC20(_asset).approve(_vault, max_value(uint256), default_return_value=True) # dev: max approval failed

    yld._addAssetOpportunity(_asset, _vault)
    return True


@external
def removeAssetOpportunity(_asset: address, _vault: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    yld._removeAssetOpportunity(_asset, _vault)
    assert extcall IERC20(_asset).approve(_vault, 0, default_return_value=True) # dev: approval failed
    return True


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log CompoundV3FundsRecovered(asset=_asset, recipient=_recipient, amount=balance)
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
    log CompoundV3LegoIdSet(legoId=_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._canGovern(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log CompoundV3Activated(isActivated=_shouldActivate)
