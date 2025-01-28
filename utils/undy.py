from typing import NamedTuple, Callable
import boa
import json
from generated.types import LegoRegistryContract, WalletTemplateContract


def get_agentic_wallet(wallet_address: str) -> WalletTemplateContract:
    return boa.load_abi('generated/abi/WalletTemplate.json').at(wallet_address)


class UndyContracts(NamedTuple):
    lego_registry: LegoRegistryContract
    get_agentic_wallet: Callable[[str], WalletTemplateContract]


def load_undy():
    manifest = json.load(open('base-sepolia-manifest.json'))
    lego_registry = boa.load_abi('generated/abi/LegoRegistry.json').at(manifest['LegoRegistry'])
    return UndyContracts(
        lego_registry=lego_registry,
        get_agentic_wallet=get_agentic_wallet
    )
