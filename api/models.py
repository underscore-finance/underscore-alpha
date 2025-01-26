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
