"""
FastAPI Router Assembly
"""

from fastapi import APIRouter
from backend.app.api.auth import router as auth_router
from backend.app.api.incidents import router as incidents_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.cameras import router as cameras_router
from backend.app.api.zones import router as zones_router
from backend.app.api.audit import router as audit_router
from backend.app.api.stats import router as stats_router
from backend.app.api.pqc import router as pqc_router
from backend.app.api.user_portal import router as user_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(incidents_router)
api_router.include_router(evidence_router)
api_router.include_router(cameras_router)
api_router.include_router(zones_router)
api_router.include_router(audit_router)
api_router.include_router(stats_router)
api_router.include_router(pqc_router)
api_router.include_router(user_router)
