from api.services.app import app
from api.routes.legos import router as legos_router
from api.routes.agents import router as agents_router
from api.routes.login import router as login_router
from api.routes.messages import router as messages_router
from pydantic import BaseModel
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Include API routes
app.include_router(legos_router, prefix="/legos", tags=["Legos"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(login_router, prefix="/login", tags=["Login"])
app.include_router(messages_router, prefix="/messages", tags=["Messages"])


class RootResponse(BaseModel):
    message: str


@app.get("/", response_model=RootResponse)
def read_root():
    return {
        "message": "Welcome to the Underscore API",
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")  # This will print the detailed validation errors
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.on_event("startup")
async def startup_event():
    print("Available routes:")
    for route in app.routes:
        print(f"{route.methods} {route.path}")
