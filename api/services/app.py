from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.services.auth import setup_auth
from api.services.db import init_db

app = FastAPI(redirect_slashes=True)

# Initialize FastAPI
app = FastAPI(
    title="Underscore API",
    version="1.0.0",
    description="API for interacting with Underscore Protocol"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_auth(app)

init_db(app)
