from datetime import datetime, timezone
from typing import Any, Optional, List
from fastapi import Query, Form
from tortoise.expressions import F
from api.models import Message, Agent
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel, ConfigDict
from api.services.auth import requires_user_auth, user_auth, requires_agent_auth, agent_auth
from api.services.dependencies import get_undy
from api.models import User
from api.services.pusher import PusherService
from functools import lru_cache
from time import time

# Router for login
router = APIRouter()
pusher = PusherService()

# Cache for storing access verification results
_access_cache = {}


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    wallet_address: str
    description: str | None
    verified: bool


class Balance(BaseModel):
    balance: Optional[str] = None
    contractAddress: Optional[str] = None
    decimals: Optional[int] = None
    name: Optional[str] = None
    rawBalance: Optional[str] = None
    symbol: Optional[str] = None


class MessageContext(BaseModel):
    balances: Optional[List[Balance]] = None

    def model_dump(self, **kwargs):
        # This ensures the context is JSON serializable
        return super().model_dump(mode='json', **kwargs)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    local_id: Optional[str] = None
    agent: Optional[AgentResponse]
    user_id: Optional[UUID]
    sender: str
    agentic_wallet: str
    message: str
    created_at: datetime
    updated_at: datetime
    context: Optional[MessageContext] = None  # Updated to use MessageContext


class SendUserMessageRequest(BaseModel):
    agentic_wallet: str
    message: str
    agent_wallet: str
    local_id: str
    context: Optional[MessageContext] = None


class SendAgentMessageRequest(BaseModel):
    agentic_wallet: str
    message: str
    local_id: Optional[str] = None


# HELPER FUNCTIONS


async def verify_message_access(agentic_wallet: str, agent_wallet: str | None, user_wallet: str):
    """
    Verify wallet ownership and agent status.
    Short cache to prevent rapid-fire contract calls during message sending.
    """
    # Create cache key
    cache_key = f"{agentic_wallet}:{agent_wallet}:{user_wallet}"
    current_time = time()

    # Check cache with shorter duration (5 seconds)
    if cache_key in _access_cache:
        cached_result, cached_time = _access_cache[cache_key]
        if current_time - cached_time < 5:  # 5 seconds cache
            if isinstance(cached_result, Exception):
                raise cached_result
            return cached_result

    try:
        undy = get_undy()
        wallet_contract = undy.get_agentic_wallet(agentic_wallet)
        if user_wallet:
            # Check wallet ownership
            owner = wallet_contract.owner()
            if owner.lower() != user_wallet.lower():
                raise HTTPException(
                    status_code=403,
                    detail="User does not own this agentic wallet"
                )

        # If there's an agent wallet, verify it's active
        if agent_wallet:
            settings = wallet_contract.agentSettings(agent_wallet)
            if not settings or not settings.isActive:
                raise HTTPException(
                    status_code=403,
                    detail="Agent is not active"
                )

        # Cache successful result
        _access_cache[cache_key] = (True, current_time)
        return True

    except Exception as e:
        # Cache the exception
        _access_cache[cache_key] = (e, current_time)
        raise


async def get_messages(
    wallet: str,
    agent_id: UUID = Query(default=None),
    limit: int = Query(default=50, le=100),  # max 100 messages per request
    before: Optional[datetime] = None,  # timestamp of oldest message in current view
    after: Optional[datetime] = None,  # timestamp of newest message in current view
):
    # Start with base query including agent relationship
    query = (Message.filter(agentic_wallet=wallet)
             .prefetch_related('agent')
             .select_related('agent'))

    if agent_id:
        query = query.filter(agent_id=agent_id)

    if before:
        # Load older messages
        query = query.filter(created_at__lt=before).order_by("-created_at")
        return await query.limit(limit)

    elif after:
        # Sync newer messages (missed while offline)
        query = query.filter(created_at__gt=after).order_by("created_at")
        return await query.all()  # No limit when catching up

    # Initial load - get most recent messages
    query = query.order_by("-created_at")
    return await query.limit(limit)


