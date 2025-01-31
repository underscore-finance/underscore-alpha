from pusher import Pusher
from typing import Dict, Any
from dotenv import load_dotenv
import os
import json
from uuid import UUID
from datetime import datetime

load_dotenv()


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class PusherService:
    def __init__(self):
        self.client = Pusher(
            app_id=os.getenv('PUSHER_APP_ID'),
            key=os.getenv('PUSHER_KEY'),
            secret=os.getenv('PUSHER_SECRET'),
            cluster=os.getenv('PUSHER_CLUSTER'),
            ssl=True,
            json_encoder=CustomJSONEncoder
        )

    async def trigger_new_message(self, agentic_wallet: str, agent_wallet: str, message_data: dict):
        """Send message to both channels, but include context only in agent channel"""
        user_channel = f'private-chat-{agentic_wallet}'
        agent_channel = f'private-chat-agent-{agent_wallet}'

        # Create a copy without context for user channel
        user_message_data = message_data.copy()
        user_message_data.pop('context', None)

        # Send to user channel without context
        self.client.trigger(user_channel, 'new-message', user_message_data)

        # Send to agent channel with context
        self.client.trigger(agent_channel, 'new-message', message_data)

    async def trigger_error(self, agentic_wallet: str, agent_wallet: str, error_data: dict):
        """Send error event to both channels"""
        user_channel = f"private-chat-{agentic_wallet}"
        agent_channel = f"private-chat-agent-{agent_wallet}"

        self.client.trigger([user_channel, agent_channel], 'message-error', error_data)

    def authenticate(self, channel: str, socket_id: str):
        """Authenticate a channel subscription"""
        return self.client.authenticate(
            channel=channel,
            socket_id=socket_id
        )
