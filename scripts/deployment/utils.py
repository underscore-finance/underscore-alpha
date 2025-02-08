import subprocess
import json
from pathlib import Path

import boa
from utils import log


class Tokens:
    USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    WETH = "0x4200000000000000000000000000000000000006"
    CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
    WSTETH = "0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452"
    CBETH = "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22"
    AERO = "0x940181a94a35a4569e4529a3cdfb74e38fd98631"
    EURC = "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42"
    USDS = "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc"
    TBTC = "0x236aa50979d5f3de3bd1eeb40e81137f22ab794b"
    FROK = "0x42069babe14fb1802c5cb0f50bb9d2ad6fef55e2"
    CRVUSD = "0x417ac0e078398c154edfadd9ef675d30be60af93"


class LegoType:
    YIELD_OPP = 2**0  # 2 ** 0 = 1
    DEX = 2**1  # 2 ** 1 = 2


# Declare DEPLOYMENTS as a global variable
DEPLOYMENTS = {}
OUTPUT_DIR = Path("generated")
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"


def load_deployments():
    global DEPLOYMENTS  # Use the global DEPLOYMENTS variable
    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)

    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            log.h3("Loading deployments from manifest...")
            DEPLOYMENTS = json.load(f)
            log.h3(f"Loaded {len(DEPLOYMENTS.keys())} deployments")
    else:
        log.h3("No manifest found, starting fresh...")
        DEPLOYMENTS = {}


def deploy_contract(name, path, *args):
    global DEPLOYMENTS  # Use the global DEPLOYMENTS variable

    if name in DEPLOYMENTS.keys():
        log.h3(f"Contract {name} already deployed at {DEPLOYMENTS[name]['address']}")
        return get_contract(name)

    contract = boa.load(path, *args, name=name)

    abi_result = subprocess.run(
        ["vyper", "-f", "abi", str(path)],
        capture_output=True,
        text=True
    )

    abi = json.loads(abi_result.stdout)

    DEPLOYMENTS[name] = {
        "address": contract.address,
        "abi": abi,
        "path": path,
        "name": name,
    }

    save_manifest()

    return contract


def get_contract(name):
    return boa.load_partial(DEPLOYMENTS[name]['path']).at(DEPLOYMENTS[name]['address'])


def save_manifest():
    # Save to JSON file
    if not Path.exists(OUTPUT_DIR):
        Path.mkdir(OUTPUT_DIR)

    deployment_info = {}
    for key, value in DEPLOYMENTS.items():
        deployment_info[key] = {
            "address": value['address'],
            "abi": value['abi'],
            "path": value['path'],
        }

    with open(OUTPUT_DIR / "manifest.json", "w") as f:
        json.dump(deployment_info, f, indent=2, sort_keys=True)
