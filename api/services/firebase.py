import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_defunct
from api.models import User

# Load environment variables
load_dotenv()

service_account = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40{os.getenv('FIREBASE_PROJECT_ID')}.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}


# Use a service account
cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred)


def get_user_by_token(token: str):
    return auth.verify_id_token(token)


def verify_signature(address, signature, message):
    # Encode the message
    message_encoded = encode_defunct(text=message)
    # Recover the address from the signature
    recovered_address = Account.recover_message(message_encoded, signature=signature)
    return recovered_address.lower() == address.lower()


async def create_custom_token(address):
    # Create a custom token for the user

    try:
        user = auth.get_user_by_email(f"{address}@underscore.finance")
    except:
        user = auth.create_user(email=f"{address}@underscore.finance", display_name=address)

    custom_token = auth.create_custom_token(user.uid)
    if not await User.get_or_none(firebase_id=user.uid):
        await User.create(firebase_id=user.uid, wallet_address=address, email="")

    return custom_token
