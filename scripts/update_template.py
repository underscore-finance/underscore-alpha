import boa
import os
import dotenv
from eth_account import Account

from utils import log
from scripts.deployment.utils import load_deployments, get_contract, deploy_contract, remove_contract

HIGHTOP_AGENT = '0xf1A77E89a38843E95A1634A4EB16854D48d29709'


dotenv.load_dotenv()


def main():
    with boa.set_network_env(os.environ.get('UNDY_RPC_URL') or 'http://localhost:8545'):
        deployer = Account.from_key(os.environ.get('DEPLOYER_PRIVATE_KEY'))
        boa.env.add_account(deployer)
        load_deployments()

        log.h1("Updating Template...")

        factory = get_contract("AgentFactory")
        remove_contract("WalletFunds")
        template = deploy_contract("WalletFunds", "contracts/core/WalletFunds.vy")
        factory.setMainWalletTemplate(template.address)


if __name__ == "__main__":
    main()
