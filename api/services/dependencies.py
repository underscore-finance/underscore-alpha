import boa

from utils.context import get_blockchain_context
from utils.undy import load_undy, UndyContracts
from utils.context import get_account


def get_undy() -> UndyContracts:
    with get_blockchain_context():
        account = get_account()
        boa.env.add_account(account)
        return load_undy()
