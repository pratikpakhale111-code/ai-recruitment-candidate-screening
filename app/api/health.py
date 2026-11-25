from fastapi import APIRouter

from app.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check application health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
