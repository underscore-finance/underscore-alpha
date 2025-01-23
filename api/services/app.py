from fastapi import FastAPI
from api.services.auth import setup_auth

# Initialize FastAPI
app = FastAPI(
    title="Underscore API",
    version="1.0.0",
    description="API for interacting with Underscore Protocol"
)

setup_auth(app)
