from fastapi import APIRouter, HTTPException, Depends
from api.models import Agent, Agent_Pydantic, User
from typing import List
from pydantic import BaseModel
from uuid import UUID
from api.services.turnkey import turnkey_client
from api.services.auth import generate_api_key, user_auth, requires_user_auth


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


class AgentPrivate(BaseModel):
    id: UUID
    name: str
    description: str | None
    wallet_address: str
    verified: bool
    api_key: str

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


@requires_user_auth()
@router.get("/user/list", response_model=List[AgentPrivate])
async def get_user_agents(user: User = Depends(user_auth)):
    """
    Get all agents for a user.
    """
    agents = await Agent.filter(user=user)
    return agents


@requires_user_auth()
@router.get("/user/get/{agent_id}", response_model=AgentPrivate)
async def get_user_agent(agent_id: str, user: User = Depends(user_auth)):
    """
    Get a single agent for a user.
    """
    agent = await Agent.get_or_none(id=agent_id, user=user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await Agent_Pydantic.from_tortoise_orm(agent)


@requires_user_auth()
@router.post("/user/create", response_model=AgentCreateResponse)
async def create_agent(agent: AgentCreate, user: User = Depends(user_auth)):
    """
    Create an agent for a user.
    """
    # First create agent with basic info
    agent_dict = agent.model_dump()
    agent_dict["verified"] = False
    agent_dict["api_key"] = generate_api_key()
    agent_dict["wallet_address"] = ""  # Temporary empty value
    agent_dict["pk_id"] = ""  # Temporary empty value

    # Create the agent first to get the ID
    agent_obj = await Agent.create(**agent_dict, user=user)

    # Now create the wallet using agent ID
    wallet = await turnkey_client.create_private_key(f"agent-{agent_obj.id}")

    # Update agent with wallet info
    agent_obj.wallet_address = wallet["address"]
    agent_obj.pk_id = wallet["private_key_id"]
    await agent_obj.save()

    return agent_obj


@router.get("/public/list", response_model=List[AgentPublic])
async def get_agents():
    """
    Get all agents.
    """
    return await Agent.all()


@router.get("/public/get/{agent_id}", response_model=AgentPublic)
async def get_agent(agent_id: str):
    """
    Get a single agent.
    """
    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await Agent_Pydantic.from_tortoise_orm(agent)
