from fastapi import APIRouter

from app.api.v2 import persona
from app.api.v2 import practice
from app.api.v2 import review

api_router_v2 = APIRouter(prefix="/api/v2")
api_router_v2.include_router(persona.router)
api_router_v2.include_router(practice.router)
api_router_v2.include_router(review.router)
