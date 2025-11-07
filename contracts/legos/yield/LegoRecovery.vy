# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

implements: LegoYield
implements: LegoCommon
initializes: gov

exports: gov.__interface__

import contracts.modules.LocalGov as gov
from ethereum.ercs import IERC20
from interfaces import LegoYield
from interfaces import LegoCommon

interface AgentFactory:
    def isUserWallet(_wallet: address) -> bool: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct Recovery:
    user: address
    asset: address
    recipient: address

event Deposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256

event FundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    amount: uint256

event BackupFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    amount: uint256

event LegoIdSet:
    legoId: uint256

# user assets
userAssets: public(HashMap[address, HashMap[address, uint256]]) # user -> asset -> amount

GOVERNANCE: public(immutable(address))
AGENT_FACTORY_ID: constant(uint256) = 1
MAX_RECOVERIES: constant(uint256) = 30

# config
legoId: public(uint256)
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_governance: address, _addyRegistry: address):
    assert empty(address) not in [_governance, _addyRegistry] # dev: invalid addrs
    GOVERNANCE = _governance
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True
    gov.__init__(empty(address), _addyRegistry, 0, 0)


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

    # verify user is wallet
    agentFactory: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(AGENT_FACTORY_ID)
    assert staticcall AgentFactory(agentFactory).isUserWallet(msg.sender) # dev: not a user wallet

    # transfer deposit asset to this contract
    transferAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert transferAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, transferAmount, default_return_value=True) # dev: transfer failed

    # save user asset
    self.userAssets[msg.sender][_asset] += transferAmount

    log Deposit(user=msg.sender, asset=_asset, amount=transferAmount)
    return transferAmount, empty(address), 0, 0, 0


@external
def migrateFunds(_recoveries: DynArray[Recovery, MAX_RECOVERIES]) -> bool:
    assert msg.sender == GOVERNANCE or gov._canGovern(msg.sender) # dev: no perms
    for r: Recovery in _recoveries:
        amount: uint256 = min(self.userAssets[r.user][r.asset], staticcall IERC20(r.asset).balanceOf(self))
        if amount == 0:
            continue
        if r.recipient == empty(address):
            continue
        assert extcall IERC20(r.asset).transfer(r.recipient, amount, default_return_value=True) # dev: transfer failed
        self.userAssets[r.user][r.asset] -= amount
        log FundsRecovered(asset=r.asset, recipient=r.recipient, amount=amount)
    return True


##################
# Backup Recover #
##################


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log BackupFundsRecovered(asset=_asset, recipient=_recipient, amount=balance)
    return True


#########
# Other #
#########


@view
@external
def getRegistries() -> DynArray[address, 10]:
    return []


@view
@external
def getAccessForLego(_user: address) -> (address, String[64], uint256):
    return empty(address), empty(String[64]), 0


# underlying asset


@view
@external
def isVaultToken(_vaultToken: address) -> bool:
    return True


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    return empty(address)


# underlying amount


@view
@external
def getUnderlyingAmount(_vaultToken: address, _vaultTokenAmount: uint256) -> uint256:
    return 0


@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    return 0


# usd value


@view
@external
def getUsdValueOfVaultToken(_vaultToken: address, _vaultTokenAmount: uint256, _oracleRegistry: address = empty(address)) -> uint256:
    return 0


# all underlying data together


@view
@external
def getUnderlyingData(_vaultToken: address, _vaultTokenAmount: uint256, _oracleRegistry: address = empty(address)) -> (address, uint256, uint256):
    return empty(address), 0, 0


# other


@view
@external
def totalAssets(_vaultToken: address) -> uint256:
    return 0


@view
@external
def totalBorrows(_vaultToken: address) -> uint256:
    return 0


@external
def withdrawTokens(
    _asset: address,
    _amount: uint256,
    _vaultToken: address,
    _recipient: address,
    _oracleRegistry: address = empty(address),
) -> (uint256, uint256, uint256, uint256):
    return 0, 0, 0, 0


@external
def claimRewards(
    _user: address,
    _market: address,
    _rewardToken: address,
    _rewardAmount: uint256,
    _proof: bytes32,
):
    pass


@external
def addAssetOpportunity(_asset: address, _vault: address) -> bool:
    return True


@external
def removeAssetOpportunity(_asset: address, _vault: address) -> bool:
    return True


@external
def setLegoId(_legoId: uint256) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(2) # dev: no perms
    prevLegoId: uint256 = self.legoId
    assert prevLegoId == 0 or prevLegoId == _legoId # dev: invalid lego id
    self.legoId = _legoId
    log LegoIdSet(legoId=_legoId)
    return True


@external
def activate(_shouldActivate: bool):
    pass
