from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "agent_message_counters" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "message_count" INT NOT NULL DEFAULT 0,
    "last_message_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "agent_id" CHAR(36) NOT NULL REFERENCES "agents" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "messages" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "sender" VARCHAR(255) NOT NULL,
    "agentic_wallet" VARCHAR(255) NOT NULL,
    "message" TEXT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "agent_id" CHAR(36) REFERENCES "agents" ("id") ON DELETE CASCADE,
    "user_id" CHAR(36) REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_messages_sender_21dfe1" ON "messages" ("sender");
CREATE INDEX IF NOT EXISTS "idx_messages_agentic_94fe99" ON "messages" ("agentic_wallet");
CREATE INDEX IF NOT EXISTS "idx_messages_created_c3e88b" ON "messages" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_messages_agent_i_a72b64" ON "messages" ("agent_id");
CREATE INDEX IF NOT EXISTS "idx_messages_user_id_e06570" ON "messages" ("user_id");
        CREATE TABLE IF NOT EXISTS "user_message_counters" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "message_count" INT NOT NULL DEFAULT 0,
    "last_message_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" CHAR(36) NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "agent_message_counters";
        DROP TABLE IF EXISTS "messages";
        DROP TABLE IF EXISTS "user_message_counters";"""
