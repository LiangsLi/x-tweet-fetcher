# x-tweet-fetcher

Fetch one public X/Twitter post or embedded Article and return a stable, reader-friendly JSON
document. The package is designed for document readers and AI agents that already have a specific
URL; it does not provide search, timelines, replies, or browser automation.

## Supported URLs

```text
https://x.com/{user}/status/{post_id}
https://twitter.com/{user}/status/{post_id}
https://x.com/{user}/article/{post_id}
https://twitter.com/{user}/article/{post_id}
```

Both public `status` and `article` routes use the same Post ID and produce equivalent content.
Internal `x.com/i/article/{article_id}` URLs are not supported.

## Install

```bash
pip install .
```

Install this branch directly from Git:

```bash
pip install "x-tweet-fetcher @ git+https://github.com/ythx-101/x-tweet-fetcher.git@codex/slim-url-reader"
```

For reproducible application builds, pin a commit rather than a moving branch name.

## Agent skill

The repository includes a distributable Codex-compatible Skill at
[`skills/fetch-x-post`](skills/fetch-x-post). It teaches an Agent to fetch one known public X post or
Article, validate the JSON envelope, preserve rich Markdown and code blocks, interpret media and
quoted-post metadata, and handle stable errors.

Clone this branch, install the `xtf` command, and copy the Skill into the user's Skill directory:

```bash
git clone --depth 1 --branch codex/slim-url-reader https://github.com/ythx-101/x-tweet-fetcher.git
cd x-tweet-fetcher
uv tool install .
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/fetch-x-post "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart or reload the Agent client after installation. Invoke it explicitly with `$fetch-x-post`, or
ask the Agent to read, summarize, analyze, or extract content from a specific `x.com`/`twitter.com`
status or Article URL.

## CLI

```bash
xtf https://x.com/ClaudeDevs/status/2074208949205881033
xtf https://x.com/ClaudeDevs/article/2074208949205881033 --pretty
```

The compatibility form remains available:

```bash
xtf --url https://x.com/user/status/123
```

Options:

```text
--pretty, -p     Indent JSON output
--timeout N      Upstream timeout in seconds (default: 30)
--version        Show the installed package version
```

stdout contains exactly one JSON object. Fetch failures exit with status `1`; usage errors exit
with status `2`. Error details remain machine-readable inside the JSON response.

## Python API

```python
from xtf import fetch

document = fetch("https://x.com/ClaudeDevs/status/2074208949205881033")

print(document.kind)              # "post" or "article"
print(document.title)
print(document.content_markdown)
payload = document.to_dict()
```

`fetch_url` is an alias of `fetch`.

## Document schema

Every successful result contains a `schema_version` and fixed top-level fields:

```json
{
  "schema_version": "1.0",
  "source": "x",
  "source_url": "https://x.com/user/status/123",
  "canonical_url": "https://x.com/user/status/123",
  "post_id": "123",
  "kind": "article",
  "title": "Article title",
  "author": {"name": "Display Name", "handle": "user"},
  "published_at": "...",
  "post_text": "Post text accompanying the Article",
  "content_text": "Plain searchable content",
  "content_markdown": "# Rich Markdown content",
  "media": [],
  "quote": null,
  "metrics": {
    "likes": 0,
    "reposts": 0,
    "replies": 0,
    "bookmarks": 0,
    "views": 0
  },
  "language": "en"
}
```

X Articles preserve headings, lists, links, emphasis, fenced code, dividers, cover images, inline
images, and embedded Post links. Images and videos are represented by their original URLs and
metadata; the package does not download binary media files.

Errors use the same versioned envelope and one of these stable codes:

```text
invalid_url
not_found
rate_limited
upstream_unavailable
invalid_upstream_response
unsupported_content
```

## Upstream behavior

The package uses the public FxTwitter API v2 and falls back to its legacy endpoint when v2 returns
a transient or malformed response. A definite 404 does not fall back. FxTwitter is an independent
third-party service with no availability SLA.

## Development

```bash
uv run pytest
uv run ruff check src tests
uv build
```

Tests use captured fixtures and mocked HTTP calls; CI does not depend on live X/FxTwitter access.

## License

[MIT](LICENSE)
