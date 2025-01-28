from api.services.app import app
from api.routes.legos import router as legos_router
from api.routes.agents import router as agents_router
from api.routes.login import router as login_router
from api.routes.messages import router as messages_router
from pydantic import BaseModel
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
