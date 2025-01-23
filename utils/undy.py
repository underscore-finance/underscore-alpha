from contextlib import contextmanager
from typing import NamedTuple
import boa
import os
from eth_account import Account
import json
from generated.types import LegoRegistryContract


class UndyContracts(NamedTuple):
    lego_registry: LegoRegistryContract


def load_undy():
    manifest = json.load(open('generated/manifest.json'))
    lego_registry = boa.load_partial('contracts/core/LegoRegistry.vy').at(manifest['lego_registry'])
    return UndyContracts(
        lego_registry=lego_registry,
    )
