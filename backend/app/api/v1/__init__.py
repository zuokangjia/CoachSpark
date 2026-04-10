from fastapi import APIRouter

from app.api.v1 import companies
from app.api.v1 import interviews
from app.api.v1 import match
from app.api.v1 import review
from app.api.v1 import prep
from app.api.v1 import profile
from app.api.v1 import dashboard
from app.api.v1 import company_brief
from app.api.v1 import offers
from app.api.v1 import resume
from app.api.v1 import push

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(companies.router)
api_router.include_router(interviews.router)
api_router.include_router(match.router)
api_router.include_router(review.router)
api_router.include_router(prep.router)
api_router.include_router(profile.router)
api_router.include_router(dashboard.router)
api_router.include_router(company_brief.router)
api_router.include_router(offers.router)
api_router.include_router(resume.router)
api_router.include_router(push.router)
