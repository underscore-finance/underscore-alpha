# SPDX-License-Identifier: BUSL-1.1
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/BUSL_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry

from ethereum.ercs import IERC20
from interfaces import LegoYield
from interfaces import LegoCommon

flag LegoType:
    YIELD_OPP
    DEX
    BORROW

struct VaultTokenInfo:
    legoId: uint256
    vaultToken: address

event LegoHelperSet:
    helperAddr: indexed(address)

# lego types
pendingLegoType: public(HashMap[address, LegoType]) # addr -> pending lego type
legoIdToType: public(HashMap[uint256, LegoType]) # legoId -> lego type

legoHelper: public(address)

MAX_VAULTS: constant(uint256) = 15
MAX_VAULTS_FOR_USER: constant(uint256) = 30


@deploy
def __init__(
    _addyRegistry: address,
    _minLegoChangeDelay: uint256,
    _maxLegoChangeDelay: uint256,
):
    assert _addyRegistry != empty(address) # dev: invalid addy registry

    # initialize gov
    gov.__init__(empty(address), _addyRegistry, 0, 0)

    # initialize registry
    registry.__init__(_minLegoChangeDelay, _maxLegoChangeDelay, "LegoRegistry.vy")


@view
@external
def isYieldLego(_legoId: uint256) -> bool:
    return self.legoIdToType[_legoId] == LegoType.YIELD_OPP


#################
# Register Lego #
#################


@view
@external
def isValidNewLegoAddr(_addr: address) -> bool:
    return registry._isValidNewAddy(_addr)


@external
def registerNewLego(_addr: address, _description: String[64], _legoType: LegoType) -> bool:
    """
    @notice Initiates the registration process for a new Lego
    @dev Only callable by governor. Sets up a pending registration that requires confirmation after a delay period
    @param _addr The address of the Lego to register
    @param _description A short description of the Lego (max 64 characters)
    @param _legoType The type of Lego (YIELD_OPP or DEX)
    @return True if the registration was successfully initiated, False if the Lego is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    isPending: bool = registry._registerNewAddy(_addr, _description)
    if isPending:
        self.pendingLegoType[_addr] = _legoType
    return isPending


@external
def confirmNewLegoRegistration(_addr: address) -> uint256:
    """
    @notice Confirms a pending Lego registration after the required delay period
    @dev Only callable by governor. Finalizes the registration by assigning an ID and setting the Lego type
    @param _addr The address of the Lego to confirm registration for
    @return The assigned ID for the registered Lego, or 0 if confirmation fails
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    legoId: uint256 = registry._confirmNewAddy(_addr)
    if legoId == 0:
        self.pendingLegoType[_addr] = empty(LegoType)
        return 0

    # set lego id
    assert extcall LegoCommon(_addr).setLegoId(legoId) # dev: set id failed

    # set lego type
    legoType: LegoType = self.pendingLegoType[_addr]
    self.legoIdToType[legoId] = legoType
    self.pendingLegoType[_addr] = empty(LegoType)

    return legoId


@external
def cancelPendingNewLego(_addr: address) -> bool:
    """
    @notice Cancels a pending Lego registration
    @dev Only callable by governor. Removes the pending registration and emits a cancellation event
    @param _addr The address of the Lego whose pending registration should be cancelled
    @return True if the cancellation was successful, reverts if no pending registration exists
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    self.pendingLegoType[_addr] = empty(LegoType)
    return registry._cancelPendingNewAddy(_addr)


###############
# Update Lego #
###############


@view
@external
def isValidLegoUpdate(_legoId: uint256, _newAddr: address) -> bool:
    return registry._isValidAddyUpdate(_legoId, _newAddr, registry.addyInfo[_legoId].addr)


@external
def updateLegoAddr(_legoId: uint256, _newAddr: address) -> bool:
    """
    @notice Initiates an address update for an existing registered Lego
    @dev Only callable by governor. Sets up a pending update that requires confirmation after a delay period
    @param _legoId The ID of the Lego to update
    @param _newAddr The new address to set for the Lego
    @return True if the update was successfully initiated, False if the update is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._updateAddyAddr(_legoId, _newAddr)


