import os


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
EIGHTEEN_DECIMALS = 10**18


FORKS = {
    "mainnet": {
        "rpc_url": f"https://eth-mainnet.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}",
        "etherscan_url": "https://api.etherscan.io/api",
        "etherscan_api_key": os.environ.get("ETHERSCAN_API_KEY"),
        "block": 21552600,
        "anvil": True,
    },
    "base": {
        "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}",
        "block": 24740075,
        "etherscan_url": "https://api.basescan.org/api",
        "etherscan_api_key": os.environ.get("BASESCAN_API_KEY"),
        "anvil": True,
    }
}