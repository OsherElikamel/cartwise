"""Domain errors raised by the service layer.

Services never import FastAPI: they raise these, and app.main maps each
one to an HTTP status in a single exception handler.
"""


class DomainError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


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
