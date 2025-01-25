# @version 0.4.0

from ethereum.ercs import IERC20
import interfaces.LegoInterface as LegoPartner

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view
    def isValidLegoId(_legoId: uint256) -> bool: view

interface WethContract:
    def withdraw(_amount: uint256): nonpayable
    def deposit(): payable

flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP

struct AgentInfo:
    isActive: bool
    allowedAssets: DynArray[address, MAX_ASSETS]
    allowedLegoIds: DynArray[uint256, MAX_LEGOS]

struct Signature:
    signature: Bytes[65]
    signer: address
    expiration: uint256

struct ActionInstruction:
    action: ActionType
    legoId: uint256
    asset: address
    vault: address
    amount: uint256
    recipient: address
    altLegoId: uint256
    altVault: address
    altAsset: address
    altAmount: uint256

event AgenticDeposit:
    signer: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    refundAssetAmount: uint256
    legoId: uint256
    legoAddr: address
    broadcaster: address
    isSignerAgent: bool

event AgenticWithdrawal:
    signer: indexed(address)
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    refundVaultTokenAmount: uint256
    legoId: uint256
    legoAddr: address
    broadcaster: address
    isSignerAgent: bool

event AgenticSwap:
    signer: indexed(address)
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    swapAmount: uint256
    toAmount: uint256
    refundAssetAmount: uint256
    legoId: uint256
    legoAddr: address
    broadcaster: address
    isSignerAgent: bool

event WalletFundsTransferred:
    signer: indexed(address)
    recipient: indexed(address)
    asset: indexed(address)
    amount: uint256
    broadcaster: address
    isSignerAgent: bool

event EthConvertedToWeth:
    signer: indexed(address)
    amount: uint256
    paidEth: uint256
    weth: indexed(address)
    broadcaster: indexed(address)
    isSignerAgent: bool

event WethConvertedToEth:
    signer: indexed(address)
    amount: uint256
    weth: indexed(address)
    broadcaster: indexed(address)
    isSignerAgent: bool

event WhitelistAddrSet:
    addr: indexed(address)
    isAllowed: bool

event AgentAdded:
    agent: indexed(address)
    allowedAssets: uint256
    allowedLegoIds: uint256

event AgentModified:
    agent: indexed(address)
    allowedAssets: uint256
    allowedLegoIds: uint256

event AgentDisabled:
    agent: indexed(address)
    prevAllowedAssets: uint256
    prevAllowedLegoIds: uint256

event LegoIdAddedToAgent:
    agent: indexed(address)
    legoId: indexed(uint256)

event AssetAddedToAgent:
    agent: indexed(address)
    asset: indexed(address)

# settings
owner: public(address)
agentSettings: public(HashMap[address, AgentInfo])
isRecipientAllowed: public(HashMap[address, bool])

# config
legoRegistry: public(address)
wethAddr: public(address)
initialized: public(bool)

API_VERSION: constant(String[28]) = "0.0.1"
MAX_ASSETS: constant(uint256) = 25
MAX_LEGOS: constant(uint256) = 10
MAX_INSTRUCTIONS: constant(uint256) = 20

# eip-712
usedSignatures: public(HashMap[Bytes[65], bool])

DEPOSIT_TYPE_HASH: constant(bytes32) = keccak256('Deposit(uint256 legoId,address asset,uint256 amount,address vault,uint256 expiration)')
WITHDRAWAL_TYPE_HASH: constant(bytes32) = keccak256('Withdrawal(uint256 legoId,address asset,uint256 amount,address vaultToken,uint256 expiration)')
REBALANCE_TYPE_HASH: constant(bytes32) = keccak256('Rebalance(uint256 fromLegoId,uint256 toLegoId,address asset,uint256 amount,address fromVaultToken,address toVault,uint256 expiration)')
SWAP_TYPE_HASH: constant(bytes32) = keccak256('Swap(uint256 legoId,address tokenIn,address tokenOut,uint256 amountIn,uint256 minAmountOut,uint256 expiration)')
TRANSFER_TYPE_HASH: constant(bytes32) = keccak256('Transfer(address recipient,uint256 amount,address asset,uint256 expiration)')
ETH_TO_WETH_TYPE_HASH: constant(bytes32) = keccak256('EthToWeth(uint256 amount,uint256 depositLegoId,address depositVault,uint256 expiration)')
WETH_TO_ETH_TYPE_HASH: constant(bytes32) = keccak256('WethToEth(uint256 amount,address recipient,uint256 withdrawLegoId,address withdrawVaultToken,uint256 expiration)')

