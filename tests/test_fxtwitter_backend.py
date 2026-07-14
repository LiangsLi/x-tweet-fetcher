"""FxTwitter API-version routing and compatibility tests."""
from __future__ import annotations

import pytest

from xtf.backends.fxtwitter import FxTwitterBackend
from xtf.exceptions import NotFound, UpstreamDown


def _tweet(**overrides):
    tweet = {
        "text": "hello",
        "author": {"name": "Alice", "screen_name": "alice"},
        "likes": 2,
        "reposts": 3,
        "replies": 4,
    }
    tweet.update(overrides)
    return tweet


def test_fetch_tweet_prefers_v2(monkeypatch):
    calls = []

    def fake_get_json(url, **_kwargs):
        calls.append(url)
        return {"code": 200, "status": _tweet()}

    monkeypatch.setattr("xtf.backends.fxtwitter.http.get_json", fake_get_json)

    result = FxTwitterBackend().fetch_tweet("alice", "123")

    assert calls == ["https://api.fxtwitter.com/2/status/123"]
    assert result["retweets"] == 3


def test_fetch_tweet_falls_back_to_legacy_on_v2_upstream_error(monkeypatch):
    calls = []

    def fake_get_json(url, **_kwargs):
        calls.append(url)
        if "/2/status/" in url:
            raise UpstreamDown("v2 unavailable")
        return {"code": 200, "tweet": _tweet(retweets=5)}

    monkeypatch.setattr("xtf.backends.fxtwitter.http.get_json", fake_get_json)

    result = FxTwitterBackend().fetch_tweet("alice", "123")

    assert calls == [
        "https://api.fxtwitter.com/2/status/123",
        "https://api.fxtwitter.com/alice/status/123",
    ]
    assert result["retweets"] == 5


def test_fetch_tweet_does_not_fallback_when_post_is_missing(monkeypatch):
    calls = []

    def fake_get_json(url, **_kwargs):
        calls.append(url)
        return {"code": 404, "message": "Not found"}

    monkeypatch.setattr("xtf.backends.fxtwitter.http.get_json", fake_get_json)

    with pytest.raises(NotFound):
        FxTwitterBackend().fetch_tweet("alice", "123")
    assert calls == ["https://api.fxtwitter.com/2/status/123"]