@external
def confirmLegoUpdate(_legoId: uint256) -> bool:
    """
    @notice Confirms a pending Lego address update after the required delay period
    @dev Only callable by governor. Finalizes the update by updating the address and setting the Lego ID
    @param _legoId The ID of the Lego to confirm update for
    @return True if the update was successfully confirmed, False if confirmation fails
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    didUpdate: bool = registry._confirmAddyUpdate(_legoId)
    if didUpdate:
        legoAddr: address = registry.addyInfo[_legoId].addr
        assert extcall LegoCommon(legoAddr).setLegoId(_legoId) # dev: set id failed
    return didUpdate


@external
def cancelPendingLegoUpdate(_legoId: uint256) -> bool:
    """
    @notice Cancels a pending Lego address update
    @dev Only callable by governor. Removes the pending update and emits a cancellation event
    @param _legoId The ID of the Lego whose pending update should be cancelled
    @return True if the cancellation was successful, reverts if no pending update exists
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyUpdate(_legoId)


################
# Disable Lego #
################


@view
@external
def isValidLegoDisable(_legoId: uint256) -> bool:
    return registry._isValidAddyDisable(_legoId, registry.addyInfo[_legoId].addr)


@external
def disableLegoAddr(_legoId: uint256) -> bool:
    """
    @notice Initiates the disable process for an existing registered Lego
    @dev Only callable by governor. Sets up a pending disable that requires confirmation after a delay period
    @param _legoId The ID of the Lego to disable
    @return True if the disable was successfully initiated, False if the disable is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._disableAddyAddr(_legoId)


@external
def confirmLegoDisable(_legoId: uint256) -> bool:
    """
    @notice Confirms a pending Lego disable after the required delay period
    @dev Only callable by governor. Finalizes the disable by clearing the Lego address
    @param _legoId The ID of the Lego to confirm disable for
    @return True if the disable was successfully confirmed, False if confirmation fails
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._confirmAddyDisable(_legoId)


@external
def cancelPendingLegoDisable(_legoId: uint256) -> bool:
    """
    @notice Cancels a pending Lego disable
    @dev Only callable by governor. Removes the pending disable and emits a cancellation event
    @param _legoId The ID of the Lego whose pending disable should be cancelled
    @return True if the cancellation was successful, reverts if no pending disable exists
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyDisable(_legoId)


#####################
# Lego Change Delay #
#####################


@external
def setLegoChangeDelay(_numBlocks: uint256) -> bool:
    """
    @notice Sets the delay period required for Lego changes
    @dev Only callable by governor. The delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY
    @param _numBlocks The number of blocks to set as the delay period
    @return True if the delay was successfully set, reverts if delay is invalid
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@view
@external
def legoChangeDelay() -> uint256:
    return registry.addyChangeDelay


@external
def setLegoChangeDelayToMin() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(registry.MIN_ADDY_CHANGE_DELAY)


#################
# Views / Utils #
#################


@view
@external
def numLegosRaw() -> uint256:
    return registry.numAddys


# is valid


@view
@external
def isValidLegoAddr(_addr: address) -> bool:
    return registry._isValidAddyAddr(_addr)


@view
@external
def isValidLegoId(_legoId: uint256) -> bool:
    return registry._isValidAddyId(_legoId)


# lego getters


@view
@external
def getLegoId(_addr: address) -> uint256:
    return registry._getAddyId(_addr)


@view
@external
def getLegoAddr(_legoId: uint256) -> address:
    return registry._getAddy(_legoId)


@view
@external
def getLegoInfo(_legoId: uint256) -> registry.AddyInfo:
    return registry.addyInfo[_legoId]


@view
@external
def getLegoDescription(_legoId: uint256) -> String[64]:
    return registry.addyInfo[_legoId].description


# high level


@view
@external
def getNumLegos() -> uint256:
    return registry._getNumAddys()


@view
@external
def getLastLegoAddr() -> address:
    return registry._getLastAddyAddr()


@view
@external
def getLastLegoId() -> uint256:
    return registry._getLastAddyId()


# underlying asset


@view
@external
def getUnderlyingAsset(_vaultToken: address) -> address:
    """
    @notice Get the underlying asset for a vault token
    @dev Returns empty address if vault token is not registered
    @param _vaultToken The address of the vault token to query
    @return The underlying asset address
    """
    if _vaultToken == empty(address):
        return empty(address)

    numLegos: uint256 = registry.numAddys
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = self.legoIdToType[i]
        if legoType != LegoType.YIELD_OPP:
            continue

        legoAddr: address = registry.addyInfo[i].addr
        asset: address = staticcall LegoYield(legoAddr).getUnderlyingAsset(_vaultToken)
        if asset != empty(address):
            return asset

    return empty(address)


