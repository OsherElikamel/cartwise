import logging

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from app.core.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["Diagnostics"])
logger = logging.getLogger("cartwise.client")


class ClientError(BaseModel):
    message: str = Field(max_length=500)
    stack: str | None = Field(None, max_length=4000)
    url: str = Field(max_length=300)


@router.post("/client-errors", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
def report_client_error(request: Request, data: ClientError):
    """A crash on someone's screen, logged where we can see it."""
    logger.error("Browser crash on %s: %s\n%s", data.url, data.message, data.stack or "")
