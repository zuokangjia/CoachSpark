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

# 导入 embedding 维度检测功能
try:
    from app.services.rag_retrieval_service import _detect_vector_dimension
    EMBEDDING_CHECK_ENABLED = True
except ImportError:
    EMBEDDING_CHECK_ENABLED = False
    logger.warning("无法导入 embedding 维度检测功能")

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
    
    # 检测 embedding 模型维度（仅在启用时）
    if EMBEDDING_CHECK_ENABLED:
        try:
            actual_dim = _detect_vector_dimension()
            logger.info(f"✅ Embedding 模型维度检测完成: {actual_dim} 维")
        except Exception as e:
            logger.warning(f"⚠️  Embedding 维度检测失败（不影响服务启动）: {e}")
    
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