@view
@external
def getUnderlyingForUser(_user: address, _asset: address) -> uint256:
    """
    @notice Get the total underlying amount for a user in a given asset
    @dev Returns 0 if user or asset is empty
    @param _user The address of the user to query
    @param _asset The address of the asset to query
    """
    if empty(address) in [_user, _asset]:
        return 0

    totalDeposited: uint256 = 0
    numLegos: uint256 = registry.numAddys
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = self.legoIdToType[i]
        if legoType != LegoType.YIELD_OPP:
            continue

        legoAddr: address = registry.addyInfo[i].addr
        legoVaultTokens: DynArray[address, MAX_VAULTS] = staticcall LegoYield(legoAddr).getAssetOpportunities(_asset)
        if len(legoVaultTokens) == 0:
            continue

        for vaultToken: address in legoVaultTokens:
            if vaultToken == empty(address):
                continue
            vaultTokenBal: uint256 = staticcall IERC20(vaultToken).balanceOf(_user)
            if vaultTokenBal != 0:
                totalDeposited += staticcall LegoYield(legoAddr).getUnderlyingAmount(vaultToken, vaultTokenBal)

    return totalDeposited


@view
@external
def getVaultTokensForUser(_user: address, _asset: address) -> DynArray[VaultTokenInfo, MAX_VAULTS_FOR_USER]:
    """
    @notice Get all vault tokens for a user in a given asset
    @dev Returns empty array if user or asset is empty
    @param _user The address of the user to query
    @param _asset The address of the asset to query
    @return Array of VaultTokenInfo structs containing legoId and vaultToken address
    """
    if empty(address) in [_user, _asset]:
        return []

    vaultTokens: DynArray[VaultTokenInfo, MAX_VAULTS_FOR_USER] = []

    numLegos: uint256 = registry.numAddys
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = self.legoIdToType[i]
        if legoType != LegoType.YIELD_OPP:
            continue

        legoAddr: address = registry.addyInfo[i].addr
        legoVaultTokens: DynArray[address, MAX_VAULTS] = staticcall LegoYield(legoAddr).getAssetOpportunities(_asset)
        if len(legoVaultTokens) == 0:
            continue

        for vaultToken: address in legoVaultTokens:
            if vaultToken == empty(address):
                continue
            if staticcall IERC20(vaultToken).balanceOf(_user) != 0:
                vaultTokens.append(VaultTokenInfo(
                    legoId=i,
                    vaultToken=vaultToken
                ))

    return vaultTokens


@view
@external
def getLegoFromVaultToken(_vaultToken: address) -> (uint256, address):
    """
    @notice Get the lego ID and address for a given vault token
    @dev Returns (0, empty(address)) if vault token is not valid
    @param _vaultToken The address of the vault token to query
    @return The lego ID and address
    """
    numLegos: uint256 = registry.numAddys
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = self.legoIdToType[i]
        if legoType != LegoType.YIELD_OPP:
            continue

        legoAddr: address = registry.addyInfo[i].addr
        if staticcall LegoYield(legoAddr).isVaultToken(_vaultToken):
            return i, legoAddr

    return 0, empty(address)


@view
@external
def isVaultToken(_vaultToken: address) -> bool:
    """
    @notice Check if a given address is a registered vault token
    @dev Returns False if not a vault token
    @param _vaultToken The address of the vault token to query
    @return True if the address is a vault token, False otherwise
    """
    numLegos: uint256 = registry.numAddys
    for i: uint256 in range(1, numLegos, bound=max_value(uint256)):
        legoType: LegoType = self.legoIdToType[i]
        if legoType != LegoType.YIELD_OPP:
            continue

        legoAddr: address = registry.addyInfo[i].addr
        if staticcall LegoYield(legoAddr).isVaultToken(_vaultToken):
            return True

    return False


###############
# Lego Helper #
###############


@view
@external 
def isValidLegoHelper(_helperAddr: address) -> bool:
    """
    @notice Check if an address can be set as the Lego helper
    @dev Address must be a contract and different from current helper
    @param _helperAddr The address to validate
    @return True if address can be set as helper, False otherwise
    """
    return self._isValidLegoHelper(_helperAddr)


@view
@internal 
def _isValidLegoHelper(_helperAddr: address) -> bool:
    if not _helperAddr.is_contract or _helperAddr == empty(address):
        return False
    return _helperAddr != self.legoHelper


@external
def setLegoHelper(_helperAddr: address) -> bool:
    """
    @notice Set a new Lego helper address
    @dev Only callable by governor
    @param _helperAddr The address to set as helper
    @return True if helper was set successfully, False otherwise
    """
    assert gov._canGovern(msg.sender) # dev: no perms

    if not self._isValidLegoHelper(_helperAddr):
        return False
    self.legoHelper = _helperAddr
    log LegoHelperSet(helperAddr=_helperAddr)
    return True

