from contextlib import contextmanager
from typing import NamedTuple, Callable
import boa
import os
from eth_account import Account
import json
from generated.types import LegoRegistryContract, WalletTemplateContract


def get_agentic_wallet(wallet_address: str) -> WalletTemplateContract:
    return boa.env.lookup_contract(wallet_address)


class UndyContracts(NamedTuple):
    lego_registry: LegoRegistryContract
    get_agentic_wallet: Callable[[str], WalletTemplateContract]


def load_undy():
    manifest = json.load(open('generated/manifest.json'))
    lego_registry = boa.load_partial('contracts/core/LegoRegistry.vy').at(manifest['lego_registry'])
    return UndyContracts(
        lego_registry=lego_registry,
        get_agentic_wallet=get_agentic_wallet
    )
