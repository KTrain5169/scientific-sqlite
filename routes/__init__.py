from fastapi import APIRouter
from .v1 import user_router, sample_router

api_router = APIRouter()
api_router.include_router(user_router, prefix="/v1")
api_router.include_router(sample_router, prefix="/v1")