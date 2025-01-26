from fastapi import APIRouter, HTTPException
from api.models import Agent, Agent_Pydantic
from typing import List
from pydantic import BaseModel
import secrets
import string
from uuid import UUID
from api.services.firebase import create_custom_token, verify_signature

# Define a Pydantic model for the request body


class LoginRequest(BaseModel):
    address: str
    signature: str
    message: str


# Router for login
router = APIRouter()


@router.post("/")
async def login(request: LoginRequest):
    address = request.address
    signature = request.signature
    message = request.message
    if not verify_signature(address, signature, message):
        raise HTTPException(status_code=401, detail="Invalid signature")
    return await create_custom_token(address)
