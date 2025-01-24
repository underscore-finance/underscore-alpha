from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class Agent(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    wallet_address = fields.CharField(max_length=255)
    pk_id = fields.CharField(max_length=255)
    api_key = fields.CharField(max_length=255)
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
