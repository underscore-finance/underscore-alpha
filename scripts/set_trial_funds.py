import boa
import os
import dotenv
from eth_account import Account

from utils import log
from scripts.deployment.utils import load_deployments, get_contract, Tokens


dotenv.load_dotenv()


def main():
    with boa.set_network_env(os.environ.get('UNDY_RPC_URL') or 'http://localhost:8545'):
        deployer = Account.from_key(os.environ.get('DEPLOYER_PRIVATE_KEY'))
        boa.env.add_account(deployer)

        log.h1("Setting Trial Funds...")
        load_deployments()

        wallet = get_contract("AgentFactory").setTrialFundsData(
            Tokens.USDC, 10000000
        )
        print('Trial funds set', wallet)


if __name__ == "__main__":
    main()
