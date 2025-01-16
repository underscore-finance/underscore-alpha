# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface CompoundV3:
    def withdrawTo(_recipient: address, _asset: address, _amount: uint256): nonpayable
    def supplyTo(_recipient: address, _asset: address, _amount: uint256): nonpayable
    def baseToken() -> address: view

interface CompoundV3Configurator:
    def factory(_cometAsset: address) -> address: view

interface LegoRegistry:
    def governor() -> address: view

event CompoundV3Deposit:
    sender: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    recipient: address

event CompoundV3Withdrawal:
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

event CompoundV3LegoIdSet:
    legoId: uint256

legoId: public(uint256)

COMPOUND_V3_CONFIGURATOR: public(immutable(address))
LEGO_REGISTRY: public(immutable(address))


@deploy
def __init__(_configurator: address, _legoRegistry: address):
    assert empty(address) not in [_configurator, _legoRegistry] # dev: invalid addrs
    COMPOUND_V3_CONFIGURATOR = _configurator
    LEGO_REGISTRY = _legoRegistry


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [COMPOUND_V3_CONFIGURATOR]


@view
@internal
def _validateAssetAndVault(_asset: address, _vault: address):
    assert staticcall CompoundV3Configurator(COMPOUND_V3_CONFIGURATOR).factory(_vault) != empty(address) # dev: invalid vault
    assert staticcall CompoundV3(_vault).baseToken() == _asset # dev: invalid asset


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _amount: uint256, _vault: address, _recipient: address) -> (uint256, address, uint256, uint256):
    self._validateAssetAndVault(_asset, _vault)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preRecipientVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(_recipient)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).approve(_vault, depositAmount, default_return_value=True) # dev: approval failed
    extcall CompoundV3(_vault).supplyTo(_recipient, _asset, depositAmount) # dev: could not deposit into compound v3
    assert extcall IERC20(_asset).approve(_vault, 0, default_return_value=True) # dev: approval failed

    # validate vault token transfer
    newRecipientVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(_recipient)
    vaultTokenAmountReceived: uint256 = newRecipientVaultBalance - preRecipientVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    actualDepositAmount: uint256 = depositAmount - refundAssetAmount
    log CompoundV3Deposit(msg.sender, _asset, _vault, actualDepositAmount, vaultTokenAmountReceived, _recipient)
    return actualDepositAmount, _vault, vaultTokenAmountReceived, refundAssetAmount


############
# Withdraw #
############


@external
def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address, _recipient: address) -> (uint256, uint256, uint256):
    self._validateAssetAndVault(_asset, _vaultToken)

    # pre balances
    preRecipientBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    extcall CompoundV3(_vaultToken).withdrawTo(_recipient, _asset, max_value(uint256)) # dev: could not withdraw from compound v3

    # validate received asset , transfer back to user
    newRecipientBalance: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    assetAmountReceived: uint256 = newRecipientBalance - preRecipientBalance
    assert assetAmountReceived != 0 # dev: no asset amount received

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(_vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed

    vaultTokenAmountBurned: uint256 = transferVaultTokenAmount - refundVaultTokenAmount
    log CompoundV3Withdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, vaultTokenAmountBurned, _recipient)
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
    log CompoundV3LegoIdSet(_legoId)
    return True
