import boa

from fastapi import Request
from utils.context import get_blockchain_context
from utils.undy import load_undy, UndyContracts
from utils.context import get_account


def get_undy(request: Request) -> UndyContracts:
    key = request.state.agent['pk']
    with get_blockchain_context():
        account = get_account(key)
        boa.env.add_account(account)
        return load_undy()
