# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface CompoundV3:
    def withdrawTo(_recipient: address, _asset: address, _amount: uint256): nonpayable
    def supplyTo(_recipient: address, _asset: address, _amount: uint256): nonpayable
    def baseToken() -> address: view

interface AgentFactory:
    def isAgenticWallet(_wallet: address) -> bool: view

interface CompoundV3Configurator:
    def factory(_cometAsset: address) -> address: view

interface LegoRegistry:
    def governor() -> address: view

event CompoundV3Deposit:
    user: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256

event CompoundV3Withdrawal:
    user: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event CompoundV3LegoIdSet:
    legoId: uint256

event CompoundV3LegoActivated:
    isActivated: bool

# config
legoId: public(uint256)
isActivated: public(bool)

COMPOUND_V3_CONFIGURATOR: immutable(address)
LEGO_REGISTRY: immutable(address)
AGENT_FACTORY: immutable(address)


@deploy
def __init__(_configurator: address, _legoRegistry: address, _agentFactory: address):
    assert empty(address) not in [_configurator, _legoRegistry, _agentFactory] # dev: invalid addrs
    COMPOUND_V3_CONFIGURATOR = _configurator
    LEGO_REGISTRY = _legoRegistry
    AGENT_FACTORY = _agentFactory
    self.isActivated = True


@view
@internal
def _validateAssetAndVault(_asset: address, _vault: address):
    assert self.isActivated # dev: not activated
    assert staticcall AgentFactory(AGENT_FACTORY).isAgenticWallet(msg.sender) # dev: no perms

    assert staticcall CompoundV3Configurator(COMPOUND_V3_CONFIGURATOR).factory(_vault) != empty(address) # dev: invalid vault
    assert staticcall CompoundV3(_vault).baseToken() == _asset # dev: invalid asset


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _amount: uint256, _vault: address) -> (uint256, address, uint256):
    self._validateAssetAndVault(_asset, _vault)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preUserVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(msg.sender)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).approve(_vault, depositAmount, default_return_value=True) # dev: approval failed
    extcall CompoundV3(_vault).supplyTo(msg.sender, _asset, depositAmount) # dev: could not deposit into compound v3
    assert extcall IERC20(_asset).approve(_vault, 0, default_return_value=True) # dev: approval failed

    # validate vault token transfer
    newUserVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(msg.sender)
    vaultTokenAmountReceived: uint256 = newUserVaultBalance - preUserVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAmount, default_return_value=True) # dev: transfer failed

    actualDepositAmount: uint256 = depositAmount - refundAmount
    log CompoundV3Deposit(msg.sender, _asset, _vault, actualDepositAmount, vaultTokenAmountReceived)
    return actualDepositAmount, _vault, vaultTokenAmountReceived


############
# Withdraw #
############


@external
def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address) -> (uint256, uint256):
    self._validateAssetAndVault(_asset, _vaultToken)

    # pre balances
    preUserBalance: uint256 = staticcall IERC20(_asset).balanceOf(msg.sender)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    extcall CompoundV3(_vaultToken).withdrawTo(msg.sender, _asset, max_value(uint256)) # dev: could not withdraw from compound v3

    # validate received asset , transfer back to user
    newUserBalance: uint256 = staticcall IERC20(_asset).balanceOf(msg.sender)
    assetAmountReceived: uint256 = newUserBalance - preUserBalance
    assert assetAmountReceived != 0 # dev: no asset amount received

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(_vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed

    vaultTokenAmountBurned: uint256 = transferVaultTokenAmount - refundVaultTokenAmount
    log CompoundV3Withdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, vaultTokenAmountBurned)
    return assetAmountReceived, vaultTokenAmountBurned


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


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log CompoundV3LegoActivated(_shouldActivate)