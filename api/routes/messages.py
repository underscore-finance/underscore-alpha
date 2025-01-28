from datetime import datetime
from typing import Optional
from fastapi import Query
from tortoise.expressions import F
from api.models import Message, Agent, UserMessageCounter, AgentMessageCounter
from uuid import UUID
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel, ConfigDict
from api.services.auth import requires_user_auth, user_auth, requires_agent_auth, agent_auth
from api.services.dependencies import get_undy
from fastapi import Depends
from api.models import User
from utils.undy import UndyContracts
from fastapi import HTTPException

# Router for login
router = APIRouter()


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    agent_id: Optional[UUID]
    user_id: Optional[UUID]
    sender: str
    agentic_wallet: str
    message: str
    created_at: datetime
    updated_at: datetime


class SendUserMessageRequest(BaseModel):
    agentic_wallet: str
    message: str
    agent_wallet: str


class SendAgentMessageRequest(BaseModel):
    agentic_wallet: str
    message: str


class MessageCountResponse(BaseModel):
    message_count: int
    last_message_at: datetime

    class Config:
        from_attributes = True


async def verify_message_access(
    agentic_wallet: str,
    agent_wallet: str = None,
    user_wallet: str = None,
):
    undy = get_undy()
    wallet_contract = undy.get_agentic_wallet(agentic_wallet)
    if user_wallet and wallet_contract.owner() != user_wallet:
        raise HTTPException(status_code=403, detail="User does not own the agentic wallet")
    if agent_wallet and not wallet_contract.agentSettings(agent_wallet).isActive:
        raise HTTPException(status_code=403, detail="Agent is not active for this wallet")


async def get_messages(
    wallet: str,
    agent_id: UUID = Query(default=None),
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
):
    query = Message.filter(agentic_wallet=wallet).order_by("-created_at")
    if agent_id:
        query = query.filter(agent_id=agent_id)
    if before:
        query = query.filter(created_at__lt=before)
    return await query.limit(limit)


async def update_message_counter(agent: str, agentic_wallet: str, last_message_at: datetime):
    # Update user message counter
    user_counter, created = await UserMessageCounter.get_or_create(
        agentic_wallet=agentic_wallet,
        defaults={
            'message_count': 1,
            'last_message_at': last_message_at
        }
    )

    if not created:
        # Perform a direct update on the counter
        await UserMessageCounter.filter(id=user_counter.id).update(
            message_count=F('message_count') + 1,
            last_message_at=last_message_at
        )
        # Refresh the instance to get the updated values
        await user_counter.refresh_from_db()

    # Update agent message counter
    agent_counter, created = await AgentMessageCounter.get_or_create(
        agent=agent,
        defaults={
            'message_count': 1,
            'last_message_at': last_message_at
        }
    )

    if not created:
        # Perform a direct update on the counter
        await AgentMessageCounter.filter(id=agent_counter.id).update(
            message_count=F('message_count') + 1,
            last_message_at=last_message_at
        )
        # Refresh the instance to get the updated values
        await agent_counter.refresh_from_db()


@requires_user_auth()
@router.get("/user/get", response_model=List[MessageResponse])
async def get_user_messages(
    wallet: str,
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
    agent_id: UUID = Query(default=None),
    user: User = Depends(user_auth),
):
    await verify_message_access(wallet, None, user.wallet_address)
    return await get_messages(wallet, agent_id, limit, before)


@requires_user_auth()
@router.post("/user/send", response_model=MessageResponse)
async def send_user_message(
    message: SendUserMessageRequest,
    user: User = Depends(user_auth),

):
    agent = await Agent.get_or_none(wallet_address=message.agent_wallet, user=user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await verify_message_access(message.agentic_wallet, message.agent_wallet, user.wallet_address)
    created_at = datetime.now()
    message_model = Message(
        agentic_wallet=message.agentic_wallet,
        agent=agent,
        user=user,
        sender='user',
        message=message.message,
        created_at=created_at,
    )
    await message_model.save()
    await update_message_counter(agent, message.agentic_wallet, created_at)
    return message_model


@requires_user_auth()
@router.get("/user/count", response_model=MessageCountResponse)
async def get_user_message_count(wallet: str, user: User = Depends(user_auth)):
    await verify_message_access(wallet, None, user.wallet_address)
    counter = await UserMessageCounter.get_or_none(agentic_wallet=wallet)
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return counter


# AGENT MESSAGES


@requires_agent_auth()
@router.get("/agent/get", response_model=List[MessageResponse])
async def get_agent_messages(
    wallet: str,
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
    user_id: UUID = Query(default=None),
    agent: Agent = Depends(agent_auth),
):
    return await get_messages(wallet, agent.id, user_id, limit, before)


@requires_agent_auth()
@router.post("/agent/send", response_model=MessageResponse)
async def send_agent_message(
    message: SendAgentMessageRequest,
    agent: Agent = Depends(agent_auth),

):
    await verify_message_access(message.agentic_wallet, agent.wallet_address)
    created_at = datetime.now()
    message_model = Message(
        agentic_wallet=message.agentic_wallet,
        agent_id=agent.id,
        sender='agent',
        message=message.message,
        created_at=created_at,
    )
    await message_model.save()
    await update_message_counter(agent, message.agentic_wallet, created_at)
    return message_model


@requires_agent_auth()
@router.get("/agent/count", response_model=MessageCountResponse)
async def get_agent_message_count(agent: Agent = Depends(agent_auth)):
    counter = await AgentMessageCounter.get_or_none(agent=agent)
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return counter
