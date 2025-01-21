# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface SkyPsm:
    def swapExactIn(_assetIn: address, _assetOut: address, _amountIn: uint256, _minAmountOut: uint256, _receiver: address, _referralCode: uint256) -> uint256: nonpayable
    def susds() -> address: view
    def usdc() -> address: view
    def usds() -> address: view

interface LegoRegistry:
    def governor() -> address: view

event SkyDeposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event SkyWithdrawal:
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

event SkyLegoIdSet:
    legoId: uint256

legoId: public(uint256)

SKY_PSM: public(immutable(address))
LEGO_REGISTRY: public(immutable(address))


@deploy
def __init__(_skyPsm: address, _legoRegistry: address):
    assert empty(address) not in [_skyPsm, _legoRegistry] # dev: invalid addrs
    SKY_PSM = _skyPsm
    LEGO_REGISTRY = _legoRegistry


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [SKY_PSM]


@view
@internal
def _validateAssetAndVault(_asset: address, _vault: address, _skyPsm: address) -> address:
    assert _asset in [staticcall SkyPsm(_skyPsm).usdc(), staticcall SkyPsm(_skyPsm).usds()] # dev: asset not supported
    vaultToken: address = staticcall SkyPsm(_skyPsm).susds()
    assert vaultToken != empty(address) # dev: asset not supported
    if _vault != empty(address):
        assert vaultToken == _vault # dev: error with vault input
    return vaultToken


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _amount: uint256, _vault: address, _recipient: address) -> (uint256, address, uint256, uint256):
    skyPsm: address = SKY_PSM
    vaultToken: address = self._validateAssetAndVault(_asset, _vault, skyPsm)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preRecipientVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(_recipient)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).approve(skyPsm, depositAmount, default_return_value=True) # dev: approval failed
    vaultTokenAmountReceived: uint256 = extcall SkyPsm(skyPsm).swapExactIn(_asset, vaultToken, depositAmount, 0, _recipient, 0)
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received
    assert extcall IERC20(_asset).approve(skyPsm, 0, default_return_value=True) # dev: approval failed

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    actualDepositAmount: uint256 = depositAmount - refundAssetAmount
    log SkyDeposit(msg.sender, _asset, vaultToken, actualDepositAmount, vaultTokenAmountReceived, _recipient)
    return actualDepositAmount, vaultToken, vaultTokenAmountReceived, refundAssetAmount


############
# Withdraw #
############


@external
def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address, _recipient: address) -> (uint256, uint256, uint256):
    skyPsm: address = SKY_PSM
    vaultToken: address = self._validateAssetAndVault(_asset, _vaultToken, skyPsm)

    # pre balances
    preLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    preRecipientAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    withdrawAmount: uint256 = min(transferVaultTokenAmount, staticcall IERC20(vaultToken).balanceOf(self))
    assert extcall IERC20(vaultToken).approve(skyPsm, withdrawAmount, default_return_value=True) # dev: approval failed
    assetAmountReceived: uint256 = extcall SkyPsm(skyPsm).swapExactIn(vaultToken, _asset, withdrawAmount, 0, _recipient, 0)
    assert assetAmountReceived != 0 # dev: no asset amount received
    assert extcall IERC20(vaultToken).approve(skyPsm, 0, default_return_value=True) # dev: approval failed

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed

    vaultTokenAmountBurned: uint256 = transferVaultTokenAmount - refundVaultTokenAmount
    log SkyWithdrawal(msg.sender, _asset, vaultToken, assetAmountReceived, vaultTokenAmountBurned, _recipient)
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
    log SkyLegoIdSet(_legoId)
    return True