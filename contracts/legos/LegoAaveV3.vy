# @version 0.4.0

implements: LegoPartner

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface AaveV3Interface:
    def supply(_asset: address, _amount: uint256, _onBehalfOf: address, _referralCode: uint16): nonpayable
    def withdraw(_asset: address, _amount: uint256, _to: address): nonpayable
    def getReserveData(_asset: address) -> AaveReserveDataV3: view

interface AgentFactory:
    def isAgenticWallet(_wallet: address) -> bool: view

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
    user: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    refundAmount: uint256

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AaveV3LegoIdSet:
    legoId: uint256

event AaveV3LegoActivated:
    isActivated: bool

# config
legoId: public(uint256)
isActivated: public(bool)

AAVE_V3_POOL: immutable(address)
LEGO_REGISTRY: immutable(address)
AGENT_FACTORY: immutable(address)


@deploy
def __init__(_aaveV3: address, _legoRegistry: address, _agentFactory: address):
    assert empty(address) not in [_aaveV3, _legoRegistry, _agentFactory] # dev: invalid addrs
    AAVE_V3_POOL = _aaveV3
    LEGO_REGISTRY = _legoRegistry
    AGENT_FACTORY = _agentFactory
    self.isActivated = True


@view
@external
def aaveV3Pool() -> address:
    return AAVE_V3_POOL


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _vault: address, _amount: uint256) -> (uint256, address, uint256):
    assert self.isActivated # dev: not activated
    assert staticcall AgentFactory(AGENT_FACTORY).isAgenticWallet(msg.sender) # dev: no perms

    # validate deposit asset
    aaveV3: address = AAVE_V3_POOL
    vaultToken: address = (staticcall AaveV3Interface(aaveV3).getReserveData(_asset)).aTokenAddress
    assert vaultToken != empty(address) # dev: invalid vault token

    # pre balances
    preLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    preUserVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(msg.sender)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, staticcall IERC20(_asset).balanceOf(self))
    assert extcall IERC20(_asset).approve(aaveV3, depositAmount, default_return_value=True) # dev: approval failed
    extcall AaveV3Interface(aaveV3).supply(_asset, depositAmount, msg.sender, 0)
    assert extcall IERC20(_asset).approve(aaveV3, 0, default_return_value=True) # dev: approval failed

    # validate vault token transfer
    newUserVaultBalance: uint256 = staticcall IERC20(vaultToken).balanceOf(msg.sender)
    vaultTokenAmountReceived: uint256 = newUserVaultBalance - preUserVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    refundAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAmount = currentLegoBalance - preLegoBalance
        assert extcall IERC20(_asset).transfer(msg.sender, refundAmount, default_return_value=True) # dev: transfer failed

    trueDepositAmount: uint256 = depositAmount - refundAmount
    log AaveV3Deposit(msg.sender, _asset, vaultToken, trueDepositAmount, vaultTokenAmountReceived, refundAmount)
    return trueDepositAmount, vaultToken, vaultTokenAmountReceived


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


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == staticcall LegoRegistry(LEGO_REGISTRY).governor() # dev: no perms
    self.isActivated = _shouldActivate
    log AaveV3LegoActivated(_shouldActivate)