DOMAIN_TYPE_HASH: constant(bytes32) = keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)')
ECRECOVER_PRECOMPILE: constant(address) = 0x0000000000000000000000000000000000000001


@deploy
def __init__():
    # make sure original reference contract can't be initialized
    self.initialized = True


@payable
@external
def __default__():
    pass


@external
def initialize(_legoRegistry: address, _wethAddr: address, _owner: address, _initialAgent: address) -> bool:
    """
    @notice Sets up the initial state of the wallet template
    @dev Can only be called once and sets core contract parameters
    @param _legoRegistry The address of the lego registry contract
    @param _wethAddr The address of the WETH contract
    @param _owner The address that will own this wallet
    @param _initialAgent The address of the initial AI agent (if any)
    @return bool True if initialization was successful
    """
    assert not self.initialized # dev: can only initialize once
    self.initialized = True

    assert empty(address) not in [_legoRegistry, _wethAddr, _owner] # dev: invalid addrs
    assert _initialAgent != _owner # dev: agent cannot be owner
    self.legoRegistry = _legoRegistry
    self.wethAddr = _wethAddr
    self.owner = _owner

    if _initialAgent != empty(address):
        self.agentSettings[_initialAgent] = AgentInfo(isActive=True, allowedAssets=[], allowedLegoIds=[])

    return True


@pure
@external
def apiVersion() -> String[28]:
    """
    @notice Returns the current API version of the contract
    @dev Returns a constant string representing the contract version
    @return String[28] The API version string
    """
    return API_VERSION


################
# Agent Access #
################


@view
@external
def canAgentAccess(_agent: address, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS]) -> bool:
    """
    @notice Checks if an agent has access to specific assets and lego IDs
    @dev Validates agent permissions against their stored settings
    @param _agent The address of the agent to check
    @param _assets List of asset addresses to validate
    @param _legoIds List of lego IDs to validate
    @return bool True if agent has access to all specified assets and legos
    """
    return self._canAgentAccess(self.agentSettings[_agent], _assets, _legoIds)


@view
@internal
def _canAgentAccess(_agent: AgentInfo, _assets: DynArray[address, MAX_ASSETS], _legoIds: DynArray[uint256, MAX_LEGOS]) -> bool:
    if not _agent.isActive:
        return False

    # check allowed assets
    if len(_agent.allowedAssets) != 0:
        for i: uint256 in range(len(_assets), bound=MAX_ASSETS):
            asset: address = _assets[i]
            if asset != empty(address) and asset not in _agent.allowedAssets:
                return False

    # check allowed lego ids
    if len(_agent.allowedLegoIds) != 0:
        for i: uint256 in range(len(_legoIds), bound=MAX_LEGOS):
            legoId: uint256 = _legoIds[i]
            if legoId != 0 and legoId not in _agent.allowedLegoIds:
                return False

    return True


