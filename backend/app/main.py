import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core import errors
from app.core.config import settings
from app.core.rate_limit import limiter
from app.routers import baskets, catalog

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="CartWise API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

DOMAIN_ERROR_STATUS = {
    errors.NotFoundError: status.HTTP_404_NOT_FOUND,
    errors.ConflictError: status.HTTP_409_CONFLICT,
    errors.AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    errors.ValidationError: status.HTTP_400_BAD_REQUEST,
    errors.UpstreamError: status.HTTP_502_BAD_GATEWAY,
}


@app.exception_handler(errors.DomainError)
async def domain_error_handler(_request: Request, exc: errors.DomainError):
    code = DOMAIN_ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    if code >= 500:
        logger.error("Upstream failure: %s", exc.detail)
    return JSONResponse(status_code=code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(catalog.router)
app.include_router(baskets.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
