# @version 0.4.0

from interfaces import UserWalletInterface
from ethereum.ercs import IERC20

flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP
    CONVERSION
    ADD_LIQ
    REMOVE_LIQ
    CLAIM_REWARDS
    BORROW
    REPAY

struct Signature:
    signature: Bytes[65]
    signer: address
    expiration: uint256

struct ActionInstruction:
    usePrevAmountOut: bool
    action: ActionType
    legoId: uint256
    asset: address
    vault: address
    amount: uint256
    altLegoId: uint256
    altAsset: address
    altVault: address
    altAmount: uint256
    minAmountOut: uint256
    pool: address
    proof: bytes32
    nftAddr: address
    nftTokenId: uint256
    tickLower: int24
    tickUpper: int24
    minAmountA: uint256
    minAmountB: uint256
    minLpAmount: uint256
    liqToRemove: uint256
    recipient: address
    isWethToEthConversion: bool

struct PendingOwner:
    newOwner: address
    initiatedBlock: uint256
    confirmBlock: uint256

event AgentOwnershipChangeInitiated:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    confirmBlock: uint256

event AgentOwnershipChangeConfirmed:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event AgentOwnershipChangeCancelled:
    cancelledOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event AgentOwnershipChangeDelaySet:
    delayBlocks: uint256

event AgentFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

initialized: public(bool)
usedSignatures: public(HashMap[Bytes[65], bool])

# owner
owner: public(address) # owner of the wallet
pendingOwner: public(PendingOwner) # pending owner of the wallet
ownershipChangeDelay: public(uint256) # num blocks to wait before owner can be changed

# eip-712
ECRECOVER_PRECOMPILE: constant(address) = 0x0000000000000000000000000000000000000001
DOMAIN_TYPE_HASH: constant(bytes32) = keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)')
DEPOSIT_TYPE_HASH: constant(bytes32) = keccak256('Deposit(address userWallet,uint256 legoId,address asset,address vault,uint256 amount,uint256 expiration)')
WITHDRAWAL_TYPE_HASH: constant(bytes32) = keccak256('Withdrawal(address userWallet,uint256 legoId,address asset,address vaultToken,uint256 vaultTokenAmount,uint256 expiration)')
REBALANCE_TYPE_HASH: constant(bytes32) = keccak256('Rebalance(address userWallet,uint256 fromLegoId,address fromAsset,address fromVaultToken,uint256 toLegoId,address toVault,uint256 fromVaultTokenAmount,uint256 expiration)')
SWAP_TYPE_HASH: constant(bytes32) = keccak256('Swap(address userWallet,uint256 legoId,address tokenIn,address tokenOut,uint256 amountIn,uint256 minAmountOut,address pool,uint256 expiration)')
ADD_LIQ_TYPE_HASH: constant(bytes32) = keccak256('AddLiquidity(address userWallet,uint256 legoId,address nftAddr,uint256 nftTokenId,address pool,address tokenA,address tokenB,uint256 amountA,uint256 amountB,int24 tickLower,int24 tickUpper,uint256 minAmountA,uint256 minAmountB,uint256 minLpAmount,uint256 expiration)')
REMOVE_LIQ_TYPE_HASH: constant(bytes32) = keccak256('RemoveLiquidity(address userWallet,uint256 legoId,address nftAddr,uint256 nftTokenId,address pool,address tokenA,address tokenB,uint256 liqToRemove,uint256 minAmountA,uint256 minAmountB,uint256 expiration)')
TRANSFER_TYPE_HASH: constant(bytes32) = keccak256('Transfer(address userWallet,address recipient,uint256 amount,address asset,uint256 expiration)')
ETH_TO_WETH_TYPE_HASH: constant(bytes32) = keccak256('EthToWeth(address userWallet,uint256 amount,uint256 depositLegoId,address depositVault,uint256 expiration)')
WETH_TO_ETH_TYPE_HASH: constant(bytes32) = keccak256('WethToEth(address userWallet,uint256 amount,address recipient,uint256 withdrawLegoId,address withdrawVaultToken,uint256 expiration)')
CLAIM_REWARDS_TYPE_HASH: constant(bytes32) = keccak256('ClaimRewards(address userWallet,uint256 legoId,address market,address rewardToken,uint256 rewardAmount,bytes32 proof,uint256 expiration)')
BORROW_TYPE_HASH: constant(bytes32) = keccak256('Borrow(address userWallet,uint256 legoId,address borrowAsset,uint256 amount,uint256 expiration)')
REPAY_TYPE_HASH: constant(bytes32) = keccak256('Repay(address userWallet,uint256 legoId,address paymentAsset,uint256 paymentAmount,uint256 expiration)')
BATCH_ACTIONS_TYPE_HASH: constant(bytes32) =  keccak256('BatchActions(address userWallet,ActionInstruction[] instructions,uint256 expiration)')
ACTION_INSTRUCTION_TYPE_HASH: constant(bytes32) = keccak256('ActionInstruction(bool usePrevAmountOut,uint256 action,uint256 legoId,address asset,address vault,uint256 amount,uint256 altLegoId,address altAsset,address altVault,uint256 altAmount,uint256 minAmountOut,address pool,bytes32 proof,address nftAddr,uint256 nftTokenId,int24 tickLower,int24 tickUpper,uint256 minAmountA,uint256 minAmountB,uint256 minLpAmount,uint256 liqToRemove,address recipient,bool isWethToEthConversion)')

