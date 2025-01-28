from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader, HTTPBearer
from api.models import Agent, Agent_Pydantic, User, User_Pydantic
from api.services.firebase import get_user_by_token
from typing import Callable
import secrets
import string


# Define headers for agentId and apiKey
agent_id_header = APIKeyHeader(name="X-Agent-Id")
agent_key_header = APIKeyHeader(name="X-API-Key")

# JWT Bearer
jwt_bearer = HTTPBearer()

# Configure OpenAPI security scheme


def setup_auth(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            },
            "AgentAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Agent-Id"
            },
            "AgentKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }

        # Add security based on decorator
        for route in app.routes:
            if hasattr(route, "endpoint"):
                path = route.path
                if path in openapi_schema["paths"]:
                    # Get the HTTP method from the route
                    route_method = route.methods.pop().lower()  # GET -> get

                    if route_method in openapi_schema["paths"][path]:
                        operation = openapi_schema["paths"][path][route_method]

                        endpoint = route.endpoint
                        original_endpoint = getattr(endpoint, "__wrapped__", endpoint)

                        requires_user_auth = (
                            hasattr(endpoint, "_requires_user_auth") or
                            hasattr(original_endpoint, "_requires_user_auth")
                        )
                        requires_agent_auth = (
                            hasattr(endpoint, "_requires_agent_auth") or
                            hasattr(original_endpoint, "_requires_agent_auth")
                        )

                        # Reset any existing security
                        if "security" in operation:
                            del operation["security"]

                        # Only add security if explicitly required
                        if requires_user_auth:
                            operation["security"] = [{"BearerAuth": []}]
                            if "summary" in operation:
                                operation["summary"] = f"[User Auth] {operation['summary']}"
                            else:
                                operation["summary"] = "[User Auth]"
                        elif requires_agent_auth:
                            operation["security"] = [{"AgentAuth": [], "AgentKeyAuth": []}]
                            if "summary" in operation:
                                operation["summary"] = f"[Agent Auth] {operation['summary']}"
                            else:
                                operation["summary"] = "[Agent Auth]"

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi


def requires_user_auth():
    """Decorator to mark routes as requiring user authentication"""
    def decorator(func: Callable):
        setattr(func, "_requires_user_auth", True)
        return func
    return decorator


def requires_agent_auth():
    """Decorator to mark routes as requiring agent authentication"""
    def decorator(func: Callable):
        setattr(func, "_requires_agent_auth", True)
        return func
    return decorator


async def user_auth(credentials: HTTPAuthorizationCredentials = Security(jwt_bearer)) -> User:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        if token.startswith('Bearer '):
            token = token[7:]
        firebase_user = get_user_by_token(token)
        user = await User.get_or_none(firebase_id=firebase_user["uid"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Updated auth functions
async def agent_auth(
    agent_id: str = Security(agent_id_header),
    api_key: str = Security(agent_key_header)
) -> Agent:
    if not agent_id or not api_key:
        raise HTTPException(status_code=401, detail="Agent ID or API Key header not found")

    agent = await Agent.get_or_none(id=agent_id, api_key=api_key)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid Agent ID or API Key")
    return agent


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