@view
@internal
def _checkSignerPermissions(
    _signer: address,
    _owner: address,
    _assets: DynArray[address, MAX_ASSETS] = [],
    _legoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> bool:
    if _signer == _owner:
        return False
    
    # if signer is not owner, check if they have access to the assets and lego ids
    assert self._canAgentAccess(self.agentSettings[_signer], _assets, _legoIds) # dev: agent not allowed

    return True


###########
# Deposit #
###########


@nonreentrant
@external
def depositTokens(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _vault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
    """
    @notice Deposits tokens into a specified lego integration and vault
    @param _legoId The ID of the lego to use for deposit
    @param _asset The address of the token to deposit
    @param _amount The amount to deposit (defaults to max)
    @param _vault The target vault address (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets deposited
    @return address The vault token address
    @return uint256 The amount of vault tokens received
    """
    signer: address = self._getSignerOnDeposit(_legoId, _asset, _amount, _vault, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, self.owner, [_asset], [_legoId])
    return self._depositTokens(signer, _legoId, _asset, _amount, _vault, isSignerAgent)


@nonreentrant
@external
def depositTokensWithTransfer(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _vault: address = empty(address),
) -> (uint256, address, uint256):
    """
    @notice Transfers tokens from sender and deposits them into a specified lego integration and vault
    @param _legoId The ID of the lego to use for deposit
    @param _asset The address of the token to deposit
    @param _amount The amount to deposit (defaults to max)
    @param _vault The target vault address (optional)
    @return uint256 The amount of assets deposited
    @return address The vault token address
    @return uint256 The amount of vault tokens received
    """
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, amount, default_return_value=True) # dev: transfer failed
    return self._depositTokens(msg.sender, _legoId, _asset, amount, _vault, self.agentSettings[msg.sender].isActive)


@internal
def _depositTokens(
    _signer: address,
    _legoId: uint256,
    _asset: address,
    _amount: uint256,
    _vault: address,
    _isSignerAgent: bool,
) -> (uint256, address, uint256):
    legoAddr: address = staticcall LegoRegistry(self.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize amount
    wantedAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert wantedAmount != 0 # dev: nothing to transfer
    assert extcall IERC20(_asset).approve(legoAddr, wantedAmount, default_return_value=True) # dev: approval failed

    # deposit into lego partner
    assetAmountDeposited: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    refundAssetAmount: uint256 = 0
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, refundAssetAmount = extcall LegoPartner(legoAddr).depositTokens(_asset, wantedAmount, _vault, self)
    assert extcall IERC20(_asset).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticDeposit(_signer, _asset, vaultToken, assetAmountDeposited, vaultTokenAmountReceived, refundAssetAmount, _legoId, legoAddr, msg.sender, _isSignerAgent)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived


@internal
def _getSignerOnDeposit(
    _legoId: uint256,
    _asset: address,
    _amount: uint256,
    _vault: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(DEPOSIT_TYPE_HASH, _legoId, _asset, _amount, _vault, _sig.expiration), _sig)

    return _sig.signer


############
# Withdraw #
############


@nonreentrant
@external
def withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _vaultToken: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256):
    """
    @notice Withdraws tokens from a specified lego integration and vault
    @param _legoId The ID of the lego to use for withdrawal
    @param _asset The address of the token to withdraw
    @param _amount The amount to withdraw (defaults to max)
    @param _vaultToken The vault token address (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets received
    @return uint256 The amount of vault tokens burned
    """
    signer: address = self._getSignerOnWithdrawal(_legoId, _asset, _amount, _vaultToken, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, self.owner, [_asset], [_legoId])
    return self._withdrawTokens(signer, _legoId, _asset, _amount, _vaultToken, isSignerAgent)


@internal
def _withdrawTokens(
    _signer: address,
    _legoId: uint256,
    _asset: address,
    _amount: uint256,
    _vaultToken: address,
    _isSignerAgent: bool,
) -> (uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(self.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # finalize amount, this will look at vault token balance (not always 1:1 with underlying asset)
    withdrawAmount: uint256 = _amount
    if _vaultToken != empty(address):
        withdrawAmount = min(_amount, staticcall IERC20(_vaultToken).balanceOf(self))

        # some vault tokens require max value approval (comp v3)
        assert extcall IERC20(_vaultToken).approve(legoAddr, max_value(uint256), default_return_value=True) # dev: approval failed

    assert withdrawAmount != 0 # dev: nothing to withdraw

    # withdraw from lego partner
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    refundVaultTokenAmount: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount = extcall LegoPartner(legoAddr).withdrawTokens(_asset, withdrawAmount, _vaultToken, self)

    # zero out approvals
    if _vaultToken != empty(address):
        assert extcall IERC20(_vaultToken).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticWithdrawal(_signer, _asset, _vaultToken, assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount, _legoId, legoAddr, msg.sender, _isSignerAgent)
    return assetAmountReceived, vaultTokenAmountBurned


@internal
def _getSignerOnWithdrawal(
    _legoId: uint256,
    _asset: address,
    _amount: uint256,
    _vaultToken: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(WITHDRAWAL_TYPE_HASH, _legoId, _asset, _amount, _vaultToken, _sig.expiration), _sig)

    return _sig.signer


#############
# Rebalance #
#############


@nonreentrant
@external
def rebalance(
    _fromLegoId: uint256,
    _toLegoId: uint256,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _fromVaultToken: address = empty(address),
    _toVault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
    """
    @notice Withdraws tokens from one lego and deposits them into another (always same asset)
    @param _fromLegoId The ID of the source lego
    @param _toLegoId The ID of the destination lego
    @param _asset The address of the token to rebalance
    @param _amount The amount to rebalance (defaults to max)
    @param _fromVaultToken The source vault token address (optional)
    @param _toVault The destination vault address (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets deposited in the destination vault
    @return address The destination vault token address
    @return uint256 The amount of destination vault tokens received
    """
    signer: address = self._getSignerOnRebalance(_fromLegoId, _toLegoId, _asset, _amount, _fromVaultToken, _toVault, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, self.owner, [_asset], [_fromLegoId, _toLegoId])
    return self._rebalance(signer, _fromLegoId, _toLegoId, _asset, _amount, _fromVaultToken, _toVault, isSignerAgent)


@internal
def _rebalance(
    _signer: address,
    _fromLegoId: uint256,
    _toLegoId: uint256,
    _asset: address,
    _amount: uint256,
    _fromVaultToken: address,
    _toVault: address,
    _isSignerAgent: bool,
) -> (uint256, address, uint256):

    # withdraw from the first lego
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned = self._withdrawTokens(_signer, _fromLegoId, _asset, _amount, _fromVaultToken, _isSignerAgent)

    # deposit the received assets into the second lego
    assetAmountDeposited: uint256 = 0
    newVaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived = self._depositTokens(_signer, _toLegoId, _asset, assetAmountReceived, _toVault, _isSignerAgent)

    return assetAmountDeposited, newVaultToken, vaultTokenAmountReceived


@internal
def _getSignerOnRebalance(
    _fromLegoId: uint256,
    _toLegoId: uint256,
    _asset: address,
    _amount: uint256,
    _fromVaultToken: address,
    _toVault: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(REBALANCE_TYPE_HASH, _fromLegoId, _toLegoId, _asset, _amount, _fromVaultToken, _toVault, _sig.expiration), _sig)

    return _sig.signer


########
# Swap #
########


@nonreentrant
@external
def swapTokens(
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256 = max_value(uint256),
    _minAmountOut: uint256 = 0,
    _sig: Signature = empty(Signature),
) -> (uint256, uint256):
    """
    @notice Swaps tokens using a specified lego integration
    @dev Validates agent permissions if caller is not the owner
    @param _legoId The ID of the lego to use for swapping
    @param _tokenIn The address of the token to swap from
    @param _tokenOut The address of the token to swap to
    @param _amountIn The amount of input tokens to swap (defaults to max balance)
    @param _minAmountOut The minimum amount of output tokens to receive (defaults to 0)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The actual amount of input tokens swapped
    @return uint256 The amount of output tokens received
    """
    signer: address = self._getSignerOnSwap(_legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, self.owner, [_tokenIn, _tokenOut], [_legoId])
    return self._swapTokens(signer, _legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, isSignerAgent)


@internal
def _swapTokens(
    _signer: address,
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256, 
    _isSignerAgent: bool,
) -> (uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(self.legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego
    assert empty(address) not in [_tokenIn, _tokenOut] # dev: invalid tokens

    # finalize amount
    swapAmount: uint256 = min(_amountIn, staticcall IERC20(_tokenIn).balanceOf(self))
    assert swapAmount != 0 # dev: nothing to swap
    assert extcall IERC20(_tokenIn).approve(legoAddr, swapAmount, default_return_value=True) # dev: approval failed

    # swap assets via lego partner
    actualSwapAmount: uint256 = 0
    toAmount: uint256 = 0
    refundAssetAmount: uint256 = 0
    actualSwapAmount, toAmount, refundAssetAmount = extcall LegoPartner(legoAddr).swapTokens(_tokenIn, _tokenOut, swapAmount, _minAmountOut, self)
    assert extcall IERC20(_tokenIn).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log AgenticSwap(_signer, _tokenIn, _tokenOut, actualSwapAmount, toAmount, refundAssetAmount, _legoId, legoAddr, msg.sender, _isSignerAgent)
    return actualSwapAmount, toAmount


@internal
def _getSignerOnSwap(
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(SWAP_TYPE_HASH, _legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _sig.expiration), _sig)

    return _sig.signer


##################
# Transfer Funds #
##################


@nonreentrant
@external
def transferFunds(
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
    _sig: Signature = empty(Signature),
) -> bool:
    """
    @notice Transfers funds to a specified recipient
    @dev Handles both ETH and token transfers with optional amount specification
    @param _recipient The address to receive the funds
    @param _amount The amount to transfer (defaults to max)
    @param _asset The token address (empty for ETH)
    @param _sig The signature of agent or owner (optional)
    @return bool True if the transfer was successful
    """
    owner: address = self.owner
    signer: address = self._getSignerOnTransfer(_recipient, _amount, _asset, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, owner, [_asset])
    return self._transferFunds(signer, _recipient, _amount, _asset, owner, isSignerAgent)


@internal
def _transferFunds(
    _signer: address,
    _recipient: address,
    _amount: uint256,
    _asset: address,
    _owner: address,
    _isSignerAgent: bool,
) -> bool:
    # validate recipient
    if _recipient != _owner:
        assert self.isRecipientAllowed[_recipient] # dev: recipient not allowed

    # finalize amount
    amount: uint256 = 0
    if _asset == empty(address):
        amount = min(_amount, self.balance)
    else:
        amount = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert amount != 0 # dev: nothing to transfer

    # transfer funds
    if _asset == empty(address):
        send(_recipient, amount)
    else:
        assert extcall IERC20(_asset).transfer(_recipient, amount, default_return_value=True) # dev: transfer failed

    log WalletFundsTransferred(_signer, _recipient, _asset, amount, msg.sender, _isSignerAgent)
    return True


@internal
def _getSignerOnTransfer(
    _recipient: address,
    _amount: uint256,
    _asset: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(TRANSFER_TYPE_HASH, _recipient, _amount, _asset, _sig.expiration), _sig)

    return _sig.signer


# transfer whitelist


@nonreentrant
@external
def setWhitelistAddr(_addr: address, _isAllowed: bool) -> bool:
    """
    @notice Sets or removes an address from the transfer whitelist
    @dev Can only be called by the owner
    @param _addr The external address to whitelist/blacklist
    @param _isAllowed Whether the address can receive funds
    @return bool True if the whitelist was updated successfully
    """
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms

    assert _addr != empty(address) # dev: invalid addr
    assert _addr != owner # dev: owner cannot be whitelisted
    assert _addr != self # dev: wallet cannot be whitelisted
    assert _isAllowed != self.isRecipientAllowed[_addr] # dev: already set

    self.isRecipientAllowed[_addr] = _isAllowed
    log WhitelistAddrSet(_addr, _isAllowed)
    return True


#################
# Batch Actions #
#################


@nonreentrant
@external
def performManyActions(_instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS]) -> bool:
    """
    @notice Performs multiple actions in a single transaction
    @dev Executes a batch of instructions with proper permission checks
    @param _instructions Array of action instructions to execute
    @return bool True if all actions were executed successfully
    """
    assert len(_instructions) != 0 # dev: no instructions

    owner: address = self.owner
    isSignerAgent: bool = False
    agentInfo: AgentInfo = AgentInfo(isActive=True, allowedAssets=[], allowedLegoIds=[])

    # get agent settings
    if msg.sender != owner:
        isSignerAgent = True
        agentInfo = self.agentSettings[msg.sender]
        assert agentInfo.isActive # dev: agent not active

    # iterate through instructions
    for i: uint256 in range(len(_instructions), bound=MAX_INSTRUCTIONS):
        instruction: ActionInstruction = _instructions[i]

        # deposit
        if instruction.action == ActionType.DEPOSIT:
            assert self._canAgentAccess(agentInfo, [instruction.asset], [instruction.legoId]) # dev: not allowed
            self._depositTokens(msg.sender, instruction.legoId, instruction.asset, instruction.amount, instruction.vault, isSignerAgent)

        # withdraw
        elif instruction.action == ActionType.WITHDRAWAL:
            assert self._canAgentAccess(agentInfo, [instruction.asset], [instruction.legoId]) # dev: not allowed
            self._withdrawTokens(msg.sender, instruction.legoId, instruction.asset, instruction.amount, instruction.vault, isSignerAgent)

        # rebalance
        elif instruction.action == ActionType.REBALANCE:
            assert self._canAgentAccess(agentInfo, [instruction.asset], [instruction.legoId, instruction.altLegoId]) # dev: not allowed
            self._rebalance(msg.sender, instruction.legoId, instruction.altLegoId, instruction.asset, instruction.amount, instruction.vault, instruction.altVault, isSignerAgent)

        # transfer
        elif instruction.action == ActionType.TRANSFER:
            assert self._canAgentAccess(agentInfo, [instruction.asset], [instruction.legoId]) # dev: not allowed
            self._transferFunds(msg.sender, instruction.recipient, instruction.amount, instruction.asset, owner, isSignerAgent)

        # swap
        elif instruction.action == ActionType.SWAP:
            assert self._canAgentAccess(agentInfo, [instruction.asset, instruction.altAsset], [instruction.legoId]) # dev: not allowed
            self._swapTokens(msg.sender, instruction.legoId, instruction.asset, instruction.altAsset, instruction.amount, instruction.altAmount, isSignerAgent)

    return True


################
# Wrapped ETH #
################


# eth -> weth


@nonreentrant
@payable
@external
def convertEthToWeth(
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
    """
    @notice Converts ETH to WETH and optionally deposits into a lego integration and vault
    @param _amount The amount of ETH to convert (defaults to max)
    @param _depositLegoId The lego ID to use for deposit (optional)
    @param _depositVault The vault address for deposit (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of assets deposited (if deposit performed)
    @return address The vault token address (if deposit performed)
    @return uint256 The amount of vault tokens received (if deposit performed)
    """
    weth: address = self.wethAddr
    signer: address = self._getSignerOnEthToWeth(_amount, _depositLegoId, _depositVault, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, self.owner, [weth], [_depositLegoId])

    # convert eth to weth
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).deposit(value=amount)
    log EthConvertedToWeth(signer, amount, msg.value, weth, msg.sender, isSignerAgent)

    # deposit weth into lego partner
    assetAmountDeposited: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    if _depositLegoId != 0:
        assetAmountDeposited, vaultToken, vaultTokenAmountReceived = self._depositTokens(signer, _depositLegoId, weth, amount, _depositVault, isSignerAgent)

    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived


@internal
def _getSignerOnEthToWeth(
    _amount: uint256,
    _depositLegoId: uint256,
    _depositVault: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(ETH_TO_WETH_TYPE_HASH, _amount, _depositLegoId, _depositVault, _sig.expiration), _sig)

    return _sig.signer


# weth -> eth


@nonreentrant
@external
def convertWethToEth(
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
    _sig: Signature = empty(Signature),
) -> uint256:
    """
    @notice Converts WETH to ETH and optionally withdraws from a vault first
    @param _amount The amount of WETH to convert (defaults to max)
    @param _recipient The address to receive the ETH (optional)
    @param _withdrawLegoId The lego ID to withdraw from (optional)
    @param _withdrawVaultToken The vault token to withdraw (optional)
    @param _sig The signature of agent or owner (optional)
    @return uint256 The amount of ETH received
    """
    weth: address = self.wethAddr
    owner: address = self.owner
    signer: address = self._getSignerOnWethToEth(_amount, _recipient, _withdrawLegoId, _withdrawVaultToken, _sig)
    isSignerAgent: bool = self._checkSignerPermissions(signer, owner, [weth], [_withdrawLegoId])

    # withdraw weth from lego partner (if applicable)
    amount: uint256 = _amount
    if _withdrawLegoId != 0:
        _na: uint256 = 0
        amount, _na = self._withdrawTokens(signer, _withdrawLegoId, weth, _amount, _withdrawVaultToken, isSignerAgent)

    # convert weth to eth
    amount = min(amount, staticcall IERC20(weth).balanceOf(self))
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).withdraw(amount)
    log WethConvertedToEth(signer, amount, weth, msg.sender, isSignerAgent)

    # transfer eth to recipient (if applicable)
    if _recipient != empty(address):
        self._transferFunds(signer, _recipient, amount, empty(address), owner, isSignerAgent)

    return amount


@internal
def _getSignerOnWethToEth(
    _amount: uint256,
    _recipient: address,
    _withdrawLegoId: uint256,
    _withdrawVaultToken: address,
    _sig: Signature,
) -> address:
    if _sig.signer == empty(address) or _sig.signature == empty(Bytes[65]):
        return msg.sender

    # check if signature is valid
    self._isValidSignature(abi_encode(WETH_TO_ETH_TYPE_HASH, _amount, _recipient, _withdrawLegoId, _withdrawVaultToken, _sig.expiration), _sig)

    return _sig.signer


##################
# Agent Settings #
##################


# add or modify agent settings


@nonreentrant
@external
def addOrModifyAgent(
    _agent: address,
    _allowedAssets: DynArray[address, MAX_ASSETS] = [],
    _allowedLegoIds: DynArray[uint256, MAX_LEGOS] = [],
) -> bool:
    """
    @notice Adds a new agent or modifies an existing agent's permissions
        If empty arrays are provided, the agent has access to all assets and lego ids
    @dev Can only be called by the owner
    @param _agent The address of the agent to add or modify
    @param _allowedAssets List of assets the agent can interact with
    @param _allowedLegoIds List of lego IDs the agent can use
    @return bool True if the agent was successfully added or modified
    """
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms
    assert _agent != owner # dev: agent cannot be owner
    assert _agent != empty(address) # dev: invalid agent

    agentInfo: AgentInfo = self.agentSettings[_agent]
    isNewAgent: bool = not agentInfo.isActive

    # sanitize input data
    agentInfo.allowedAssets, agentInfo.allowedLegoIds = self._sanitizeAgentInputData(_allowedAssets, _allowedLegoIds)

    # save data
    agentInfo.isActive = True
    self.agentSettings[_agent] = agentInfo

    # log event
    if isNewAgent:
        log AgentAdded(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    else:
        log AgentModified(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    return True


@view
@internal
def _sanitizeAgentInputData(
    _allowedAssets: DynArray[address, MAX_ASSETS],
    _allowedLegoIds: DynArray[uint256, MAX_LEGOS],
) -> (DynArray[address, MAX_ASSETS], DynArray[uint256, MAX_LEGOS]):

    # nothing to do here
    if len(_allowedAssets) == 0 and len(_allowedLegoIds) == 0:
        return _allowedAssets, _allowedLegoIds

    # sanitize and dedupe assets
    cleanAssets: DynArray[address, MAX_ASSETS] = []
    for i: uint256 in range(len(_allowedAssets), bound=MAX_ASSETS):
        asset: address = _allowedAssets[i]
        if asset == empty(address):
            continue
        if asset not in cleanAssets:
            cleanAssets.append(asset)

    # validate and dedupe lego ids
    cleanLegoIds: DynArray[uint256, MAX_LEGOS] = []
    if len(_allowedLegoIds) != 0:
        legoRegistry: address = self.legoRegistry
        for i: uint256 in range(len(_allowedLegoIds), bound=MAX_LEGOS):
            legoId: uint256 = _allowedLegoIds[i]
            if not staticcall LegoRegistry(legoRegistry).isValidLegoId(legoId):
                continue
            if legoId not in cleanLegoIds:
                cleanLegoIds.append(legoId)

    return cleanAssets, cleanLegoIds


# disable agent


@nonreentrant
@external
def disableAgent(_agent: address) -> bool:
    """
    @notice Disables an existing agent
    @dev Can only be called by the owner
    @param _agent The address of the agent to disable
    @return bool True if the agent was successfully disabled
    """
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active
    self.agentSettings[_agent] = empty(AgentInfo)

    log AgentDisabled(_agent, len(agentInfo.allowedAssets), len(agentInfo.allowedLegoIds))
    return True


# add lego id for agent


@nonreentrant
@external
def addLegoIdForAgent(_agent: address, _legoId: uint256) -> bool:
    """
    @notice Adds a lego ID to an agent's allowed legos
    @dev Can only be called by the owner
    @param _agent The address of the agent
    @param _legoId The lego ID to add
    @return bool True if the lego ID was successfully added
    """
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active

    assert staticcall LegoRegistry(self.legoRegistry).isValidLegoId(_legoId)
    assert _legoId not in agentInfo.allowedLegoIds # dev: lego id already saved

    # save data
    agentInfo.allowedLegoIds.append(_legoId)
    self.agentSettings[_agent] = agentInfo

    # log event
    log LegoIdAddedToAgent(_agent, _legoId)
    return True


# add asset for agent


@nonreentrant
@external
def addAssetForAgent(_agent: address, _asset: address) -> bool:
    """
    @notice Adds an asset to an agent's allowed assets
    @dev Can only be called by the owner
    @param _agent The address of the agent
    @param _asset The asset address to add
    @return bool True if the asset was successfully added
    """
    assert msg.sender == self.owner # dev: no perms

    agentInfo: AgentInfo = self.agentSettings[_agent]
    assert agentInfo.isActive # dev: agent not active

    assert _asset != empty(address) # dev: invalid asset
    assert _asset not in agentInfo.allowedAssets # dev: asset already saved

    # save data
    agentInfo.allowedAssets.append(_asset)
    self.agentSettings[_agent] = agentInfo

    # log event
    log AssetAddedToAgent(_agent, _asset)
    return True


###########
# EIP-712 #
###########


@view
@external
def DOMAIN_SEPARATOR() -> bytes32:
    return self._domainSeparator()


@view
@internal
def _domainSeparator() -> bytes32:
    return keccak256(
        concat(
            DOMAIN_TYPE_HASH,
            keccak256('AgenticWallet'),
            keccak256(API_VERSION),
            abi_encode(chain.id, self)
        )
    )


@internal
def _isValidSignature(_encodedValue: Bytes[256], _sig: Signature):
    assert not self.usedSignatures[_sig.signature] 
    assert _sig.expiration >= block.timestamp
    
    digest: bytes32 = keccak256(concat(b'\x19\x01', self._domainSeparator(), keccak256(_encodedValue)))

    # NOTE: signature is packed as r, s, v
    r: bytes32 = convert(slice(_sig.signature, 0, 32), bytes32)
    s: bytes32 = convert(slice(_sig.signature, 32, 32), bytes32)
    v: uint8 = convert(slice(_sig.signature, 64, 1), uint8)
    
    response: Bytes[32] = raw_call(
        ECRECOVER_PRECOMPILE,
        abi_encode(digest, v, r, s),
        max_outsize=32,
        is_static_call=True  # This is a view function
    )
    
    assert len(response) == 32  # dev: invalid ecrecover response length
    assert abi_decode(response, address) == _sig.signer
    self.usedSignatures[_sig.signature] = True

