from api.services.app import app
from api.routes.legos import router as legos_router
from pydantic import BaseModel

# Include API routes
app.include_router(legos_router, prefix="/legos", tags=["Legos"])


class RootResponse(BaseModel):
    message: str


@app.get("/", response_model=RootResponse)
def read_root():
    return {
        "message": "Welcome to the Underscore API",
    }
