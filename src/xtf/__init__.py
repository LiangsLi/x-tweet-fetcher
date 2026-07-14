"""Fetch one public X/Twitter URL as a reader-friendly document."""
from importlib.metadata import PackageNotFoundError, version

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

try:
    __version__ = version("x-tweet-fetcher")
except PackageNotFoundError:  # Direct PYTHONPATH use without installed metadata.
    __version__ = "0+unknown"

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
