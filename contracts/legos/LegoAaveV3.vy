# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface AaveV3Interface:
    def supply(_asset: address, _amount: uint256, _onBehalfOf: address, _referralCode: uint16): nonpayable
    def withdraw(_asset: address, _amount: uint256, _to: address): nonpayable
    def getReserveData(_asset: address) -> AaveReserveDataV3: view

interface LegoRegistry:
    def governor() -> address: view

struct AaveReserveDataV3:
    configuration: uint256
    liquidityIndex: uint128
    currentLiquidityRate: uint128
    variableBorrowIndex: uint128
    currentVariableBorrowRate: uint128
    currentStableBorrowRate: uint128
    lastUpdateTimestamp: uint40
    id: uint16
    aTokenAddress: address
    stableDebtTokenAddress: address
    variableDebtTokenAddress: address
    interestRateStrategyAddress: address
    accruedToTreasury: uint128
    unbacked: uint128
    isolationModeTotalDebt: uint128

event AaveV3Deposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event AaveV3Withdrawal:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    recipient: address

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AaveV3LegoIdSet:
    legoId: uint256

legoId: public(uint256)

AAVE_V3_POOL: public(immutable(address))
LEGO_REGISTRY: public(immutable(address))


@deploy
def __init__(_aaveV3: address, _legoRegistry: address):
    assert empty(address) not in [_aaveV3, _legoRegistry] # dev: invalid addrs
    AAVE_V3_POOL = _aaveV3
    LEGO_REGISTRY = _legoRegistry


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [AAVE_V3_POOL]


@view
@internal
def _validateAssetAndVault(_asset: address, _vault: address, _registry: address) -> address:
    vaultToken: address = (staticcall AaveV3Interface(_registry).getReserveData(_asset)).aTokenAddress
    assert vaultToken != empty(address) # dev: asset not supported
    if _vault != empty(address):
        assert vaultToken == _vault # dev: error with vault input
    return vaultToken


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _amount: uint256, _vault: address, _recipient: address) -> (uint256, address, uint256, uint256):
    aaveV3: address = AAVE_V3_POOL
    vaultToken: address = self._validateAssetAndVault(_asset, _vault, aaveV3)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preRecipientVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(_recipient)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).approve(aaveV3, depositAmount, default_return_value=True) # dev: approval failed
    extcall AaveV3Interface(aaveV3).supply(_asset, depositAmount, _recipient, 0)
    assert extcall IERC20(_asset).approve(aaveV3, 0, default_return_value=True) # dev: approval failed

    # validate vault token transfer
    newRecipientVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(_recipient)
    vaultTokenAmountReceived: uint256 = newRecipientVaultBalance - preRecipientVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    actualDepositAmount: uint256 = depositAmount - refundAssetAmount
    log AaveV3Deposit(msg.sender, _asset, vaultToken, actualDepositAmount, vaultTokenAmountReceived, _recipient)
    return actualDepositAmount, vaultToken, vaultTokenAmountReceived, refundAssetAmount


############
# Withdraw #
############


@external
def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address, _recipient: address) -> (uint256, uint256, uint256):
    aaveV3: address = AAVE_V3_POOL
    vaultToken: address = self._validateAssetAndVault(_asset, _vaultToken, aaveV3)

    # pre balances
    preLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    preRecipientAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    extcall AaveV3Interface(aaveV3).withdraw(_asset, max_value(uint256), _recipient)

    # validate asset transfer
    newRecipientAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    assetAmountReceived: uint256 = newRecipientAssetBalance - preRecipientAssetBalance
    assert assetAmountReceived != 0 # dev: no asset amount received

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed

    vaultTokenAmountBurned: uint256 = transferVaultTokenAmount - refundVaultTokenAmount
    log AaveV3Withdrawal(msg.sender, _asset, vaultToken, assetAmountReceived, vaultTokenAmountBurned, _recipient)
    return assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount


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
    log AaveV3LegoIdSet(_legoId)
    return True