from pydantic import BaseModel
from api.routes.agents import router as agents_router
from api.routes.legos import router as legos_router
from api.services.app import app
from dotenv import load_dotenv
load_dotenv()


# Include API routes
app.include_router(legos_router, prefix="/legos", tags=["Legos"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])


class RootResponse(BaseModel):
    message: str


@app.get("/", response_model=RootResponse)
def read_root():
    return {
        "message": "Welcome to the Underscore API",
    }
