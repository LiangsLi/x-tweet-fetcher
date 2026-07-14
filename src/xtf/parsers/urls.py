"""URL / ID parsing helpers. Pure functions."""
from __future__ import annotations

import re
from typing import Optional


_POST_URL_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?(?:x\.com|twitter\.com)/"
    r"([a-zA-Z0-9_]{1,15})/(?:status|article)/(\d+)(?:[/?#]|$)",
    re.IGNORECASE,
)


def parse_tweet_url(url: str) -> tuple[str, str]:
    """Extract author and post ID from an X status or public Article URL."""
    match = _POST_URL_RE.search(url.strip())
    if match:
        return match.group(1), match.group(2)
    raise ValueError(f"Cannot parse tweet URL: {url}")
def extract_list_id(input_str: str) -> Optional[str]:
    """Extract list ID from a URL or raw ID string.

    Accepts:
      - Pure numeric ID:           "123456789"
      - List URL:                 "https://x.com/i/lists/123456789"
      - List URL (twitter.com):  "https://twitter.com/i/lists/123456789"
      - List URL (no scheme):    "x.com/i/lists/123456789"

    Returns the list ID string (digits only), or None if unparseable.
    """
    input_str = input_str.strip()

    # Pure numeric ID
    if re.match(r'^\d+$', input_str):
        return input_str

    # URL containing /i/lists/<id>
    m = re.search(r'/i/lists/(\d+)', input_str)
    if m:
        return m.group(1)

    return None


def parse_article_id(input_str: str) -> Optional[str]:
    """Extract article ID from a URL or raw ID string.

    Accepts:
      - Pure numeric ID:           "2011779830157557760"
      - Article URL:               "https://x.com/i/article/2011779830157557760"
      - Article URL (no scheme):   "x.com/i/article/2011779830157557760"
      - Tweet URL whose text links to an article (pass the ID directly in that case)

    Returns the article ID string, or None if unparseable.
    """
    input_str = input_str.strip()

    # Pure numeric ID
    if re.match(r'^\d{10,25}$', input_str):
        return input_str

    # URL containing /i/article/<id>
    m = re.search(r'/i/article/(\d{10,25})', input_str)
    if m:
        return m.group(1)

    return None

