---
name: x-tweet-fetcher
description: >
  Fetch one known public X/Twitter status or Article URL as stable structured JSON. Use this skill
  when an agent or reader needs the full text, rich Article Markdown, fenced code, images, videos,
  quotes, author, and metrics for a specific URL. It does not search X or fetch timelines/replies.
---

# X Tweet Fetcher

Use the installed CLI for a known public URL:

```bash
xtf https://x.com/user/status/123 --pretty
```

Public Article aliases are accepted:

```bash
xtf https://x.com/user/article/123 --pretty
```

The JSON fields most useful to a reader are:

- `kind`: `post` or `article`
- `title`: Article title or `null`
- `content_text`: searchable plain content
- `content_markdown`: rich content including fenced code and inline images
- `media`: structured image/video URLs and metadata
- `quote`: normalized quoted Post when present
- `error`: machine-readable failure details

Python callers can use:

```python
from xtf import fetch

document = fetch(url)
markdown = document.content_markdown
```

Do not use this package for search, timelines, replies, Lists, private posts, authenticated content,
or `x.com/i/article/{article_id}` URLs.
