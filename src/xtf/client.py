"""Public URL-to-document client backed by the FxTwitter public API."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import http
from .exceptions import (
    InvalidUpstreamResponse,
    InvalidUrl,
    NotFound,
    RateLimited,
    UpstreamDown,
    UpstreamUnavailable,
)
from .models import XDocument
from .normalize import normalize_document
from .parsers.urls import parse_post_url

API = "https://api.fxtwitter.com"
API_V2 = f"{API}/2"


def _payload(data: Any, field: str, identifier: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise InvalidUpstreamResponse("FxTwitter response is not a JSON object")
    code = data.get("code")
    if code == 404:
        raise NotFound(f"post {identifier} not found")
    if code in (403, 429):
        raise RateLimited(f"FxTwitter rate limited post {identifier}")
    if code != 200:
        raise InvalidUpstreamResponse(
            f"FxTwitter returned code {code}: {data.get('message', 'Unknown')}"
        )
    payload = data.get(field)
    if not isinstance(payload, Mapping):
        raise InvalidUpstreamResponse(f"FxTwitter response is missing the {field!r} object")
    return payload


def _fetch_post(username: str, post_id: str, timeout: float) -> Mapping[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        data = http.get_json(f"{API_V2}/status/{post_id}", headers=headers, timeout=timeout)
        return _payload(data, "status", post_id)
    except (UpstreamDown, InvalidUpstreamResponse) as v2_error:
        try:
            data = http.get_json(
                f"{API}/{username}/status/{post_id}", headers=headers, timeout=timeout
            )
            return _payload(data, "tweet", f"{username}/{post_id}")
        except (UpstreamDown, InvalidUpstreamResponse) as legacy_error:
            raise UpstreamUnavailable(
                f"FxTwitter v2 failed ({v2_error}); legacy endpoint failed ({legacy_error})"
            ) from legacy_error


def fetch(url: str, *, timeout: float = 30.0) -> XDocument:
    """Fetch one public X status/article URL as a reader-friendly document."""
    try:
        parsed = parse_post_url(url)
    except (AttributeError, TypeError, ValueError) as error:
        raise InvalidUrl(str(error)) from error
    return normalize_document(parsed, _fetch_post(parsed.username, parsed.post_id, timeout))


fetch_url = fetch
