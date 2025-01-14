# @version 0.3.10

implements: LegoPartner

from vyper.interfaces import ERC20
import interfaces.LegoInterface as LegoPartner

interface AaveV3Interface:
    def supply(_asset: address, _amount: uint256, _onBehalfOf: address, _referralCode: uint16): nonpayable
    def withdraw(_asset: address, _amount: uint256, _to: address): nonpayable
    def getReserveData(_asset: address) -> AaveReserveDataV3: view

interface AgentFactory:
    def isAgenticWallet(_wallet: address) -> bool: view

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
    depositAmount: uint256
    vaultTokens: uint256
    refundAmount: uint256

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event AaveV3LegoIdSet:
    legoId: uint256

event AaveV3LegoGovernorSet:
    governor: indexed(address)

event AaveV3LegoActivated:
    isActivated: bool

# config
legoId: public(uint256)
governor: public(address)
isActivated: public(bool)

AAVE_V3: immutable(address)
LEGO_REGISTRY: immutable(address)
AGENT_FACTORY: immutable(address)


@external
def __init__(_aaveV3: address, _legoRegistry: address, _agentFactory: address, _governor: address):
    assert empty(address) not in [_aaveV3, _legoRegistry, _agentFactory, _governor] # dev: invalid addrs
    AAVE_V3 = _aaveV3
    LEGO_REGISTRY = _legoRegistry
    AGENT_FACTORY = _agentFactory
    self.governor = _governor
    self.isActivated = True


###########
# Deposit #
###########


@external
def depositTokens(_asset: address, _vault: address, _amount: uint256) -> (uint256, uint256):
    assert self.isActivated # dev: not activated
    assert AgentFactory(AGENT_FACTORY).isAgenticWallet(msg.sender) # dev: no perms

    # validate deposit asset
    aaveV3: address = AAVE_V3
    vaultToken: address = AaveV3Interface(aaveV3).getReserveData(_asset).aTokenAddress
    assert vaultToken != empty(address) # dev: invalid vault token

    # pre balances
    preLegoBalance: uint256 = ERC20(_asset).balanceOf(self)
    preUserVaultBalance: uint256 = ERC20(vaultToken).balanceOf(msg.sender)

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, ERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert ERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # deposit assets into lego partner
    depositAmount: uint256 = min(transferAmount, ERC20(_asset).balanceOf(self))
    assert ERC20(_asset).approve(aaveV3, depositAmount, default_return_value=True) # dev: approval failed
    AaveV3Interface(aaveV3).supply(_asset, depositAmount, msg.sender, 0)
    assert ERC20(_asset).approve(aaveV3, 0, default_return_value=True) # dev: approval failed

    # validate vault token transfer
    newUserVaultBalance: uint256 = ERC20(vaultToken).balanceOf(msg.sender)
    vaultTokenAmountReceived: uint256 = newUserVaultBalance - preUserVaultBalance
    assert vaultTokenAmountReceived != 0 # dev: no vault tokens received

    # refund if full deposit didn't get through
    currentLegoBalance: uint256 = ERC20(_asset).balanceOf(self)
    refundAmount: uint256 = 0
    if currentLegoBalance > preLegoBalance:
        refundAmount = currentLegoBalance - preLegoBalance
        assert ERC20(_asset).transfer(msg.sender, refundAmount, default_return_value=True) # dev: transfer failed

    trueDepositAmount: uint256 = depositAmount - refundAmount
    log AaveV3Deposit(msg.sender, _asset, trueDepositAmount, vaultTokenAmountReceived, refundAmount)
    return trueDepositAmount, vaultTokenAmountReceived


#################
# Recover Funds #
#################


@view
@external
def isValidFundsRecovery(_asset: address, _recipient: address) -> bool:
    return self._isValidFundsRecovery(_asset, _recipient, ERC20(_asset).balanceOf(self))


@view
@internal
def _isValidFundsRecovery(_asset: address, _recipient: address, _balance: uint256) -> bool:
    if empty(address) in [_recipient, _asset]:
        return False
    return _balance != 0


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert msg.sender == self.governor # dev: no perms

    balance: uint256 = ERC20(_asset).balanceOf(self)
    if not self._isValidFundsRecovery(_asset, _recipient, balance):
        return False

    assert ERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
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


################
# Set Governor #
################


@view
@external 
def isValidGovernor(_newGovernor: address) -> bool:
    return self._isValidGovernor(_newGovernor)


@view
@internal 
def _isValidGovernor(_newGovernor: address) -> bool:
    if not _newGovernor.is_contract or _newGovernor == empty(address):
        return False
    return _newGovernor != self.governor


@external
def setGovernor(_newGovernor: address) -> bool:
    assert self.isActivated # dev: not activated
    assert msg.sender == self.governor # dev: no perms
    if not self._isValidGovernor(_newGovernor):
        return False
    self.governor = _newGovernor
    log AaveV3LegoGovernorSet(_newGovernor)
    return True


############
# Activate #
############


@external
def activate(_shouldActivate: bool):
    assert msg.sender == self.governor # dev: no perms
    self.isActivated = _shouldActivate
    log AaveV3LegoActivated(_shouldActivate)