import boa
import json
from pathlib import Path
from utils.context import get_blockchain_context, get_account
from scripts.generate_contracts import generate_contract_files


def main():
    generate_contract_files()
    with get_blockchain_context():
        deployer = get_account('deployer')
        boa.env.add_account(deployer)
        print("Deploying Undy...")
        deployment = {}

        lego_registry = boa.load('contracts/core/LegoRegistry.vy', deployer,  name='lego_registry')
        deployment['lego_registry'] = lego_registry.address

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
