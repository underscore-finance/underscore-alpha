from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
import os
from pathlib import Path

# Get the root directory of project
BASE_DIR = Path(__file__).parent.parent.parent

DB_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite://{BASE_DIR}/db.sqlite3"
)

TORTOISE_ORM = {
    "connections": {
        "default": DB_URL
    },
    "apps": {
        "models": {
            "models": ["api.models", "aerich.models"],
            "default_connection": "default",
        }
    }
}


def init_db(app: FastAPI) -> None:
    """Initialize database connection"""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,  # Set to False in production
        add_exception_handlers=True,
    )
