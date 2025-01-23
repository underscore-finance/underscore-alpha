import boa
from contextlib import contextmanager
import os
from eth_account import Account


@contextmanager
def get_blockchain_context():
    env = boa.set_network_env(os.environ.get('UNDY_RPC_URL') or 'http://localhost:8545')
    yield env


def get_account(key='0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'):
    return Account.from_key(key)
