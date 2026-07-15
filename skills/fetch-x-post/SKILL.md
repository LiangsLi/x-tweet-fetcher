---
name: fetch-x-post
description: Fetch one public x.com or twitter.com status or Article URL with the x-tweet-fetcher CLI and return stable reader-friendly JSON containing complete text, rich Markdown, fenced code blocks, media metadata, quoted-post context, metrics, and machine-readable errors. Use when Codex needs to read, summarize, analyze, cite, or extract content from a specific X/Twitter post or Article URL. Do not use for search, timelines, replies, account monitoring, private posts, or arbitrary web pages.
---

# Fetch X Post

Fetch exactly one public X/Twitter post or embedded Article through the `xtf` command. Treat the
versioned JSON document as the source of truth and preserve its rich content when answering.

## Check the prerequisite

Check whether the command is available before fetching:

```bash
command -v xtf
xtf --version
```

If `xtf` is unavailable, install the package only when package installation is in scope:

```bash
uv tool install "x-tweet-fetcher @ git+https://github.com/ythx-101/x-tweet-fetcher.git@codex/slim-url-reader"
```

Alternatively, install it into the active Python environment:

```bash
python -m pip install "x-tweet-fetcher @ git+https://github.com/ythx-101/x-tweet-fetcher.git@codex/slim-url-reader"
```

If installation is not authorized, report that `xtf` is missing and provide the appropriate command
instead of substituting an unrelated scraper.

## Accept only supported URLs

Accept these public URL forms:

```text
https://x.com/{user}/status/{post_id}
https://twitter.com/{user}/status/{post_id}
https://x.com/{user}/article/{post_id}
https://twitter.com/{user}/article/{post_id}
```

Treat public `status` and `article` routes with the same Post ID as equivalent inputs. Preserve the
user-provided URL as `source_url`; use `canonical_url` for the normalized X URL.

Reject unsupported inputs such as profiles, searches, timelines, private posts, arbitrary web pages,
and internal `x.com/i/article/{article_id}` URLs.

## Fetch the document

Run the command with the URL as one quoted argument:

```bash
xtf "https://x.com/user/status/123" --pretty --timeout 30
```

The compatibility form is also valid:

```bash
xtf --url "https://x.com/user/article/123" --pretty
```

Capture stdout and the process exit code. Parse stdout as exactly one JSON object. Do not scrape
terminal formatting or infer success from human-readable text.

Interpret exit codes as follows:

- `0`: successful document; no top-level `error` field.
- `1`: fetch or upstream failure; inspect `error.code` and `error.retryable`.
- `2`: invalid invocation or URL; correct the input instead of retrying unchanged.

## Read the result

On success:

1. Require `schema_version` to equal `"1.0"` before relying on the documented field meanings.
2. Use `kind` to distinguish a normal `post` from an embedded `article`.
3. Prefer `content_markdown` for reading, summarizing, quoting structure, or passing content to another
   Agent. It preserves headings, lists, links, emphasis, dividers, images, and fenced code blocks.
4. Use `content_text` for indexing or plain-text search. It retains code text but removes Markdown
   syntax and image markup.
5. Keep `post_text` separate from Article content. For an Article, it is the accompanying X post text,
   not the Article body.
6. Inspect `media` for original image/video URLs and metadata. Do not claim to have visually inspected
   an image merely because its URL is present.
7. Inspect `quote` for a quoted post. A `null` value means no quoted-post context was returned.
8. Preserve code fences and their language labels when reproducing code from an Article.

On failure:

1. Read the stable `error.code`, `error.message`, and `error.retryable` fields.
2. Retry only when `retryable` is `true`, and avoid repeated immediate retries. Prefer one delayed retry
   unless the user explicitly requests persistent monitoring.
3. Never replace an error with invented post content or a guessed summary.

Read [references/output-schema.md](references/output-schema.md) before building an integration,
validating a payload, explaining individual fields, or returning a full example. It contains the
complete success and error structures, field semantics, media rules, and representative payloads.

## Return the requested form

- When the user asks to fetch, download, or return structured data, return the successful JSON object
  without renaming or dropping fields.
- When the user asks to read, summarize, translate, or analyze, base the answer on
  `content_markdown`, retain important code and media references, and include `canonical_url` as the
  source link.
- When the user requests the original text, do not silently summarize it. Distinguish `post_text` from
  the Article body.
- When downstream code needs machine-readable input, pass through the JSON rather than converting it
  into an ad hoc schema.

## Respect limitations

- Fetch only one known public URL per command.
- Do not search X, enumerate a user's timeline, retrieve reply threads, or monitor accounts.
- Do not expect authentication to reveal private or age-restricted content.
- Do not expect binary media downloads; `media` contains URLs and metadata only.
- Treat FxTwitter as an independent upstream service without an availability SLA.
