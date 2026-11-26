from fastapi import APIRouter

from app.api.applications import router as applications_router
from app.api.candidates import router as candidates_router
from app.api.jobs import router as jobs_router
from app.api.resumes import router as resumes_router
from app.api.screening import router as screening_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(candidates_router)
api_router.include_router(applications_router)
api_router.include_router(resumes_router)
api_router.include_router(screening_router)
