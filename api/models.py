from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class User(models.Model):
    id = fields.UUIDField(pk=True)
    firebase_id = fields.CharField(max_length=255, unique=True)
    email = fields.CharField(max_length=255)
    wallet_address = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"


User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)


class Agent(models.Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="agents")
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    wallet_address = fields.CharField(max_length=255)
    pk_id = fields.CharField(max_length=255)
    api_key = fields.CharField(max_length=255)
    verified = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "agents"

    def __str__(self):
        return self.name


# Create Pydantic models automatically
Agent_Pydantic = pydantic_model_creator(Agent, name="Agent")
AgentIn_Pydantic = pydantic_model_creator(
    Agent, name="AgentIn", exclude_readonly=True
)

AgentPublic_Pydantic = pydantic_model_creator(
    Agent,
    name="AgentPublic",
    include=("id", "name", "description")  # only include these fields
)


class Message(models.Model):
    id = fields.UUIDField(pk=True)
    agent = fields.ForeignKeyField("models.Agent", related_name="messages", null=True, index=True)
    user = fields.ForeignKeyField("models.User", related_name="messages", null=True, index=True)
    sender = fields.CharField(max_length=255, index=True)
    agentic_wallet = fields.CharField(max_length=255, index=True)
    message = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "messages"
        ordering = ["-created_at"]


class UserMessageCounter(models.Model):
    id = fields.UUIDField(pk=True)
    agentic_wallet = fields.CharField(max_length=255, index=True)
    message_count = fields.IntField(default=0)
    last_message_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_message_counters"


class AgentMessageCounter(models.Model):
    id = fields.UUIDField(pk=True)
    agent = fields.ForeignKeyField("models.Agent", related_name="message_counter", unique=True)
    message_count = fields.IntField(default=0)
    last_message_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "agent_message_counters"


# Add this with your other pydantic model creators
Message_Pydantic = pydantic_model_creator(Message, name="Message")
