"""Reader-focused public API and stable document schema tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from xtf import fetch, fetch_url
from xtf.exceptions import InvalidUrl, NotFound, UpstreamDown

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())["tweet"]


def test_fetch_normalizes_post_quote_and_media(monkeypatch):
    calls = []

    def fake_get_json(url, **_kwargs):
        calls.append(url)
        return {"code": 200, "status": _fixture("fxtwitter_tweet.json")}

    monkeypatch.setattr("xtf.client.http.get_json", fake_get_json)
    document = fetch("https://twitter.com/alice/status/123?s=20")
    payload = document.to_dict()

    assert calls == ["https://api.fxtwitter.com/2/status/123"]
    assert payload["schema_version"] == "1.0"
    assert payload["kind"] == "post"
    assert payload["canonical_url"] == "https://x.com/alice/status/123"
    assert payload["content_text"].startswith("Announcing v2")
    assert payload["media"][0]["role"] == "post"
    assert payload["media"][1]["type"] == "video"
    assert payload["quote"]["author"]["handle"] == "carol"
    assert payload["metrics"]["reposts"] == 45


def test_fetch_article_preserves_code_text_and_images(monkeypatch):
    monkeypatch.setattr(
        "xtf.client.http.get_json",
        lambda *_args, **_kwargs: {"code": 200, "status": _fixture("fxtwitter_article.json")},
    )

    document = fetch_url("https://x.com/writerjane/article/456#section")
    payload = document.to_dict()

    assert payload["kind"] == "article"
    assert payload["title"] == "Building Fetchers"
    assert payload["content_markdown"].startswith("![](https://pbs.twimg.com/media/COVER.jpg)")
    assert "```markdown" in payload["content_markdown"]
    assert "name: verify-frontend-change" in payload["content_markdown"]
    assert "name: verify-frontend-change" in payload["content_text"]
    assert "![](https://pbs.twimg.com/media/INLINE.jpg)" in payload["content_markdown"]
    assert [(item["role"], item["url"]) for item in payload["media"]] == [
        ("cover", "https://pbs.twimg.com/media/COVER.jpg"),
        ("inline", "https://pbs.twimg.com/media/INLINE.jpg"),
    ]


def test_fetch_falls_back_to_legacy(monkeypatch):
    calls = []

    def fake_get_json(url, **_kwargs):
        calls.append(url)
        if "/2/status/" in url:
            raise UpstreamDown("v2 failed")
        return {"code": 200, "tweet": _fixture("fxtwitter_tweet.json")}

    monkeypatch.setattr("xtf.client.http.get_json", fake_get_json)
    assert fetch("https://x.com/alice/status/123").post_id == "123"
    assert calls == [
        "https://api.fxtwitter.com/2/status/123",
        "https://api.fxtwitter.com/alice/status/123",
    ]


def test_fetch_does_not_fallback_on_not_found(monkeypatch):
    calls = []

    def fake_get_json(url, **_kwargs):
        calls.append(url)
        return {"code": 404, "message": "Not found"}

    monkeypatch.setattr("xtf.client.http.get_json", fake_get_json)
    with pytest.raises(NotFound):
        fetch("https://x.com/alice/status/404")
    assert calls == ["https://api.fxtwitter.com/2/status/404"]


@pytest.mark.parametrize(
    "url",
    ["https://example.com/a/status/1", "https://x.com/a", "not a url", ""],
)
def test_fetch_rejects_unsupported_urls(url):
    with pytest.raises(InvalidUrl):
        fetch(url)
