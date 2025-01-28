import boa
import json
from pathlib import Path
from utils.context import get_blockchain_context, get_account
from scripts.generate_contracts import generate_contract_files
import os
import dotenv

dotenv.load_dotenv()

WETH = '0x4200000000000000000000000000000000000006'


def main():
    generate_contract_files()
    with get_blockchain_context():
        deployer = get_account(os.environ.get('DEPLOYER_PRIVATE_KEY'))
        boa.env.add_account(deployer)
        print("Deploying Undy...")
        deployment = {}

        lego_registry = boa.load('contracts/core/LegoRegistry.vy', deployer,  name='lego_registry')
        deployment['LegoRegistry'] = lego_registry.address

        wallet_template = boa.load('contracts/core/WalletTemplate.vy', name='wallet_template')
        deployment['WalletTemplate'] = wallet_template.address

        agent_factory = boa.load('contracts/core/AgentFactory.vy',
                                 lego_registry.address, WETH,  wallet_template,  name='agent_factory')
        deployment['AgentFactory'] = agent_factory.address

        # mocks

        token = boa.load("contracts/mock/MockErc20.vy", deployer.address, "Alpha Token",
                         "ALPHA", 18, 10_000_000, name="alpha_token")
        mock_vault = boa.load("contracts/mock/MockErc4626Vault.vy", token.address, name="alpha_erc4626_vault")
        mock_lego = boa.load('contracts/mock/MockLego.vy', token.address,
                             mock_vault.address, lego_registry.address, name='mock_lego')
        deployment['MockErc20'] = token.address
        deployment['MockErc4626Vault'] = mock_vault.address
        deployment['MockLego'] = mock_lego.address

        lego_registry.registerNewLego(mock_lego.address, 'Mock Lego')

        # Save to JSON file
        output_dir = Path("generated")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "manifest.json", "w") as f:
            json.dump(deployment, f, indent=2, sort_keys=True)

        print(f"Deployment manifest saved to {output_dir}/manifest.json")

        # Still print to console for visibility
        for key, value in deployment.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
