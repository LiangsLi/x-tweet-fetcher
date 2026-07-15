# Output schema and examples

## Contents

- [Envelope rules](#envelope-rules)
- [Successful document](#successful-document)
- [Author object](#author-object)
- [Media object](#media-object)
- [Metrics object](#metrics-object)
- [Quoted-post object](#quoted-post-object)
- [Article example](#article-example)
- [Post example](#post-example)
- [Error document](#error-document)
- [Error example](#error-example)
- [Consumer rules](#consumer-rules)

## Envelope rules

The `xtf` command writes exactly one UTF-8 JSON object to stdout. It does not wrap the object in a
list or Markdown fence. All successful and failed results use `schema_version: "1.0"`.

There are two mutually exclusive envelopes:

- A successful document contains `source`, `post_id`, `kind`, and the content fields. It has no
  top-level `error` field.
- An error document contains `source_url` and `error`. It does not contain partially reconstructed
  content.

Use the process exit code together with the envelope: `0` for success, `1` for a fetch failure, and
`2` for invalid CLI usage.

## Successful document

All top-level fields are always emitted. Optional values are represented as JSON `null`; they are not
omitted.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Always `"1.0"` for this contract. |
| `source` | string | Always `"x"`. |
| `source_url` | string | The URL supplied by the caller after surrounding whitespace is removed. Query strings and fragments remain here for provenance but do not affect the normalized identity. |
| `canonical_url` | string | Normalized `https://x.com/{handle}/status/{post_id}` URL. Article inputs also canonicalize to the public status route. |
| `post_id` | string | Decimal X Post ID represented as a string to avoid integer precision loss. |
| `kind` | `"post"` or `"article"` | Whether the returned Post contains an embedded X Article. This is determined from the payload, not merely from the input path. |
| `title` | string or null | Article title; normally `null` for a regular post. |
| `author` | object | Normalized display name and handle. See [Author object](#author-object). |
| `published_at` | string or null | Upstream publication timestamp. Treat it as an opaque timestamp string unless the consumer explicitly parses its format. |
| `post_text` | string | Text of the containing X post. For an Article, this is distinct from the Article body. |
| `content_text` | string | Plain searchable body. Article code text remains, while Markdown fences and image markup are removed. |
| `content_markdown` | string | Preferred reader body. Preserves Article structure, links, images, dividers, and fenced code. For a regular post, it is the post text. |
| `media` | array of Media | Deduplicated media belonging to the post or Article. Binary files are not downloaded. |
| `quote` | Quote or null | Normalized quoted-post context when available. |
| `metrics` | Metrics | Engagement counts for the containing post. Missing upstream counts normalize to zero. |
| `language` | string or null | Upstream language code when available, such as `"en"` or `"zh"`. |

## Author object

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Display name; may be empty when unavailable. |
| `handle` | string | Account handle without the leading `@`; may be empty when unavailable. |

## Media object

Every item in `media` and `quote.media` has the same fixed fields.

| Field | Type | Meaning |
| --- | --- | --- |
| `type` | string | Normalized media type. Common values are `"image"` and `"video"`; preserve unknown future values. |
| `role` | string | Where the media belongs: `"post"`, `"cover"`, `"inline"`, or `"quote"`. Preserve unknown future values. |
| `url` | string | Original or highest-level media URL selected by the upstream payload. |
| `width` | integer or null | Pixel width when available. |
| `height` | integer or null | Pixel height when available. |
| `thumbnail` | string or null | Video thumbnail URL when available. |
| `duration` | number or null | Video duration in seconds when available. |
| `variants` | array of objects | Video encodings supplied upstream. Typical keys include `url`, `bitrate`, and `content_type`. Images normally use an empty list. |

Media rules:

- Article cover and inline images can appear both as Markdown image links in `content_markdown` and as
  structured `media` entries.
- `url` is a remote reference, not a local file path.
- Consumers must not infer visual details that are absent from the text or metadata.
- Consumers should choose a video variant according to `content_type` and `bitrate` when they need to
  download or play media.

## Metrics object

| Field | Type | Meaning |
| --- | --- | --- |
| `likes` | integer | Like count. |
| `reposts` | integer | Repost/retweet count. |
| `replies` | integer | Reply count. |
| `bookmarks` | integer | Bookmark count. |
| `views` | integer | View count. |

Counts are non-negative normalized integers. A zero may mean either a real zero or that the upstream
payload did not provide the count.

## Quoted-post object

When `quote` is not `null`, it contains:

| Field | Type | Meaning |
| --- | --- | --- |
| `post_id` | string or null | Quoted Post ID when available. |
| `text` | string | Quoted Post text. |
| `author` | Author | Quoted Post author. |
| `published_at` | string or null | Quoted Post timestamp when available. |
| `media` | array of Media | Media with role `"quote"`. |
| `metrics` | Metrics | Engagement counts for the quoted Post. |

The quote object is context, not a recursively complete `XDocument`; it does not contain another
`quote`, `content_markdown`, or `canonical_url`.

## Article example

This representative example demonstrates an Article with a cover image, an inline image, and a
fenced code block. Real text, URLs, dimensions, dates, and counts vary.

```json
{
  "schema_version": "1.0",
  "source": "x",
  "source_url": "https://x.com/writerjane/article/456",
  "canonical_url": "https://x.com/writerjane/status/456",
  "post_id": "456",
  "kind": "article",
  "title": "Building Reliable Fetchers",
  "author": {
    "name": "Jane Writer",
    "handle": "writerjane"
  },
  "published_at": "Tue Jul 14 09:30:00 +0000 2026",
  "post_text": "A practical guide to reliable document fetching.",
  "content_text": "Building Reliable Fetchers\n\nInstall the package and preserve structured errors.\n\nfrom xtf import fetch\ndocument = fetch(url)",
  "content_markdown": "![](https://pbs.twimg.com/media/COVER.jpg)\n\n# Building Reliable Fetchers\n\nInstall the package and preserve structured errors.\n\n```python\nfrom xtf import fetch\ndocument = fetch(url)\n```\n\n![](https://pbs.twimg.com/media/INLINE.jpg)",
  "media": [
    {
      "type": "image",
      "role": "cover",
      "url": "https://pbs.twimg.com/media/COVER.jpg",
      "width": 1600,
      "height": 900,
      "thumbnail": null,
      "duration": null,
      "variants": []
    },
    {
      "type": "image",
      "role": "inline",
      "url": "https://pbs.twimg.com/media/INLINE.jpg",
      "width": 1200,
      "height": 800,
      "thumbnail": null,
      "duration": null,
      "variants": []
    }
  ],
  "quote": null,
  "metrics": {
    "likes": 120,
    "reposts": 24,
    "replies": 8,
    "bookmarks": 31,
    "views": 9500
  },
  "language": "en"
}
```

## Post example

This representative example demonstrates a regular post with image/video metadata and quoted-post
context.

```json
{
  "schema_version": "1.0",
  "source": "x",
  "source_url": "https://twitter.com/alice/status/123?s=20",
  "canonical_url": "https://x.com/alice/status/123",
  "post_id": "123",
  "kind": "post",
  "title": null,
  "author": {
    "name": "Alice Anderson",
    "handle": "alice"
  },
  "published_at": "Sat Jul 04 12:00:00 +0000 2026",
  "post_text": "Announcing the reader release.",
  "content_text": "Announcing the reader release.",
  "content_markdown": "Announcing the reader release.",
  "media": [
    {
      "type": "image",
      "role": "post",
      "url": "https://pbs.twimg.com/media/AAA111.jpg",
      "width": 1200,
      "height": 675,
      "thumbnail": null,
      "duration": null,
      "variants": []
    },
    {
      "type": "video",
      "role": "post",
      "url": "https://video.twimg.com/vid/1.mp4",
      "width": null,
      "height": null,
      "thumbnail": "https://pbs.twimg.com/thumb/1.jpg",
      "duration": 12.5,
      "variants": [
        {
          "url": "https://video.twimg.com/vid/1-hi.mp4",
          "bitrate": 832000,
          "content_type": "video/mp4"
        }
      ]
    }
  ],
  "quote": {
    "post_id": "122",
    "text": "The original announcement.",
    "author": {
      "name": "Carol Chen",
      "handle": "carol"
    },
    "published_at": null,
    "media": [],
    "metrics": {
      "likes": 10,
      "reposts": 2,
      "replies": 0,
      "bookmarks": 0,
      "views": 500
    }
  },
  "metrics": {
    "likes": 120,
    "reposts": 45,
    "replies": 33,
    "bookmarks": 12,
    "views": 9000
  },
  "language": "en"
}
```

## Error document

Every error envelope contains these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Always `"1.0"`. |
| `source_url` | string or null | Input URL when one was available; otherwise `null`. |
| `error.code` | string | Stable programmatic error code. |
| `error.message` | string | Diagnostic message intended for the caller. Do not branch on its wording. |
| `error.retryable` | boolean | Whether retrying later may succeed without changing the input. |

Stable error codes:

| Code | Retryable | Meaning |
| --- | --- | --- |
| `invalid_url` | no | URL or CLI invocation is unsupported or malformed. |
| `not_found` | no | The Post was not found or is unavailable through the public upstream. |
| `rate_limited` | yes | The upstream rejected the request because of rate limiting or access throttling. |
| `upstream_unavailable` | yes | The upstream service or network path is temporarily unavailable. |
| `invalid_upstream_response` | yes | The upstream returned malformed or incomplete data. |
| `unsupported_content` | no | A payload was received but did not contain readable supported content. |

## Error example

```json
{
  "schema_version": "1.0",
  "source_url": "https://x.com/alice/status/123",
  "error": {
    "code": "upstream_unavailable",
    "message": "FxTwitter v2 failed and the legacy endpoint was unavailable",
    "retryable": true
  }
}
```

## Consumer rules

1. Branch on `schema_version`, process exit code, and the presence of `error`; do not branch on field
   ordering or diagnostic message wording.
2. Preserve Post IDs as strings.
3. Preserve unknown media `type`, media `role`, and video-variant keys for forward compatibility.
4. Use `content_markdown` as the authoritative reader representation and `content_text` as the
   searchable fallback.
5. Do not merge `post_text` into an Article body unless the product explicitly wants an introductory
   caption.
6. Resolve relative product behavior from `canonical_url`, while retaining `source_url` for provenance.
7. Treat timestamps as upstream strings; normalize them only in an application-specific layer.
8. Treat metrics as snapshots that may change after fetching.
9. Do not interpret a zero metric as proof that the real count is zero.
10. Do not assume a media URL remains permanently available; cache or download it only when the user
    authorizes that additional action.
