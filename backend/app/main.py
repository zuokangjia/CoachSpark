import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.v1 import api_router
from app.api.v2 import api_router_v2
from app.db.session import engine, Base
from app.core.logging import logger

limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("CoachSpark API started")
    yield


app = FastAPI(
    title="CoachSpark API",
    version="1.0.0",
    description="AI-Powered Interview Preparation Coach",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration={duration}ms"
    )
    return response


app.include_router(api_router)
app.include_router(api_router_v2)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
