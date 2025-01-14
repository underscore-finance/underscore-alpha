# @version 0.3.10

from vyper.interfaces import ERC20

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

# does not include all required erc20
balanceOf: public(HashMap[address, uint256]) # user -> shares
totalSupply: public(uint256)


@external
def __init__():
    pass


@view
@external
def getReserveData(_asset: address) -> AaveReserveDataV3:
    return AaveReserveDataV3({
        configuration: 0,
        liquidityIndex: 0,
        currentLiquidityRate: 0,
        variableBorrowIndex: 0,
        currentVariableBorrowRate: 0,
        currentStableBorrowRate: 0,
        lastUpdateTimestamp: 0,
        id: 0,
        aTokenAddress: self,
        stableDebtTokenAddress: empty(address),
        variableDebtTokenAddress: empty(address),
        interestRateStrategyAddress: empty(address),
        accruedToTreasury: 0,
        unbacked: 0,
        isolationModeTotalDebt: 0,
    })


@external
def supply(_asset: address, _amount: uint256, _onBehalfOf: address, _referralCode: uint16):
    assert ERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_onBehalfOf] += _amount
    self.totalSupply += _amount


@external
def withdraw(_asset: address, _amount: uint256, _to: address):
    vaultTokenAmount: uint256 = min(_amount, self.balanceOf[msg.sender])
    transferAmount: uint256 = min(vaultTokenAmount, ERC20(_asset).balanceOf(self))
    assert ERC20(_asset).transfer(_to, transferAmount, default_return_value=True) # dev: transfer failed
    self.balanceOf[msg.sender] -= transferAmount
    self.totalSupply -= transferAmount


@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    return True