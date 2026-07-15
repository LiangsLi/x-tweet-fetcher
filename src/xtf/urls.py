"""Parse supported public X/Twitter status and Article URLs."""
from __future__ import annotations

import re
from dataclasses import dataclass

_POST_URL_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?(?:x\.com|twitter\.com)/"
    r"([a-zA-Z0-9_]{1,15})/(status|article)/(\d+)(?:[/?#]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedPostUrl:
    source_url: str
    username: str
    post_id: str
    route: str

    @property
    def canonical_url(self) -> str:
        return f"https://x.com/{self.username}/status/{self.post_id}"


def parse_post_url(url: str) -> ParsedPostUrl:
    """Parse one public status/article URL; internal ``/i/article`` is unsupported."""
    raw = url.strip()
    match = _POST_URL_RE.search(raw)
    if not match or (match.group(1).lower() == "i" and match.group(2).lower() == "article"):
        raise ValueError(f"Cannot parse X post URL: {url}")
    return ParsedPostUrl(
        source_url=raw,
        username=match.group(1),
        route=match.group(2).lower(),
        post_id=match.group(3),
    )
