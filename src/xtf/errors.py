"""Stable, machine-readable errors exposed by the slim reader package."""
from __future__ import annotations


class XtfError(Exception):
    code = "error"
    retryable = False

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message or self.code,
            "retryable": self.retryable,
        }


class InvalidUrl(XtfError):
    code = "invalid_url"


class NotFound(XtfError):
    code = "not_found"


class RateLimited(XtfError):
    code = "rate_limited"
    retryable = True


class UpstreamUnavailable(XtfError):
    code = "upstream_unavailable"
    retryable = True


class InvalidUpstreamResponse(XtfError):
    code = "invalid_upstream_response"
    retryable = True


class UnsupportedContent(XtfError):
    code = "unsupported_content"
