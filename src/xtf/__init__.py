"""Fetch one public X/Twitter URL as a reader-friendly document."""
from .client import fetch, fetch_url
from .errors import (
    InvalidUpstreamResponse,
    InvalidUrl,
    NotFound,
    RateLimited,
    UnsupportedContent,
    UpstreamUnavailable,
    XtfError,
)
from .models import Author, Media, Metrics, Quote, XDocument

__version__ = "3.0.0"

__all__ = [
    "fetch",
    "fetch_url",
    "XDocument",
    "Author",
    "Media",
    "Metrics",
    "Quote",
    "XtfError",
    "InvalidUrl",
    "NotFound",
    "RateLimited",
    "UpstreamUnavailable",
    "InvalidUpstreamResponse",
    "UnsupportedContent",
    "__version__",
]
