from fastapi import Request
from utils.context import get_blockchain_context
from utils.undy import load_undy, UndyContracts


def get_undy(request: Request) -> UndyContracts:
    print(request.headers)
    with get_blockchain_context():
        return load_undy()
