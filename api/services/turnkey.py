import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from base64 import urlsafe_b64encode
import httpx
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


class TurnkeyClient:
    def __init__(self):
        # Use production URL
        self.base_url = "https://api.turnkey.com/public/v1"  # Added /public to the path
        self.api_public_key = os.getenv("TURNKEY_API_PUBLIC_KEY")
        self.api_private_key = os.getenv("TURNKEY_API_PRIVATE_KEY")
        self.org_id = os.getenv("TURNKEY_ORG_ID")

        if not all([self.api_public_key, self.api_private_key, self.org_id]):
            raise ValueError("Missing required Turnkey environment variables")

    def _create_stamp(self, payload_str: str) -> str:
        try:
            # Convert private key from hex to int
            private_key_int = int(self.api_private_key, 16)

            # Create private key object
            private_key = ec.derive_private_key(
                private_key_int,
                ec.SECP256R1()
            )

            # Sign the payload
            signature = private_key.sign(
                payload_str.encode(),
                ec.ECDSA(hashes.SHA256())
            )

            # Create the stamp structure
            stamp = {
                "publicKey": self.api_public_key,
                "signature": signature.hex(),
                "scheme": "SIGNATURE_SCHEME_TK_API_P256"
            }

            # Base64URL encode the stamp
            encoded_stamp = urlsafe_b64encode(
                json.dumps(stamp).encode()
            ).decode().rstrip("=")

            return encoded_stamp

        except Exception as e:
            raise

    async def whoami(self):
        """Test the API connection"""
        try:
            payload = {
                "organizationId": self.org_id
            }
            payload_str = json.dumps(payload)
            stamp = self._create_stamp(payload_str)

            headers = {
                "Content-Type": "application/json",
                "X-Stamp": stamp
            }

            async with httpx.AsyncClient(verify=True) as client:  # Explicitly enable SSL verification
                response = await client.post(
                    f"{self.base_url}/query/whoami",
                    headers=headers,
                    content=payload_str
                )

                response.raise_for_status()
                return response.json()

        except httpx.ConnectError as e:
            raise
        except Exception as e:
            raise

    async def create_wallet(self, name: str, accounts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new wallet with optional accounts

        Args:
            name: Name of the wallet
            accounts: Optional list of account configurations. Each account should have:
                     - curve: e.g. "CURVE_SECP256K1"
                     - path: e.g. "m/44'/60'/0'/0/0" for Ethereum
                     - pathFormat: e.g. "PATH_FORMAT_BIP32"
                     - addressFormat: e.g. "ADDRESS_FORMAT_ETHEREUM"
        """
        if accounts is None:
            # Default to creating one Ethereum account
            accounts = [{
                "curve": "CURVE_SECP256K1",
                "path": "m/44'/60'/0'/0/0",  # Standard Ethereum derivation path
                "pathFormat": "PATH_FORMAT_BIP32",  # Added pathFormat field
                "addressFormat": "ADDRESS_FORMAT_ETHEREUM"
            }]

        payload = {
            "type": "ACTIVITY_TYPE_CREATE_WALLET",
            "timestampMs": str(int(time.time() * 1000)),
            "organizationId": self.org_id,
            "parameters": {
                "walletName": name,
                "accounts": accounts,
                "mnemonicLength": 24  # Using 24 words for maximum security
            }
        }

        try:
            response = await self._make_request("submit/create_wallet", payload)
            return response
        except httpx.HTTPStatusError as e:
            raise
        except Exception as e:
            raise

    async def get_wallet(self, wallet_id: str) -> Dict[str, Any]:
        """Get details about a Wallet"""
        payload = {
            "organizationId": self.org_id,
            "walletId": wallet_id
        }
        return await self._make_request("query/get_wallet", payload)

    async def get_private_key(self, private_key_id: str) -> Dict[str, Any]:
        """Get details about a Private Key"""
        payload = {
            "organizationId": self.org_id,
            "privateKeyId": private_key_id
        }
        return await self._make_request("query/get_private_key", payload)

    async def create_private_key(self, name: str) -> Dict[str, Any]:
        """Create a new private key using SECP256K1 curve for Ethereum addresses"""
        payload = {
            "type": "ACTIVITY_TYPE_CREATE_PRIVATE_KEYS_V2",
            "timestampMs": str(int(time.time() * 1000)),
            "organizationId": self.org_id,
            "parameters": {
                "privateKeys": [
                    {
                        "privateKeyName": name,
                        "curve": "CURVE_SECP256K1",
                        "addressFormats": ["ADDRESS_FORMAT_ETHEREUM"],
                        "privateKeyTags": []  # Added empty privateKeyTags array as required by API
                    }
                ]
            }
        }

        try:
            response = await self._make_request("submit/create_private_keys", payload)

            # Extract relevant information from response
            result = response['activity']['result']['createPrivateKeysResultV2']['privateKeys'][0]
            return {
                'private_key_id': result['privateKeyId'],
                'address': result['addresses'][0]['address']
            }
        except httpx.HTTPStatusError as e:
            raise
        except Exception as e:
            raise

    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the Turnkey API"""
        payload_str = json.dumps(payload)
        stamp = self._create_stamp(payload_str)

        headers = {
            "Content-Type": "application/json",
            "X-Stamp": stamp
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                content=payload_str
            )
            response.raise_for_status()
            return response.json()


turnkey_client = TurnkeyClient()
