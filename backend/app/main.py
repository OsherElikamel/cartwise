import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core import errors
from app.core.config import settings
from app.core.rate_limit import limiter
from app.routers import auth, baskets, catalog, client_errors, lists, localities, matches, me

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="CartWise API", version="0.1.0")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
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
    http_status = DOMAIN_ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    if http_status >= 500:
        logger.error("Upstream failure: %s", exc.detail)
    return JSONResponse(status_code=http_status, content={"detail": exc.detail, "code": exc.code})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    # Tell the client exactly how long the window is, instead of a vague "later".
    retry_after = exc.limit.limit.get_expiry()
    logger.warning("Rate limit %s hit on %s", exc.limit.limit, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Too many attempts. Try again in {retry_after} seconds.", "code": "rate_limited", "retry_after": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "code": "server_error"})


app.include_router(auth.router)
app.include_router(me.router)
app.include_router(catalog.router)
app.include_router(baskets.router)
app.include_router(matches.router)
app.include_router(lists.router)
app.include_router(localities.router)
app.include_router(client_errors.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
