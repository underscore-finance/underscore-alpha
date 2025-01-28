# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface CompoundV2:
    def redeem(_ctokenAmount: uint256) -> uint256: nonpayable
    def mint(_amount: uint256) -> uint256: nonpayable
    def underlying() -> address: view

interface CompoundV2Comptroller:
    def getAllMarkets() -> DynArray[address, MAX_MARKETS]: view

interface LegoRegistry:
    def governor() -> address: view

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

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event MoonwellLegoIdSet:
    legoId: uint256

legoId: public(uint256)

MOONWELL_COMPTROLLER: public(immutable(address))
LEGO_REGISTRY: public(immutable(address))

MAX_MARKETS: constant(uint256) = 50


@deploy
def __init__(_moonwellComptroller: address, _legoRegistry: address):
    assert empty(address) not in [_moonwellComptroller, _legoRegistry] # dev: invalid addrs
    MOONWELL_COMPTROLLER = _moonwellComptroller
    LEGO_REGISTRY = _legoRegistry


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return [MOONWELL_COMPTROLLER]


@view
@internal
def _validateAssetAndVault(_asset: address, _vault: address):
    compMarkets: DynArray[address, MAX_MARKETS] = staticcall CompoundV2Comptroller(MOONWELL_COMPTROLLER).getAllMarkets()
    assert _vault in compMarkets # dev: invalid vault
    assert staticcall CompoundV2(_vault).underlying() == _asset # dev: invalid asset


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _amount: uint256, _vault: address, _recipient: address) -> (uint256, address, uint256, uint256, uint256):
    self._validateAssetAndVault(_asset, _vault)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(self)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).approve(_vault, depositAmount, default_return_value=True) # dev: approval failed
    assert extcall CompoundV2(_vault).mint(depositAmount) == 0 # dev: could not deposit into moonwell
    assert extcall IERC20(_asset).approve(_vault, 0, default_return_value=True) # dev: approval failed

    # validate received vault tokens, transfer back to user
    newLegoVaultBalance: uint256 = staticcall IERC20(_vault).balanceOf(self)
    vaultTokenAmountReceived: uint256 = newLegoVaultBalance - preLegoVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received
    assert extcall IERC20(_vault).transfer(_recipient, vaultTokenAmountReceived, default_return_value=True) # dev: transfer failed

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAssetAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAssetAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAssetAmount, default_return_value=True) # dev: transfer failed

    actualDepositAmount: uint256 = depositAmount - refundAssetAmount
    usdValue: uint256 = 0 # TODO: add usd value (_asset, actualDepositAmount)

    log MoonwellDeposit(msg.sender, _asset, _vault, actualDepositAmount, usdValue, vaultTokenAmountReceived, _recipient)
    return actualDepositAmount, _vault, vaultTokenAmountReceived, refundAssetAmount, usdValue


############
# Withdraw #
############


@external
def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address, _recipient: address) -> (uint256, uint256, uint256, uint256):
    self._validateAssetAndVault(_asset, _vaultToken)

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)

    # transfer vaults tokens to this contract
    transferVaultTokenAmount: uint256 = min(_amount, staticcall IERC20(_vaultToken).balanceOf(msg.sender))
    assert transferVaultTokenAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, transferVaultTokenAmount, default_return_value=True) # dev: transfer failed

    # withdraw assets from lego partner
    assert extcall CompoundV2(_vaultToken).redeem(max_value(uint256)) == 0 # dev: could not withdraw from moonwell

    # validate received asset , transfer back to user
    newLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assetAmountReceived: uint256 = newLegoBalance - preLegoBalance
    assert assetAmountReceived != 0 # dev: no asset amount received
    assert extcall IERC20(_asset).transfer(_recipient, assetAmountReceived, default_return_value=True) # dev: transfer failed

    usdValue: uint256 = 0 # TODO: add usd value (_asset, assetAmountReceived)

    # refund if full withdrawal didn't happen
    currentLegoVaultBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    refundVaultTokenAmount: uint256 = 0
    if currentLegoVaultBalance > preLegoVaultBalance:
        refundVaultTokenAmount = currentLegoVaultBalance - preLegoVaultBalance
        assert extcall IERC20(_vaultToken).transfer(msg.sender, refundVaultTokenAmount, default_return_value=True) # dev: transfer failed

    vaultTokenAmountBurned: uint256 = transferVaultTokenAmount - refundVaultTokenAmount
    log MoonwellWithdrawal(msg.sender, _asset, _vaultToken, assetAmountReceived, usdValue, vaultTokenAmountBurned, _recipient)
    return assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount, usdValue


###################
# Not Implemented #
###################


@external
def swapTokens(_tokenIn: address, _tokenOut: address, _amountIn: uint256, _minAmountOut: uint256, _recipient: address) -> (uint256, uint256, uint256, uint256):
    raise "Not Implemented"


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
    log MoonwellLegoIdSet(_legoId)
    return True
