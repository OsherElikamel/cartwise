"""Domain errors raised by the service layer.

Services never import FastAPI: they raise these, and app.main maps each
one to an HTTP status in a single exception handler.
"""


class DomainError(Exception):
    """`detail` is a readable English message (logs, API docs); `code` is a stable
    identifier the frontend translates, so users see errors in their language."""

    def __init__(self, detail: str, code: str = "error"):
        super().__init__(detail)
        self.detail = detail
        self.code = code


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class UpstreamError(DomainError):
    """An external source (a chain's price portal, the LLM) failed."""
