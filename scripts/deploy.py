import boa
import os
import dotenv
from eth_account import Account

from utils import log
from scripts.deployment.utils import load_deployments
from scripts.deployment.oracles import deploy_oracles
from scripts.deployment.core import deploy_core
from scripts.deployment.legos import deploy_legos

dotenv.load_dotenv()


def main():
    with boa.set_network_env(os.environ.get('UNDY_RPC_URL') or 'http://localhost:8545'):
        deployer = Account.from_key(os.environ.get('DEPLOYER_PRIVATE_KEY'))
        boa.env.add_account(deployer)

        log.h1("Deploying Underscore...")

        load_deployments()

        deploy_core(deployer)
        deploy_oracles()
        deploy_legos()


if __name__ == "__main__":
    main()
