import pytest
import boa

from eth_account import Account
from contracts.core import WalletFunds, WalletConfig, AgentTemplate
from constants import ZERO_ADDRESS


@pytest.fixture(scope="package")
def ai_wallet(agent_factory, owner, agent):
    w = agent_factory.createUserWallet(owner, agent, sender=owner)
    assert w != ZERO_ADDRESS
    assert agent_factory.isUserWallet(w)
    return WalletFunds.at(w)


@pytest.fixture(scope="package")
def ai_wallet_config(ai_wallet):
    return WalletConfig.at(ai_wallet.walletConfig())


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
                    {"name": "legoId", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "vault", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
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
                    {"name": "legoId", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "vaultToken", "type": "address"},
                    {"name": "vaultTokenAmount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
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
def signTransfer(special_agent_signer):
    def signTransfer(
        _agent,
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
                    {"name": "recipient", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "expiration", "type": "uint256"},
                ],
            },
            "message": {
                "recipient": _recipient,
                "amount": _amount,
                "asset": _asset,
                "expiration": _expiration,
            }
        }
        return (Account.sign_typed_data(special_agent_signer.key, full_message=message).signature, special_agent_signer.address, _expiration)
    yield signTransfer