from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.db.session import init_db
from app.settings import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Evidence-based candidate screening with recruiter-controlled decisions.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)


@app.get("/", tags=["service"], summary="Describe the API")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ready",
        "docs": "/docs",
    }
