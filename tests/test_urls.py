"""Supported public X/Twitter URL parsing tests."""
from __future__ import annotations

import pytest

from xtf.urls import parse_post_url


@pytest.mark.parametrize(
    "url,username,post_id,route",
    [
        ("https://x.com/alice/status/12345", "alice", "12345", "status"),
        ("https://x.com/alice/article/12345", "alice", "12345", "article"),
        ("https://twitter.com/bob_1/status/999?s=20", "bob_1", "999", "status"),
        ("x.com/carol/status/42#photo", "carol", "42", "status"),
        (
            "www.x.com/ClaudeDevs/article/2074208949205881033/",
            "ClaudeDevs",
            "2074208949205881033",
            "article",
        ),
    ],
)
def test_parse_post_url(url, username, post_id, route):
    parsed = parse_post_url(url)
    assert (parsed.username, parsed.post_id, parsed.route) == (username, post_id, route)
    assert parsed.canonical_url == f"https://x.com/{username}/status/{post_id}"


@pytest.mark.parametrize(
    "bad",
    [
        "https://x.com/alice",
        "https://example.com/a/status/1",
        "https://notx.com/alice/status/1",
        "https://x.com/i/article/2011779830157557760",
        "not a url",
    ],
)
def test_parse_post_url_rejects_unsupported_urls(bad):
    with pytest.raises(ValueError):
        parse_post_url(bad)
