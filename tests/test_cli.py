"""JSON-only CLI contract tests."""
from __future__ import annotations

import json

import pytest

from xtf.cli import build_parser, main
from xtf.exceptions import InvalidUrl, UpstreamUnavailable
from xtf.models import Author, XDocument


def _document(source_url: str) -> XDocument:
    return XDocument(
        source_url=source_url,
        canonical_url="https://x.com/alice/status/123",
        post_id="123",
        kind="post",
        title=None,
        author=Author(name="Alice", handle="alice"),
        published_at=None,
        post_text="hello",
        content_text="hello",
        content_markdown="hello",
    )


def test_parser_exposes_only_reader_options():
    parser = build_parser()
    args = parser.parse_args(["https://x.com/alice/status/123", "--pretty", "--timeout", "5"])
    assert args.url.endswith("/123")
    assert args.pretty is True
    assert args.timeout == 5


def test_cli_positional_url_outputs_json(monkeypatch, capsys):
    monkeypatch.setattr("xtf.cli.fetch", lambda url, **_kwargs: _document(url))
    main(["https://x.com/alice/status/123"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["kind"] == "post"
    assert payload["content_markdown"] == "hello"
    assert captured.err == ""


def test_cli_compatibility_url_and_pretty_output(monkeypatch, capsys):
    monkeypatch.setattr("xtf.cli.fetch", lambda url, **_kwargs: _document(url))
    main(["--url", "https://x.com/alice/status/123", "--pretty"])
    output = capsys.readouterr().out
    assert output.startswith("{\n  ")
    assert json.loads(output)["post_id"] == "123"


@pytest.mark.parametrize("argv", [[], ["a", "--url", "b"], ["a", "--timeout", "0"]])
def test_cli_usage_errors_are_json(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(argv)
    assert exit_info.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "invalid_url"
    assert payload["error"]["retryable"] is False


@pytest.mark.parametrize(
    "error,retryable",
    [(InvalidUrl("bad URL"), False), (UpstreamUnavailable("offline"), True)],
)
def test_cli_fetch_errors_are_structured(monkeypatch, capsys, error, retryable):
    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr("xtf.cli.fetch", fail)
    with pytest.raises(SystemExit) as exit_info:
        main(["https://x.com/alice/status/123"])
    assert exit_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == error.code
    assert payload["error"]["retryable"] is retryable
