from datetime import datetime
from typing import Optional
from fastapi import Query
from tortoise.expressions import F
from api.models import Message, Agent, UserMessageCounter, AgentMessageCounter
from uuid import UUID
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from api.services.auth import requires_user_auth, user_auth, requires_agent_auth, agent_auth
from fastapi import Depends
from api.models import User
from utils.undy import load_undy, UndyContracts
from fastapi import HTTPException

# Router for login
router = APIRouter()


class MessageResponse(BaseModel):
    id: UUID
    agentic_wallet: str
    sender: str
    message: str
    agent: Agent
    created_at: datetime


class SendUserMessageRequest(BaseModel):
    agentic_wallet: str
    message: str
    agent_id: UUID


class SendAgentMessageRequest(BaseModel):
    agentic_wallet: str
    message: str
    user_id: UUID


async def verify_message_access(
    agentic_wallet: str,
    agent_id: UUID,
    user_id: UUID,
    undy: UndyContracts
):
    wallet_contract = undy.get_agentic_wallet(agentic_wallet)
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if wallet_contract.owner() != user.wallet_address:
        raise HTTPException(status_code=403, detail="User does not own the agentic wallet")
    agent = await Agent.get_or_none(id=agent_id, user=user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not wallet_contract.agentSettings(agent.wallet_address).isActive:
        raise HTTPException(status_code=403, detail="Agent is not active for this wallet")


async def get_messages(
    wallet: str,
    agent_id: UUID = Query(default=None),
    user_id: UUID = Query(default=None),
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
):
    query = Message.filter(agentic_wallet=wallet).order_by("-created_at")
    if agent_id:
        query = query.filter(agent_id=agent_id)
    if user_id:
        query = query.filter(user_id=user_id)
    if before:
        query = query.filter(created_at__lt=before)
    return await query.limit(limit)


@requires_user_auth()
@router.get("/user/get", response_model=List[MessageResponse], tags=["User Messages"])
async def get_use_messages(
    wallet: str,
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
    agent_id: UUID = Query(default=None),
    user: User = Depends(user_auth),
):
    return await get_messages(wallet, agent_id, user.id, limit, before)


@requires_user_auth()
@router.post("/user/send", response_model=MessageResponse, tags=["User Messages"])
async def send_message(
    message: SendUserMessageRequest,
    user: User = Depends(user_auth),
    undy: UndyContracts = Depends(load_undy),
):
    await verify_message_access(message.agentic_wallet, message.agent_id, user.id, undy)
    created_at = datetime.now()
    message_model = Message(
        agentic_wallet=message.agentic_wallet,
        agent_id=message.agent_id,
        user=user,
        sender='user',
        message=message.message,
        created_at=created_at,
    )
    await message_model.save()
    await UserMessageCounter.update_or_create(
        user=user,
        defaults={"message_count": 1, "last_message_at": created_at},
        update={"message_count": F("message_count") + 1, "last_message_at": created_at}
    )
    return message_model


@requires_agent_auth()
@router.get("/agent/get", response_model=List[MessageResponse], tags=["Agent Messages"])
async def get_use_messages(
    wallet: str,
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
    user_id: UUID = Query(default=None),
    agent: Agent = Depends(agent_auth),
):
    return await get_messages(wallet, agent.id, user_id, limit, before)


@requires_agent_auth()
@router.post("/agent/send", response_model=MessageResponse, tags=["Agent Messages"])
async def send_message(
    message: SendAgentMessageRequest,
    agent: Agent = Depends(agent_auth),
    undy: UndyContracts = Depends(load_undy),
):
    await verify_message_access(message.agentic_wallet, agent.id, message.user_id, undy)
    created_at = datetime.now()
    message_model = Message(
        agentic_wallet=message.agentic_wallet,
        agent_id=agent.id,
        user_id=message.user_id,
        sender='agent',
        message=message.message,
        created_at=created_at,
    )
    await message_model.save()
    await AgentMessageCounter.update_or_create(
        agent=agent,
        defaults={"message_count": 1, "last_message_at": created_at},
        update={"message_count": F("message_count") + 1, "last_message_at": created_at}
    )
    return message_model
