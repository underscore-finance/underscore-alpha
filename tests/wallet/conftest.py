import pytest
import boa

from eth_account import Account
from contracts.core import WalletFunds, WalletConfig, AgentTemplate
from constants import ZERO_ADDRESS, MAX_UINT256
from eth_account.messages import encode_defunct


@pytest.fixture(scope="package")
def ai_wallet(agent_factory, owner, agent):
    w = agent_factory.createUserWallet(owner, agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return WalletFunds.at(w)


@pytest.fixture(scope="package")
def ai_wallet_config(ai_wallet):
    return WalletConfig.at(ai_wallet.walletConfig())


@pytest.fixture(scope="package")
def createActionInstruction():
    def createActionInstruction(
        _action,
        _legoId,
        _asset,
        _vault,
        _amount,
        _usePrevAmountOut=False,
        _altLegoId=0,
        _altAsset=ZERO_ADDRESS,
        _altVault=ZERO_ADDRESS,
        _altAmount=0,
        _minAmountOut=0,
        _pool=ZERO_ADDRESS,
        _proof=b"",
        _nftAddr=ZERO_ADDRESS,
        _nftTokenId=0,
        _tickLower=0,
        _tickUpper=0,
        _minAmountA=0,
        _minAmountB=0,
        _minLpAmount=0,
        _liqToRemove=0,
        _recipient=ZERO_ADDRESS,
        _isWethToEthConversion=False,
    ):
        return (
            _usePrevAmountOut,
            _action,
            _legoId,
            _asset,
            _vault,
            _amount,
            _altLegoId,
            _altAsset,
            _altVault,
            _altAmount,
            _minAmountOut,
            _pool,
            _proof,
            _nftAddr,
            _nftTokenId,
            _tickLower,
            _tickUpper,
            _minAmountA,
            _minAmountB,
            _minLpAmount,
            _liqToRemove,
            _recipient,
            _isWethToEthConversion,
        )

    yield createActionInstruction


# signature stuff


@pytest.fixture(scope="package")
def special_agent(special_agent_signer, agent_factory):
    w = agent_factory.createAgent(special_agent_signer.address, sender=special_agent_signer.address)
    assert w != ZERO_ADDRESS
    assert agent_factory.isAgent(w)
    return AgentTemplate.at(w)


@pytest.fixture(scope="package")
def special_agent_signer():
    return Account.from_key('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80')


@pytest.fixture(scope="package")
def special_ai_wallet(agent_factory, owner, special_agent):
    w = agent_factory.createUserWallet(owner, special_agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return WalletFunds.at(w)


@pytest.fixture(scope="package")
def special_ai_wallet_config(special_ai_wallet):
    return WalletConfig.at(special_ai_wallet.walletConfig())


@pytest.fixture(scope="package")
def signDeposit(special_agent_signer):
    def signDeposit(
        _agent,
        _userWallet,
        _lego_id,
        _asset,
        _vault,
        _amount,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Deposit": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "vault", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _lego_id,
                "asset": _asset,
                "vault": _vault,
                "amount": _amount,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signDeposit


@pytest.fixture(scope="package")
def signWithdrawal(special_agent_signer):
    def signWithdrawal(
        _agent,
        _userWallet,
        _lego_id,
        _asset,
        _vaultToken,
        _vaultTokenAmount,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Withdrawal": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "vaultToken", "type": "address"},
                    {"name": "vaultTokenAmount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _lego_id,
                "asset": _asset,
                "vaultToken": _vaultToken,
                "vaultTokenAmount": _vaultTokenAmount,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signWithdrawal


@pytest.fixture(scope="package")
def signRebalance(special_agent_signer):
    def signRebalance(
        _agent,
        _userWallet,
        _fromLegoId,
        _fromAsset,
        _fromVaultToken,
        _toLegoId,
        _toVault,
        _fromVaultTokenAmount,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Rebalance": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "fromLegoId", "type": "uint256"},
                    {"name": "fromAsset", "type": "address"},
                    {"name": "fromVaultToken", "type": "address"},
                    {"name": "toLegoId", "type": "uint256"},
                    {"name": "toVault", "type": "address"},
                    {"name": "fromVaultTokenAmount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "fromLegoId": _fromLegoId,
                "fromAsset": _fromAsset,
                "fromVaultToken": _fromVaultToken,
                "toLegoId": _toLegoId,
                "toVault": _toVault,
                "fromVaultTokenAmount": _fromVaultTokenAmount,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signRebalance


@pytest.fixture(scope="package")
def signSwap(special_agent_signer):
    def signSwap(
        _agent,
        _userWallet,
        _legoId,
        _tokenIn,
        _tokenOut,
        _amountIn,
        _minAmountOut,
        _pool,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Swap": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "minAmountOut", "type": "uint256"},
                    {"name": "pool", "type": "address"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _legoId,
                "tokenIn": _tokenIn,
                "tokenOut": _tokenOut,
                "amountIn": _amountIn,
                "minAmountOut": _minAmountOut,
                "pool": _pool,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signSwap


@pytest.fixture(scope="package")
def signBorrow(special_agent_signer):
    def signBorrow(
        _agent,
        _userWallet,
        _legoId,
        _borrowAsset,
        _amount,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Borrow": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "borrowAsset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _legoId,
                "borrowAsset": _borrowAsset,
                "amount": _amount,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signBorrow


@pytest.fixture(scope="package")
def signRepay(special_agent_signer):
    def signRepay(
        _agent,
        _userWallet,
        _legoId,
        _paymentAsset,
        _paymentAmount,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Repay": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "paymentAsset", "type": "address"},
                    {"name": "paymentAmount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _legoId,
                "paymentAsset": _paymentAsset,
                "paymentAmount": _paymentAmount,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signRepay


@pytest.fixture(scope="package")
def signClaimRewards(special_agent_signer):
    def signClaimRewards(
        _agent,
        _userWallet,
        _legoId,
        _market,
        _rewardToken,
        _rewardAmount,
        _proof,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "ClaimRewards": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "market", "type": "address"},
                    {"name": "rewardToken", "type": "address"},
                    {"name": "rewardAmount", "type": "uint256"},
                    {"name": "proof", "type": "bytes32"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _legoId,
                "market": _market,
                "rewardToken": _rewardToken,
                "rewardAmount": _rewardAmount,
                "proof": _proof,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signClaimRewards


@pytest.fixture(scope="package")
def signTransfer(special_agent_signer):
    def signTransfer(
        _agent,
        _userWallet,
        _recipient,
        _amount,
        _asset,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "Transfer": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "recipient", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "recipient": _recipient,
                "amount": _amount,
                "asset": _asset,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signTransfer


@pytest.fixture(scope="package")
def signEthToWeth(special_agent_signer):
    def signEthToWeth(
        _agent,
        _userWallet,
        _amount,
        _depositLegoId,
        _depositVault,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "EthToWeth": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "depositLegoId", "type": "uint256"},
                    {"name": "depositVault", "type": "address"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "amount": _amount,
                "depositLegoId": _depositLegoId,
                "depositVault": _depositVault,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signEthToWeth


@pytest.fixture(scope="package")
def signWethToEth(special_agent_signer):
    def signWethToEth(
        _agent,
        _userWallet,
        _amount,
        _recipient,
        _withdrawLegoId,
        _withdrawVaultToken,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "WethToEth": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "recipient", "type": "address"},
                    {"name": "withdrawLegoId", "type": "uint256"},
                    {"name": "withdrawVaultToken", "type": "address"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "amount": _amount,
                "recipient": _recipient,
                "withdrawLegoId": _withdrawLegoId,
                "withdrawVaultToken": _withdrawVaultToken,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signWethToEth


@pytest.fixture(scope="package")
def signAddLiquidity(special_agent_signer):
    def signAddLiquidity(
        _agent,
        _userWallet,
        _legoId,
        _tokenA,
        _tokenB,
        _amountA=MAX_UINT256,
        _amountB=MAX_UINT256,
        _nftAddr=ZERO_ADDRESS,
        _nftTokenId=0,
        _pool=ZERO_ADDRESS,
        _tickLower=1,
        _tickUpper=1,
        _minAmountA=1,
        _minAmountB=1,
        _minLpAmount=1,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):

        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "AddLiquidity": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "nftAddr", "type": "address"},
                    {"name": "nftTokenId", "type": "uint256"},
                    {"name": "pool", "type": "address"},
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "amountA", "type": "uint256"},
                    {"name": "amountB", "type": "uint256"},
                    {"name": "tickLower", "type": "int24"},
                    {"name": "tickUpper", "type": "int24"},
                    {"name": "minAmountA", "type": "uint256"},
                    {"name": "minAmountB", "type": "uint256"},
                    {"name": "minLpAmount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _legoId,
                "nftAddr": _nftAddr,
                "nftTokenId": _nftTokenId,
                "pool": _pool,
                "tokenA": _tokenA,
                "tokenB": _tokenB,
                "amountA": _amountA,
                "amountB": _amountB,
                "tickLower": _tickLower,
                "tickUpper": _tickUpper,
                "minAmountA": _minAmountA,
                "minAmountB": _minAmountB,
                "minLpAmount": _minLpAmount,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signAddLiquidity


@pytest.fixture(scope="package")
def signRemoveLiquidity(special_agent_signer):
    def signRemoveLiquidity(
        _agent,
        _userWallet,
        _legoId,
        _pool,
        _tokenA,
        _tokenB,
        _nftAddr=ZERO_ADDRESS,
        _nftTokenId=0,
        _liqToRemove=MAX_UINT256,
        _minAmountA=0,
        _minAmountB=0,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):

        # the data to be signed
        message = {
            "domain": {
                "name": "UnderscoreAgent",
                "version": _agent.apiVersion(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _agent.address,
            },
            "types": {
                "RemoveLiquidity": [
                    {"name": "userWallet", "type": "address"},
                    {"name": "legoId", "type": "uint256"},
                    {"name": "nftAddr", "type": "address"},
                    {"name": "nftTokenId", "type": "uint256"},
                    {"name": "pool", "type": "address"},
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "liqToRemove", "type": "uint256"},
                    {"name": "minAmountA", "type": "uint256"},
                    {"name": "minAmountB", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "userWallet": _userWallet.address,
                "legoId": _legoId,
                "nftAddr": _nftAddr,
                "nftTokenId": _nftTokenId,
                "pool": _pool,
                "tokenA": _tokenA,
                "tokenB": _tokenB,
                "liqToRemove": _liqToRemove,
                "minAmountA": _minAmountA,
                "minAmountB": _minAmountB,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signRemoveLiquidity


@pytest.fixture(scope="package")
def signBatchAction(special_agent_signer):
    def signBatchAction(
        _agent,
        _userWallet,
        _instructions,
        _expiration=boa.env.evm.patch.timestamp + 60,  # 1 minute
    ):
        # Get the contract's hash
        message_hash = _agent.getBatchActionHash(_userWallet, _instructions, _expiration)

        # Sign the hash directly without any prefix
        signed = Account._sign_hash(message_hash, special_agent_signer.key)

        return (signed.signature, special_agent_signer.address, _expiration)
    yield signBatchAction
