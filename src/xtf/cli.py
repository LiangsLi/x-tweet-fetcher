"""JSON-only command line interface for fetching one public X URL."""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional, Sequence

from . import __version__, fetch
from .exceptions import RateLimited, UpstreamDown, XtfError
from .models import SCHEMA_VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xtf",
        description="Fetch one public X/Twitter post or Article as structured JSON.",
    )
    parser.add_argument("url", nargs="?", help="X/Twitter status or public Article URL")
    parser.add_argument("--url", "-u", dest="option_url", help="Compatibility URL option")
    parser.add_argument("--pretty", "-p", action="store_true", help="Indent JSON output")
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Upstream request timeout in seconds"
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _emit(payload: Dict[str, Any], pretty: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None))


def _error_payload(source_url: Optional[str], code: str, message: str, retryable: bool) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_url": source_url,
        "error": {"code": code, "message": message, "retryable": retryable},
    }


def _resolve_url(args: argparse.Namespace) -> tuple[Optional[str], Optional[dict]]:
    if args.url and args.option_url:
        return None, _error_payload(
            None, "invalid_url", "provide the URL either positionally or with --url, not both", False
        )
    url = args.url or args.option_url
    if not url:
        return None, _error_payload(None, "invalid_url", "an X/Twitter URL is required", False)
    if args.timeout <= 0:
        return None, _error_payload(url, "invalid_url", "--timeout must be greater than zero", False)
    return url, None


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    url, usage_error = _resolve_url(args)
    if usage_error:
        _emit(usage_error, args.pretty)
        raise SystemExit(2)

    assert url is not None
    try:
        payload = fetch(url, timeout=args.timeout).to_dict()
    except XtfError as error:
        retryable = isinstance(error, (RateLimited, UpstreamDown))
        payload = _error_payload(url, error.code, str(error) or error.code, retryable)
        _emit(payload, args.pretty)
        raise SystemExit(1)
    _emit(payload, args.pretty)


if __name__ == "__main__":
    main()
