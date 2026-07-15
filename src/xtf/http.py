"""Small stdlib HTTP client with bounded responses and retry/backoff."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .errors import InvalidUpstreamResponse, NotFound, RateLimited, UpstreamUnavailable

USER_AGENT = "x-tweet-fetcher/4.0"
RETRY_ATTEMPTS = 2
RETRY_BACKOFF_BASE = 1.0
MAX_BODY = 10 * 1024 * 1024


def get_text(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15,
    retries: int = RETRY_ATTEMPTS,
) -> str:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_BODY:
                    raise InvalidUpstreamResponse(f"response too large from {url}")
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise InvalidUpstreamResponse(f"response too large from {url}")
                return body.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise NotFound(f"HTTP 404 — {url}") from error
            if error.code in (403, 429):
                last_error = RateLimited(f"HTTP {error.code} — {url}")
            elif error.code >= 500:
                last_error = UpstreamUnavailable(f"HTTP {error.code} — {url}")
            else:
                raise InvalidUpstreamResponse(
                    f"HTTP {error.code}: {error.reason} — {url}"
                ) from error
        except InvalidUpstreamResponse:
            raise
        except urllib.error.URLError as error:
            last_error = UpstreamUnavailable(f"network error — {url}: {error.reason}")
        except TimeoutError:
            last_error = UpstreamUnavailable(f"timeout — {url}")

        if attempt < retries:
            time.sleep(RETRY_BACKOFF_BASE * (2**attempt))

    assert last_error is not None
    raise last_error


def get_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15,
    retries: int = RETRY_ATTEMPTS,
) -> Any:
    raw = get_text(url, headers=headers, timeout=timeout, retries=retries)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise InvalidUpstreamResponse(f"invalid JSON from {url}") from error