MIN_OWNER_CHANGE_DELAY: public(immutable(uint256))
MAX_OWNER_CHANGE_DELAY: public(immutable(uint256))
MAX_INSTRUCTIONS: constant(uint256) = 20
API_VERSION: constant(String[28]) = "0.0.1"


@deploy
def __init__(_minOwnerChangeDelay: uint256, _maxOwnerChangeDelay: uint256):
    MIN_OWNER_CHANGE_DELAY = _minOwnerChangeDelay
    MAX_OWNER_CHANGE_DELAY = _maxOwnerChangeDelay

    # make sure original reference contract can't be initialized
    self.initialized = True


@external
def initialize(_owner: address) -> bool:
    assert not self.initialized # dev: can only initialize once
    self.initialized = True

    assert empty(address) not in [_owner] # dev: invalid addr
    self.owner = _owner
    self.ownershipChangeDelay = MIN_OWNER_CHANGE_DELAY

    return True


@pure
@external
def apiVersion() -> String[28]:
    return API_VERSION


###########
# Deposit #
###########


@nonreentrant
@external
def depositTokens(
    _userWallet: address,
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(DEPOSIT_TYPE_HASH, _userWallet, _legoId, _asset, _vault, _amount, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).depositTokens(_legoId, _asset, _vault, _amount)


############
# Withdraw #
############


@nonreentrant
@external
def withdrawTokens(
    _userWallet: address,
    _legoId: uint256,
    _asset: address,
    _vaultToken: address,
    _vaultTokenAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(WITHDRAWAL_TYPE_HASH, _userWallet, _legoId, _asset, _vaultToken, _vaultTokenAmount, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).withdrawTokens(_legoId, _asset, _vaultToken, _vaultTokenAmount)


#############
# Rebalance #
#############


@nonreentrant
@external
def rebalance(
    _userWallet: address,
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVault: address,
    _fromVaultTokenAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(REBALANCE_TYPE_HASH, _userWallet, _fromLegoId, _fromAsset, _fromVaultToken, _toLegoId, _toVault, _fromVaultTokenAmount, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).rebalance(_fromLegoId, _fromAsset, _fromVaultToken, _toLegoId, _toVault, _fromVaultTokenAmount)


########
# Swap #
########


@nonreentrant
@external
def swapTokens(
    _userWallet: address,
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256 = max_value(uint256),
    _minAmountOut: uint256 = 0,
    _pool: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(SWAP_TYPE_HASH, _userWallet, _legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _pool, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).swapTokens(_legoId, _tokenIn, _tokenOut, _amountIn, _minAmountOut, _pool)


##################
# Borrow + Repay #
##################


@nonreentrant
@external
def borrow(
    _userWallet: address,
    _legoId: uint256,
    _borrowAsset: address = empty(address),
    _amount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (address, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(BORROW_TYPE_HASH, _userWallet, _legoId, _borrowAsset, _amount, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).borrow(_legoId, _borrowAsset, _amount)


@nonreentrant
@external
def repayDebt(
    _userWallet: address,
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _sig: Signature = empty(Signature),
) -> (address, uint256, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(REPAY_TYPE_HASH, _userWallet, _legoId, _paymentAsset, _paymentAmount, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).repayDebt(_legoId, _paymentAsset, _paymentAmount)


#################
# Claim Rewards #
#################


@nonreentrant
@external
def claimRewards(
    _userWallet: address,
    _legoId: uint256,
    _market: address = empty(address),
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _proof: bytes32 = empty(bytes32),
    _sig: Signature = empty(Signature),
):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(CLAIM_REWARDS_TYPE_HASH, _userWallet, _legoId, _market, _rewardToken, _rewardAmount, _proof, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    extcall UserWalletInterface(_userWallet).claimRewards(_legoId, _market, _rewardToken, _rewardAmount, _proof)


#################
# Add Liquidity #
#################


@nonreentrant
@external
def addLiquidity(
    _userWallet: address,
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _tickLower: int24 = min_value(int24),
    _tickUpper: int24 = max_value(int24),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _minLpAmount: uint256 = 0,
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256, uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(ADD_LIQ_TYPE_HASH, _userWallet, _legoId, _nftAddr, _nftTokenId, _pool, _tokenA, _tokenB, _amountA, _amountB, _tickLower, _tickUpper, _minAmountA, _minAmountB, _minLpAmount, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).addLiquidity(_legoId, _nftAddr, _nftTokenId, _pool, _tokenA, _tokenB, _amountA, _amountB, _tickLower, _tickUpper, _minAmountA, _minAmountB, _minLpAmount)


####################
# Remove Liquidity #
####################


@nonreentrant
@external
def removeLiquidity(
    _userWallet: address,
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _liqToRemove: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _sig: Signature = empty(Signature),
) -> (uint256, uint256, uint256, bool):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(REMOVE_LIQ_TYPE_HASH, _userWallet, _legoId, _nftAddr, _nftTokenId, _pool, _tokenA, _tokenB, _liqToRemove, _minAmountA, _minAmountB, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).removeLiquidity(_legoId, _nftAddr, _nftTokenId, _pool, _tokenA, _tokenB, _liqToRemove, _minAmountA, _minAmountB)


##################
# Transfer Funds #
##################


@nonreentrant
@external
def transferFunds(
    _userWallet: address,
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(TRANSFER_TYPE_HASH, _userWallet, _recipient, _amount, _asset, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).transferFunds(_recipient, _amount, _asset)


################
# Wrapped ETH #
################


# eth -> weth


@nonreentrant
@external
def convertEthToWeth(
    _userWallet: address,
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
    _sig: Signature = empty(Signature),
) -> (uint256, address, uint256):
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(ETH_TO_WETH_TYPE_HASH, _userWallet, _amount, _depositLegoId, _depositVault, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).convertEthToWeth(_amount, _depositLegoId, _depositVault)


# weth -> eth


@nonreentrant
@external
def convertWethToEth(
    _userWallet: address,
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultToken: address = empty(address),
    _sig: Signature = empty(Signature),
) -> uint256:
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidSignature(abi_encode(WETH_TO_ETH_TYPE_HASH, _userWallet, _amount, _recipient, _withdrawLegoId, _withdrawVaultToken, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer
    return extcall UserWalletInterface(_userWallet).convertWethToEth(_amount, _recipient, _withdrawLegoId, _withdrawVaultToken)


#################
# Batch Actions #
#################


@nonreentrant
@external
def performBatchActions(
    _userWallet: address,
    _instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS],
    _sig: Signature = empty(Signature),
) -> bool:
    owner: address = self.owner
    if msg.sender != owner:
        self._isValidBatchSignature(self._hashBatchActions(_userWallet, _instructions, _sig.expiration), _sig)
        assert _sig.signer == owner # dev: invalid signer

    assert len(_instructions) != 0 # dev: no instructions
    prevAmountReceived: uint256 = 0

    # not using these vars
    naAddyA: address = empty(address)
    naValueA: uint256 = 0
    naValueB: uint256 = 0
    naValueC: uint256 = 0
    naValueD: uint256 = 0
    naBool: bool = False

    # iterate through instructions
    for j: uint256 in range(len(_instructions), bound=MAX_INSTRUCTIONS):
        i: ActionInstruction = _instructions[j]

        # deposit
        if i.action == ActionType.DEPOSIT:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            naValueA, naAddyA, prevAmountReceived, naValueB = extcall UserWalletInterface(_userWallet).depositTokens(i.legoId, i.asset, i.vault, amount)

        # withdraw
        elif i.action == ActionType.WITHDRAWAL:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            prevAmountReceived, naValueA, naValueB = extcall UserWalletInterface(_userWallet).withdrawTokens(i.legoId, i.asset, i.vault, amount)

        # rebalance
        elif i.action == ActionType.REBALANCE:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            naValueA, naAddyA, prevAmountReceived, naValueB = extcall UserWalletInterface(_userWallet).rebalance(i.legoId, i.asset, i.vault, i.altLegoId, i.altVault, amount)

        # swap
        elif i.action == ActionType.SWAP:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            naValueA, prevAmountReceived, naValueB = extcall UserWalletInterface(_userWallet).swapTokens(i.legoId, i.asset, i.altAsset, amount, i.minAmountOut, i.pool)

        # borrow
        elif i.action == ActionType.BORROW:
            naAddyA, prevAmountReceived, naValueB = extcall UserWalletInterface(_userWallet).borrow(i.legoId, i.asset, i.amount)

        # repay debt
        elif i.action == ActionType.REPAY:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            extcall UserWalletInterface(_userWallet).repayDebt(i.legoId, i.asset, amount)
            prevAmountReceived = 0

        # claim rewards
        elif i.action == ActionType.CLAIM_REWARDS:
            extcall UserWalletInterface(_userWallet).claimRewards(i.legoId, i.asset, i.altAsset, i.amount, i.proof)
            prevAmountReceived = 0

        # add liquidity
        elif i.action == ActionType.ADD_LIQ:
            amount: uint256 = i.amount # this only goes towards token A amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            prevAmountReceived, naValueA, naValueB, naValueC, naValueD = extcall UserWalletInterface(_userWallet).addLiquidity(i.legoId, i.nftAddr, i.nftTokenId, i.pool, i.asset, i.altAsset, amount, i.altAmount, i.tickLower, i.tickUpper, i.minAmountA, i.minAmountB, i.minLpAmount)

        # remove liquidity
        elif i.action == ActionType.REMOVE_LIQ:
            amount: uint256 = i.liqToRemove # this only goes to `_liqToRemove`
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            naValueA, naValueB, naValueC, naBool = extcall UserWalletInterface(_userWallet).removeLiquidity(i.legoId, i.nftAddr, i.nftTokenId, i.pool, i.asset, i.altAsset, amount, i.minAmountA, i.minAmountB)
            prevAmountReceived = 0

        # transfer
        elif i.action == ActionType.TRANSFER:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            extcall UserWalletInterface(_userWallet).transferFunds(i.recipient, amount, i.asset)
            prevAmountReceived = 0

        # conversion
        elif i.action == ActionType.CONVERSION:
            amount: uint256 = i.amount
            if i.usePrevAmountOut and prevAmountReceived != 0:
                amount = prevAmountReceived
            if i.isWethToEthConversion:
                prevAmountReceived = extcall UserWalletInterface(_userWallet).convertWethToEth(amount, i.recipient, i.legoId, i.vault)
            else:
                prevAmountReceived, naAddyA, naValueB = extcall UserWalletInterface(_userWallet).convertEthToWeth(amount, i.legoId, i.vault)
                if naValueB != 0:
                    prevAmountReceived = naValueB

    return True


###########
# EIP 712 #
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
            keccak256('UnderscoreAgent'),
            keccak256(API_VERSION),
            abi_encode(chain.id, self)
        )
    )


@internal
def _isValidSignature(_encodedValue: Bytes[512], _sig: Signature):
    assert not self.usedSignatures[_sig.signature] # dev: signature already used
    assert _sig.expiration >= block.timestamp # dev: signature expired
    
    digest: bytes32 = keccak256(concat(b'\x19\x01', self._domainSeparator(), keccak256(_encodedValue)))

    # NOTE: signature is packed as r, s, v
    r: bytes32 = convert(slice(_sig.signature, 0, 32), bytes32)
    s: bytes32 = convert(slice(_sig.signature, 32, 32), bytes32)
    v: uint8 = convert(slice(_sig.signature, 64, 1), uint8)
    
    response: Bytes[32] = raw_call(
        ECRECOVER_PRECOMPILE,
        abi_encode(digest, v, r, s),
        max_outsize=32,
        is_static_call=True # This is a view function
    )
    
    assert len(response) == 32 # dev: invalid ecrecover response length
    assert abi_decode(response, address) == _sig.signer # dev: invalid signature
    self.usedSignatures[_sig.signature] = True


@view
@internal
def _encodeActionInstruction(instr: ActionInstruction) -> Bytes[768]:
    # Just encode, no hash
    return abi_encode(
        ACTION_INSTRUCTION_TYPE_HASH,
        instr.usePrevAmountOut,
        instr.action,
        instr.legoId,
        instr.asset,
        instr.vault,
        instr.amount,
        instr.altLegoId,
        instr.altAsset,
        instr.altVault,
        instr.altAmount,
        instr.minAmountOut,
        instr.pool,
        instr.proof,
        instr.nftAddr,
        instr.nftTokenId,
        instr.tickLower,
        instr.tickUpper,
        instr.minAmountA,
        instr.minAmountB,
        instr.minLpAmount,
        instr.liqToRemove,
        instr.recipient,
        instr.isWethToEthConversion
    )


@view
@internal
def _encodeInstructions(_instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS]) -> Bytes[15360]:
    concatenated: Bytes[15360] = empty(Bytes[15360]) # max size for 20 instructions - 20*768
    for i: uint256 in range(len(_instructions), bound=MAX_INSTRUCTIONS):
        concatenated = convert(
            concat(
                concatenated, 
                self._encodeActionInstruction(_instructions[i])
            ), 
            Bytes[15360]
        )
    return slice(concatenated, 0, len(_instructions) * 768)


@view
@internal
def _hashBatchActions(_userWallet: address, _instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS], _expiration: uint256) -> Bytes[15520]:
    # Now we encode everything and hash only once at the end
    return abi_encode(
        BATCH_ACTIONS_TYPE_HASH,
        _userWallet,
        self._encodeInstructions(_instructions),
        _expiration
    )


@internal
def _isValidBatchSignature(_encodedValue: Bytes[15520], _sig: Signature):
    encoded_hash: bytes32 = keccak256(_encodedValue)
    domain_sep: bytes32 = self._domainSeparator()
    
    digest: bytes32 = keccak256(concat(b'\x19\x01', domain_sep, encoded_hash))
    
    assert not self.usedSignatures[_sig.signature] # dev: signature already used
    assert _sig.expiration >= block.timestamp # dev: signature expired
    
    # NOTE: signature is packed as r, s, v
    r: bytes32 = convert(slice(_sig.signature, 0, 32), bytes32)
    s: bytes32 = convert(slice(_sig.signature, 32, 32), bytes32)
    v: uint8 = convert(slice(_sig.signature, 64, 1), uint8)
    
    response: Bytes[32] = raw_call(
        ECRECOVER_PRECOMPILE,
        abi_encode(digest, v, r, s),
        max_outsize=32,
        is_static_call=True # This is a view function
    )
    
    assert len(response) == 32 # dev: invalid ecrecover response length
    signer: address = abi_decode(response, address)
    assert abi_decode(response, address) == _sig.signer # dev: invalid signature
    self.usedSignatures[_sig.signature] = True


@view
@external
def getBatchActionHash(_userWallet: address, _instructions: DynArray[ActionInstruction, MAX_INSTRUCTIONS], _expiration: uint256) -> bytes32:
    encodedValue: Bytes[15520] = self._hashBatchActions(_userWallet, _instructions, _expiration)
    encoded_hash: bytes32 = keccak256(encodedValue)
    return keccak256(concat(b'\x19\x01', self._domainSeparator(), encoded_hash))


####################
# Ownership Change #
####################


@external
def changeOwnership(_newOwner: address):
    """
    @notice Initiates a new ownership change
    @dev Can only be called by the current owner
    @param _newOwner The address of the new owner
    """
    currentOwner: address = self.owner
    assert msg.sender == currentOwner # dev: no perms
    assert _newOwner not in [empty(address), currentOwner] # dev: invalid new owner

    confirmBlock: uint256 = block.number + self.ownershipChangeDelay
    self.pendingOwner = PendingOwner(
        newOwner= _newOwner,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log AgentOwnershipChangeInitiated(currentOwner, _newOwner, confirmBlock)


@external
def confirmOwnershipChange():
    """
    @notice Confirms the ownership change
    @dev Can only be called by the new owner
    """
    data: PendingOwner = self.pendingOwner
    assert data.newOwner != empty(address) # dev: no pending owner
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached
    assert msg.sender == data.newOwner # dev: only new owner can confirm

    prevOwner: address = self.owner
    self.owner = data.newOwner
    self.pendingOwner = empty(PendingOwner)
    log AgentOwnershipChangeConfirmed(prevOwner, data.newOwner, data.initiatedBlock, data.confirmBlock)


@external
def cancelOwnershipChange():
    """
    @notice Cancels the ownership change
    @dev Can only be called by the current owner
    """
    assert msg.sender == self.owner # dev: no perms
    data: PendingOwner = self.pendingOwner
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingOwner = empty(PendingOwner)
    log AgentOwnershipChangeCancelled(data.newOwner, data.initiatedBlock, data.confirmBlock)


@external
def setOwnershipChangeDelay(_numBlocks: uint256):
    """
    @notice Sets the ownership change delay
    @dev Can only be called by the owner
    @param _numBlocks The number of blocks to wait before ownership can be changed
    """
    assert msg.sender == self.owner # dev: no perms
    assert _numBlocks >= MIN_OWNER_CHANGE_DELAY and _numBlocks <= MAX_OWNER_CHANGE_DELAY # dev: invalid delay
    self.ownershipChangeDelay = _numBlocks
    log AgentOwnershipChangeDelaySet(_numBlocks)


#################
# Recover Funds #
#################


@external
def recoverFunds(_asset: address) -> bool:
    """
    @notice transfers funds from the agent wallet to the owner
    @dev anyone can call this!
    @param _asset The address of the asset to recover
    @return bool True if the funds were recovered successfully
    """
    owner: address = self.owner
    assert msg.sender == owner # dev: no perms
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [owner, _asset] or balance == 0:
        return False

    assert extcall IERC20(_asset).transfer(owner, balance, default_return_value=True) # dev: recovery failed
    log AgentFundsRecovered(_asset, owner, balance)
    return True
