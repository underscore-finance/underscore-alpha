from fastapi import APIRouter, HTTPException
from api.models import Agent, Agent_Pydantic
from typing import List
from pydantic import BaseModel
import secrets
import string
from uuid import UUID
from api.services.turnkey import turnkey_client

# Router for agent
router = APIRouter()


class AgentPublic(BaseModel):
    id: UUID
    name: str
    description: str | None
    wallet_address: str
    verified: bool

    model_config = {
        "from_attributes": True,
    }


class AgentCreate(BaseModel):
    name: str
    description: str | None


class AgentCreateResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    wallet_address: str
    verified: bool
    api_key: str


@router.get("/", response_model=List[AgentPublic])
async def get_agents():
    return await Agent.all()


@router.get("/{agent_id}", response_model=AgentPublic)
async def get_agent(agent_id: str):
    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await Agent_Pydantic.from_tortoise_orm(agent)


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/", response_model=AgentCreateResponse)
async def create_agent(agent: AgentCreate):
    # First create agent with basic info
    agent_dict = agent.model_dump()
    agent_dict["verified"] = False
    agent_dict["api_key"] = generate_api_key()
    agent_dict["wallet_address"] = ""  # Temporary empty value
    agent_dict["pk_id"] = ""  # Temporary empty value

    # Create the agent first to get the ID
    agent_obj = await Agent.create(**agent_dict)

    # Now create the wallet using agent ID
    wallet = await turnkey_client.create_private_key(f"agent-{agent_obj.id}")

    # Update agent with wallet info
    agent_obj.wallet_address = wallet["address"]
    agent_obj.pk_id = wallet["private_key_id"]
    await agent_obj.save()

    return agent_obj
