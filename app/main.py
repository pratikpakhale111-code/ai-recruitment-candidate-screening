from fastapi import FastAPI

from app.api.health import router as health_router
from app.settings import settings

app = FastAPI(
    title=settings.app_name,
    description="Evidence-based candidate screening with recruiter-controlled decisions.",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/", tags=["service"], summary="Describe the API")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ready",
        "docs": "/docs",
    }
