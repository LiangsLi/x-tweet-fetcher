"""Bounded HTTP and retry behavior tests."""
from __future__ import annotations

import urllib.error

import pytest

from xtf import http
from xtf.errors import InvalidUpstreamResponse, NotFound, UpstreamUnavailable


class _Response:
    def __init__(self, body: bytes, headers=None):
        self.body = body
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


def test_get_text_retries_network_errors(monkeypatch):
    calls = []

    def fail(*_args, **_kwargs):
        calls.append(1)
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(http.urllib.request, "urlopen", fail)
    monkeypatch.setattr(http.time, "sleep", lambda _seconds: None)
    with pytest.raises(UpstreamUnavailable):
        http.get_text("https://example.test", retries=2)
    assert len(calls) == 3


def test_get_text_does_not_retry_404(monkeypatch):
    calls = []

    def fail(*_args, **_kwargs):
        calls.append(1)
        raise urllib.error.HTTPError("u", 404, "not found", {}, None)

    monkeypatch.setattr(http.urllib.request, "urlopen", fail)
    with pytest.raises(NotFound):
        http.get_text("https://example.test", retries=3)
    assert len(calls) == 1


def test_get_text_rejects_oversized_response(monkeypatch):
    monkeypatch.setattr(http, "MAX_BODY", 4)
    monkeypatch.setattr(
        http.urllib.request, "urlopen", lambda *_args, **_kwargs: _Response(b"12345")
    )
    with pytest.raises(InvalidUpstreamResponse):
        http.get_text("https://example.test", retries=0)


def test_get_json_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(http, "get_text", lambda *_args, **_kwargs: "not json")
    with pytest.raises(InvalidUpstreamResponse):
        http.get_json("https://example.test")
