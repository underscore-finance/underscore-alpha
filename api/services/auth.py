from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from api.models import Agent, Agent_Pydantic


# handle api key
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow OPTIONS requests to pass through for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # List of paths that don't require authentication
        open_paths = [
            "/",
            "/login",
            "/login/",
            "/agents",
            "/agents/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/docs/oauth2-redirect"
        ]

        path = request.url.path

        # Check exact matches
        if path in open_paths:
            response = await call_next(request)
            return response

        # Check if path matches /agents/{id} pattern
        if path.startswith("/agents/") and path.count("/") == 2:
            response = await call_next(request)
            return response

        try:
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "API Key header not found"}
                )

            agent = await Agent.get_or_none(api_key=api_key)
            if not agent:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API Key"}
                )

            # Convert agent to pydantic model for serialization
            agent_info = await Agent_Pydantic.from_tortoise_orm(agent)
            request.state.agent = agent_info.model_dump()

            response = await call_next(request)
            return response

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": str(e)}
            )


# Configure OpenAPI security scheme

def setup_auth(app: FastAPI):
    app.add_middleware(APIKeyMiddleware)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add security scheme
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }

        # Add error response schemas
        openapi_schema["components"]["schemas"].update({
            "HTTPError": {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"}
                }
            },
            "HTTPValidationError": {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loc": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "msg": {"type": "string"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            }
        })

        # Add responses to all paths
        for path in openapi_schema["paths"].values():
            for operation in path.values():
                if "responses" not in operation:
                    operation["responses"] = {}
                operation["responses"].update({
                    "401": {
                        "description": "Unauthorized - Invalid or missing API Key",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HTTPError"}
                            }
                        }
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                            }
                        }
                    },
                    "500": {
                        "description": "Internal Server Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HTTPError"}
                            }
                        }
                    }
                })

        openapi_schema["security"] = [{"ApiKeyAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