async def send_message(
    agentic_wallet: str,
    agent: Agent,
    message: str,
    local_id: str,
    sender: str,
    user: Optional[User] = None,
    context: Optional[MessageContext] = None
) -> Message:
    """Helper function to create and broadcast messages"""
    try:
        # Create message with UTC time
        now = datetime.now(timezone.utc)
        message_model = Message(
            local_id=local_id,
            agentic_wallet=agentic_wallet,
            agent=agent,
            user=user,
            sender=sender,
            message=message,
            created_at=now,
            updated_at=now,
        )
        await message_model.save()
        message_data = MessageResponse.model_validate(message_model).model_dump()
        if context:
            message_data['context'] = context.model_dump()  # Convert to dict

        # Broadcast via Pusher
        await pusher.trigger_new_message(
            agentic_wallet,
            agent.wallet_address,
            message_data
        )

        return message_model

    except Exception as e:
        await pusher.trigger_error(
            agentic_wallet,
            agent.wallet_address,
            {'local_id': local_id, 'error': str(e)}
        )
        raise


# USER ENDPOINTS


@requires_user_auth()
@router.post("/pusher/auth/user")
async def pusher_auth_user(
    channel_name: str = Form(...),
    socket_id: str = Form(...),
    user: User = Depends(user_auth)
):
    # Format: private-chat-{wallet}
    try:
        _, _, wallet = channel_name.split('-')

        # Verify user owns this wallet
        await verify_message_access(wallet, None, user.wallet_address)

        # Generate auth signature
        auth = pusher.authenticate(
            channel=channel_name,
            socket_id=socket_id
        )
        return auth
    except Exception as e:
        raise HTTPException(status_code=403, detail="Not authorized to access this channel")


@requires_user_auth()
@router.get("/user/get", response_model=List[MessageResponse])
async def get_user_messages(
    wallet: str,
    limit: int = Query(default=50, le=100),
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
    agent_id: UUID = Query(default=None),
    user: User = Depends(user_auth),
):
    await verify_message_access(wallet, None, user.wallet_address)
    return await get_messages(wallet, agent_id, limit, before, after)


@requires_user_auth()
@router.post("/user/send", response_model=MessageResponse)
async def send_user_message(
    message: SendUserMessageRequest,
    user: User = Depends(user_auth)
):
    agent = await Agent.get_or_none(wallet_address=message.agent_wallet)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await verify_message_access(message.agentic_wallet, message.agent_wallet, user.wallet_address)
    return await send_message(
        agentic_wallet=message.agentic_wallet,
        agent=agent,
        message=message.message,
        local_id=message.local_id,
        sender='user',
        user=user,
        context=message.context
    )


# AGENT ENDPOINTS


@requires_agent_auth()
@router.post("/pusher/auth/agent")
async def pusher_auth_agent(
    channel_name: str = Form(...),
    socket_id: str = Form(...),
    agent: Agent = Depends(agent_auth)
):
    # Format: private-chat-agent-{agent_wallet}
    try:
        _, _, _, agent_wallet = channel_name.split('-')

        # Verify this is the agent's channel
        if agent.wallet_address.lower() != agent_wallet.lower():
            raise HTTPException(status_code=403, detail="Agent not authorized for this channel")

        # Generate auth signature
        auth = pusher.authenticate(
            channel=channel_name,
            socket_id=socket_id
        )
        return auth
    except Exception as e:
        raise HTTPException(status_code=403, detail="Not authorized to access this channel")


@requires_agent_auth()
@router.get("/agent/get", response_model=List[MessageResponse])
async def get_agent_messages(
    wallet: str,
    limit: int = Query(default=50, le=100),
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
    agent: Agent = Depends(agent_auth),
):
    return await get_messages(wallet, agent.id, limit, before, after)


@requires_agent_auth()
@router.post("/agent/send", response_model=MessageResponse)
async def send_agent_message(
    message: SendAgentMessageRequest,
    agent: Agent = Depends(agent_auth)
):

    await verify_message_access(message.agentic_wallet, agent.wallet_address, None)

    return await send_message(
        agentic_wallet=message.agentic_wallet,
        agent=agent,
        message=message.message,
        local_id=message.local_id,
        sender='agent'
    )
