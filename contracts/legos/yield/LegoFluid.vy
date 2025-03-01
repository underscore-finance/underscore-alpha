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

interface Erc4626Interface:
    def redeem(_vaultTokenAmount: uint256, _recipient: address, _owner: address) -> uint256: nonpayable
    def deposit(_assetAmount: uint256, _recipient: address) -> uint256: nonpayable
    def convertToAssets(_vaultTokenAmount: uint256) -> uint256: view
    def convertToShares(_assetAmount: uint256) -> uint256: view
    def totalAssets() -> uint256: view
    def asset() -> address: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface FluidLendingResolver:
    def getAllFTokens() -> DynArray[address, MAX_FTOKENS]: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

event FluidDeposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    usdValue: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event FluidWithdrawal:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    usdValue: uint256
    vaultTokenAmountBurned: uint256
    recipient: address

event FluidFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event FluidLegoIdSet:
    legoId: uint256

event FluidActivated:
    isActivated: bool

# fluid
FLUID_RESOLVER: public(immutable(address))

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

MAX_FTOKENS: constant(uint256) = 50


@deploy
def __init__(_fluidResolver: address, _addyRegistry: address):
    assert empty(address) not in [_fluidResolver, _addyRegistry] # dev: invalid addrs
    FLUID_RESOLVER = _fluidResolver
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(_addyRegistry)
    yld.__init__()


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [FLUID_RESOLVER]


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
    return self._isValidFToken(_vaultToken)


@view
@internal
def _isValidFToken(_fToken: address) -> bool:
    fTokens: DynArray[address, MAX_FTOKENS] = staticcall FluidLendingResolver(FLUID_RESOLVER).getAllFTokens()
    return _fToken in fTokens


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    return self._getUnderlyingAsset(_vaultToken)


@view
@internal
def _getUnderlyingAsset(_vaultToken: address) -> address:
    asset: address = yld.vaultToAsset[_vaultToken]
    if asset == empty(address) and self._isValidFToken(_vaultToken):
        asset = staticcall Erc4626Interface(_vaultToken).asset()
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
    return staticcall Erc4626Interface(_vaultToken).convertToAssets(_vaultTokenAmount)


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    if yld.vaultToAsset[_vaultToken] != _asset:
        return 0 # invalid vault token
    return staticcall Erc4626Interface(_vaultToken).convertToShares(_assetAmount)


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
    return staticcall Erc4626Interface(_vaultToken).totalAssets()


@view
@external
def totalBorrows(_vaultToken: address) -> uint256:
    return 0 # TODO


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

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    vaultTokenAmountReceived: uint256 = extcall Erc4626Interface(_vault).deposit(depositAmount, _recipient)
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed
        depositAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_asset, depositAmount, _oracleRegistry)
    log FluidDeposit(msg.sender, _asset, _vault, depositAmount, usdValue, vaultTokenAmountReceived, _recipient)
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
    preLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    vaultTokenAmount: uint256 = min(transferVaultTokenAmount, staticcall IERC20(_vaultToken).balanceOf(self))
    assetAmountReceived: uint256 = extcall Erc4626Interface(_vaultToken).redeem(vaultTokenAmount, _recipient, self)
    assert assetAmountReceived != 0 # dev: no asset amount received

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(_vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed
        vaultTokenAmount -= refundVaultTokenAmount

    usdValue: uint256 = self._getUsdValue(_asset, assetAmountReceived, _oracleRegistry)
    log FluidWithdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, usdValue, vaultTokenAmount, _recipient)
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


##################
# Asset Registry #
##################


@external
def addAssetOpportunity(_asset: address, _vault: address) -> bool:
    assert gov._isGovernor(msg.sender) # dev: no perms

    # specific to lego
    assert self._getUnderlyingAsset(_vault) == _asset # dev: invalid asset or vault
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
    log FluidFundsRecovered(_asset, _recipient, balance)
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
    log FluidLegoIdSet(_legoId)
    return True