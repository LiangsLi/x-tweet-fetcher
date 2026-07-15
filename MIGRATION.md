# Migrating from v3 to v4

v4 is an intentionally breaking scope reduction for document readers and AI agents that already
have a specific public X/Twitter URL.

## New API

Replace the v3 Router API:

```python
from xtf import Router
tweet = Router().fetch_tweet("user", "123")
```

with:

```python
from xtf import fetch
document = fetch("https://x.com/user/status/123")
```

The return type is `XDocument`; call `to_dict()` for the stable schema v1.0 JSON representation.

## New CLI

```bash
xtf https://x.com/user/status/123
```

`xtf --url URL` remains accepted, but all other v3 modes and flags have been removed.

## Removed in v4

- `Router`, backend classes, and the `Tweet`/`Reply`/`Profile` models
- search, timelines, replies, Lists, profiles, and mentions monitoring
- Nitter, Camofox, Playwright, and the legacy script shim
- `x.com/i/article/{article_id}` browser fetching

Consumers that need those capabilities should remain on v3 or the repository's general-purpose
`main` history. The `v1-legacy` tag still contains the older multi-platform scripts.

## JSON changes

v4 emits a reader-first document envelope with `schema_version`, `content_text`,
`content_markdown`, structured `media`, `quote`, and `metrics`. It is not field-compatible with the
v3 `tweet` envelope.
