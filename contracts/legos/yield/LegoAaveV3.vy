# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface AaveV3Interface:
    def supply(_asset: address, _amount: uint256, _onBehalfOf: address, _referralCode: uint16): nonpayable
    def withdraw(_asset: address, _amount: uint256, _to: address): nonpayable
    def getReserveData(_asset: address) -> AaveReserveDataV3: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governor() -> address: view

interface OracleRegistry:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

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
    usdValue: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event AaveV3Withdrawal:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    usdValue: uint256
    vaultTokenAmountBurned: uint256
    recipient: address

event SupportedAssetAdded:
    asset: indexed(address)
    vaultToken: indexed(address)

event SupportedAssetRemoved:
    asset: indexed(address)
    vaultToken: indexed(address)

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AaveV3LegoIdSet:
    legoId: uint256

event AaveV3Activated:
    isActivated: bool

# supported assets
assetOpportunities: public(HashMap[address, HashMap[uint256, address]]) # asset -> index -> vault token
indexOfAssetOpportunity: public(HashMap[address, HashMap[address, uint256]]) # asset -> vault token -> index
numAssetOpportunities: public(HashMap[address, uint256]) # asset -> number of opportunities

# config
legoId: public(uint256)
isActivated: public(bool)
AAVE_V3_POOL: public(immutable(address))
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_aaveV3: address, _addyRegistry: address):
    assert empty(address) not in [_aaveV3, _addyRegistry] # dev: invalid addrs
    AAVE_V3_POOL = _aaveV3
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [AAVE_V3_POOL]


@view
@internal
def _validateAssetAndVault(_asset: address, _vault: address) -> address:
    vault: address = _vault
    if _vault != empty(address):
        vault = self.assetOpportunities[_asset][1] # only one opportunity for aave v3
    assert self.indexOfAssetOpportunity[_asset][vault] != 0 # dev: asset + vault not supported
    return vault


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
    vaultToken: address = self._validateAssetAndVault(_asset, _vault)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preRecipientVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(_recipient)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    extcall AaveV3Interface(AAVE_V3_POOL).supply(_asset, depositAmount, _recipient, 0)

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
        depositAmount -= refundAssetAmount

    usdValue: uint256 = self._getUsdValue(_asset, depositAmount, _oracleRegistry)
    log AaveV3Deposit(msg.sender, _asset, vaultToken, depositAmount, usdValue, vaultTokenAmountReceived, _recipient)
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
    vaultToken: address = self._validateAssetAndVault(_asset, _vaultToken)

    # pre balances
    preLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    preRecipientAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    # transfer vaults tokens to this contract
    vaultTokenAmount: uint256 = min(_amount, staticcall IERC20(vaultToken).balanceOf(msg.sender))
    assert vaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(vaultToken).transferFrom(msg.sender, self, vaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    extcall AaveV3Interface(AAVE_V3_POOL).withdraw(_asset, max_value(uint256), _recipient)

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
        vaultTokenAmount -= refundVaultTokenAmount

    usdValue: uint256 = self._getUsdValue(_asset, assetAmountReceived, _oracleRegistry)
    log AaveV3Withdrawal(msg.sender, _asset, vaultToken, assetAmountReceived, usdValue, vaultTokenAmount, _recipient)
    return assetAmountReceived, vaultTokenAmount, refundVaultTokenAmount, usdValue


###################
# Not Implemented #
###################


@external
def swapTokens(_tokenIn: address, _tokenOut: address, _amountIn: uint256, _minAmountOut: uint256, _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, uint256, uint256, uint256):
    raise "Not Implemented"


####################
# Supported Assets #
####################


@external
def addSupportedAsset(_asset: address) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    aaveV3: address = AAVE_V3_POOL
    vaultToken: address = (staticcall AaveV3Interface(aaveV3).getReserveData(_asset)).aTokenAddress
    assert vaultToken != empty(address) # dev: asset not supported
    assert extcall IERC20(_asset).approve(aaveV3, max_value(uint256), default_return_value=True) # dev: max approval failed

    self._addAsset(_asset, vaultToken)
    log SupportedAssetAdded(_asset, vaultToken)
    return True


@external
def removeSupportedAsset(_asset: address) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms

    vaultToken: address = self.assetOpportunities[_asset][1] # only one opportunity for aave v3
    self._removeAsset(_asset, vaultToken)
    assert extcall IERC20(_asset).approve(AAVE_V3_POOL, 0, default_return_value=True) # dev: approval failed

    log SupportedAssetRemoved(_asset, vaultToken)
    return True


# internal


@internal
def _addAsset(_asset: address, _vault: address):
    assert self.indexOfAssetOpportunity[_asset][_vault] == 0 # dev: asset already supported

    aid: uint256 = self.numAssetOpportunities[_asset]
    if aid == 0:
        aid = 1 # not using 0 index
    self.assetOpportunities[_asset][aid] = _vault
    self.indexOfAssetOpportunity[_asset][_vault] = aid
    self.numAssetOpportunities[_asset] = aid + 1


@internal
def _removeAsset(_asset: address, _vault: address):
    targetIndex: uint256 = self.indexOfAssetOpportunity[_asset][_vault]
    assert targetIndex != 0 # dev: asset + vault token not found

    numOpportunities: uint256 = self.numAssetOpportunities[_asset]
    assert numOpportunities > 1 # dev: no opportunities to remove

    # update data
    lastIndex: uint256 = numOpportunities - 1
    self.numAssetOpportunities[_asset] = lastIndex
    self.indexOfAssetOpportunity[_asset][_vault] = 0

    # shift to replace the removed one
    if targetIndex != lastIndex:
        lastVaultToken: address = self.assetOpportunities[_asset][lastIndex]
        self.assetOpportunities[_asset][targetIndex] = lastVaultToken
        self.indexOfAssetOpportunity[_asset][lastVaultToken] = targetIndex


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
    prevLegoId: uint256 = self.legoId
    assert prevLegoId == 0 or prevLegoId == _legoId # dev: invalid lego id
    self.legoId = _legoId
    log AaveV3LegoIdSet(_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AaveV3Activated(_shouldActivate)