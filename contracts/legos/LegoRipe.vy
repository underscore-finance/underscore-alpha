# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

implements: LegoCredit
implements: LegoCommon
initializes: gov

exports: gov.__interface__

import contracts.modules.LocalGov as gov
from ethereum.ercs import IERC20
from interfaces import LegoCredit
from interfaces import LegoCommon

interface RipeTeller:
    def deposit(_asset: address, _amount: uint256 = max_value(uint256), _user: address = msg.sender, _vaultAddr: address = empty(address), _vaultId: uint256 = 0) -> uint256: nonpayable
    def withdraw(_asset: address, _amount: uint256 = max_value(uint256), _user: address = msg.sender, _vaultAddr: address = empty(address), _vaultId: uint256 = 0) -> uint256: nonpayable
    def repay(_paymentAmount: uint256 = max_value(uint256), _user: address = msg.sender, _isPaymentSavingsGreen: bool = False, _shouldRefundSavingsGreen: bool = True) -> bool: nonpayable
    def borrow(_greenAmount: uint256 = max_value(uint256), _user: address = msg.sender, _wantsSavingsGreen: bool = True) -> uint256: nonpayable
    def claimLoot(_user: address = msg.sender, _shouldStake: bool = True) -> uint256: nonpayable

interface RipeRegistry:
    def getAddr(_regId: uint256) -> address: view
    def savingsGreen() -> address: view
    def greenToken() -> address: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct TokenData:
    symbol: String[32]
    tokenAddress: address

event UnderscoreDeposit:
    sender: indexed(address)
    asset: indexed(address)
    assetAmountDeposited: uint256
    usdValue: uint256
    recipient: address

event UnderscoreWithdrawal:
    sender: indexed(address)
    asset: indexed(address)
    assetAmountReceived: uint256
    usdValue: uint256
    recipient: address

event UnderscoreFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    amount: uint256

event UnderscoreLegoIdSet:
    legoId: uint256

event UnderscoreActivated:
    isActivated: bool

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

RIPE_REGISTRY: public(immutable(address))
RIPE_LOOTBOX_ID: constant(uint256) = 16
RIPE_TELLER_ID: constant(uint256) = 17


@deploy
def __init__(_ripeRegistry: address, _addyRegistry: address):
    assert empty(address) not in [_ripeRegistry, _addyRegistry] # dev: invalid addrs
    RIPE_REGISTRY = _ripeRegistry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(empty(address), _addyRegistry, 0, 0)


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [RIPE_REGISTRY]


@view
@external
def getAccessForLego(_user: address) -> (address, String[64], uint256):
    return empty(address), empty(String[64]), 0


@view
@internal
def _getUsdValue(_asset: address, _amount: uint256, _oracleRegistry: address) -> uint256:
    oracleRegistry: address = _oracleRegistry
    if _oracleRegistry == empty(address):
        oracleRegistry = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(4)
    return staticcall OracleRegistry(oracleRegistry).getUsdValue(_asset, _amount)


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

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))

    # deposit into Ripe Protocol
    teller: address = staticcall RipeRegistry(RIPE_REGISTRY).getAddr(RIPE_TELLER_ID)
    assert extcall IERC20(_asset).approve(teller, depositAmount, default_return_value=True) # dev: approval failed
    depositAmount = extcall RipeTeller(teller).deposit(_asset, depositAmount, _recipient, _vault, 0)
    assert extcall IERC20(_asset).approve(teller, 0, default_return_value=True) # dev: approval failed

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    usdValue: uint256 = self._getUsdValue(_asset, depositAmount, _oracleRegistry)
    log UnderscoreDeposit(sender=msg.sender, asset=_asset, assetAmountDeposited=depositAmount, usdValue=usdValue, recipient=_recipient)
    return depositAmount, empty(address), 0, refundAssetAmount, usdValue


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

    # withdraw from Ripe Protocol
    teller: address = staticcall RipeRegistry(RIPE_REGISTRY).getAddr(RIPE_TELLER_ID)
    assetAmountReceived: uint256 = extcall RipeTeller(teller).withdraw(_asset, _amount, _recipient, _vaultToken, 0)
    assert assetAmountReceived != 0 # dev: no asset amount received

    usdValue: uint256 = self._getUsdValue(_asset, assetAmountReceived, _oracleRegistry)
    log UnderscoreWithdrawal(sender=msg.sender, asset=_asset, assetAmountReceived=assetAmountReceived, usdValue=usdValue, recipient=_recipient)
    return assetAmountReceived, 0, 0, usdValue


########
# Debt #
########


@external
def borrow(
    _borrowAsset: address,
    _amount: uint256,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (address, uint256, uint256):
    assert self.isActivated # dev: not activated

    ripeHq: address = RIPE_REGISTRY
    teller: address = staticcall RipeRegistry(ripeHq).getAddr(RIPE_TELLER_ID)
    borrowAmount: uint256 = extcall RipeTeller(teller).borrow(_amount, _recipient, True)
    assert borrowAmount != 0 # dev: no borrow amount received
    return staticcall RipeRegistry(ripeHq).greenToken(), borrowAmount, borrowAmount


@external
def repayDebt(
    _paymentAsset: address,
    _paymentAmount: uint256,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (address, uint256, uint256, uint256):
    assert self.isActivated # dev: not activated

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_paymentAsset).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_paymentAsset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed
    paymentAmount: uint256 = min(transferAmount, staticcall IERC20(_paymentAsset).balanceOf(self))

    # deposit into Ripe Protocol
    ripeHq: address = RIPE_REGISTRY
    teller: address = staticcall RipeRegistry(ripeHq).getAddr(RIPE_TELLER_ID)
    assert extcall IERC20(_paymentAsset).approve(teller, paymentAmount, default_return_value=True) # dev: approval failed
    extcall RipeTeller(teller).repay(paymentAmount, _recipient, _paymentAsset == staticcall RipeRegistry(ripeHq).savingsGreen(), True)
    assert extcall IERC20(_paymentAsset).approve(teller, 0, default_return_value=True) # dev: approval failed

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_paymentAsset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_paymentAsset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    # TODO: get remaining debt
    remainingDebt: uint256 = 0

    return _paymentAsset, paymentAmount, paymentAmount, remainingDebt


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
    assert self.isActivated # dev: not activated
    teller: address = staticcall RipeRegistry(RIPE_REGISTRY).getAddr(RIPE_TELLER_ID)
    extcall RipeTeller(teller).claimLoot(_user, True)


@view
@external
def hasClaimableRewards(_user: address) -> bool:
    # TODO: implement get view function from lootbox
    return False


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
    log UnderscoreFundsRecovered(asset=_asset, recipient=_recipient, amount=balance)
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
    log UnderscoreLegoIdSet(legoId=_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert gov._canGovern(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log UnderscoreActivated(isActivated=_shouldActivate)