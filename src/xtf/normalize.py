"""Normalize FxTwitter post payloads into the stable reader document schema."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from .article import reconstruct_article
from .errors import UnsupportedContent
from .models import Author, Media, Metrics, Quote, XDocument
from .urls import ParsedPostUrl


def _integer(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _number(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _author(raw: Any) -> Author:
    raw = raw if isinstance(raw, Mapping) else {}
    return Author(name=str(raw.get("name") or ""), handle=str(raw.get("screen_name") or ""))


def _metrics(raw: Mapping[str, Any]) -> Metrics:
    return Metrics(
        likes=_integer(raw.get("likes")),
        reposts=_integer(raw.get("retweets", raw.get("reposts"))),
        replies=_integer(raw.get("replies")),
        bookmarks=_integer(raw.get("bookmarks")),
        views=_integer(raw.get("views")),
    )


def _dimensions(raw: Mapping[str, Any]) -> tuple[Optional[int], Optional[int]]:
    width = raw.get("width", raw.get("original_img_width"))
    height = raw.get("height", raw.get("original_img_height"))
    return (_integer(width) or None, _integer(height) or None)


def _post_media(raw: Mapping[str, Any], role: str) -> list[Media]:
    media = raw.get("media")
    media = media if isinstance(media, Mapping) else {}
    result: list[Media] = []
    all_media = media.get("all")
    if isinstance(all_media, list):
        for item in all_media:
            if not isinstance(item, Mapping):
                continue
            url = str(item.get("url") or "")
            if not url:
                continue
            kind = "image" if item.get("type") == "photo" else str(item.get("type") or "media")
            width, height = _dimensions(item)
            result.append(Media(type=kind, role=role, url=url, width=width, height=height))
    videos = media.get("videos")
    if isinstance(videos, list):
        for item in videos:
            if not isinstance(item, Mapping):
                continue
            url = str(item.get("url") or "")
            if not url:
                continue
            width, height = _dimensions(item)
            variants = [dict(v) for v in item.get("variants", []) if isinstance(v, Mapping)]
            result.append(
                Media(
                    type="video",
                    role=role,
                    url=url,
                    width=width,
                    height=height,
                    thumbnail=str(item.get("thumbnail_url") or "") or None,
                    duration=_number(item.get("duration")),
                    variants=variants,
                )
            )
    return result


def _article_media(raw: Mapping[str, Any]) -> list[Media]:
    result: list[Media] = []
    candidates = [(raw.get("cover_media"), "cover")]
    candidates.extend((item, "inline") for item in raw.get("media_entities", []) or [])
    for item, role in candidates:
        if not isinstance(item, Mapping):
            continue
        info = item.get("media_info")
        if not isinstance(info, Mapping):
            continue
        url = str(info.get("original_img_url") or "")
        if not url:
            continue
        width, height = _dimensions(info)
        result.append(Media(type="image", role=role, url=url, width=width, height=height))
    return result


def _dedupe_media(items: list[Media]) -> list[Media]:
    seen: set[tuple[str, str]] = set()
    result: list[Media] = []
    for item in items:
        key = (item.role, item.url)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _quote(raw: Any) -> Optional[Quote]:
    if not isinstance(raw, Mapping):
        return None
    post_id = raw.get("id", raw.get("tweet_id"))
    return Quote(
        post_id=str(post_id) if post_id is not None else None,
        text=str(raw.get("text") or ""),
        author=_author(raw.get("author")),
        published_at=str(raw.get("created_at")) if raw.get("created_at") else None,
        media=_dedupe_media(_post_media(raw, "quote")),
        metrics=_metrics(raw),
    )


def normalize_document(parsed: ParsedPostUrl, tweet: Mapping[str, Any]) -> XDocument:
    """Convert one validated FxTwitter post object into an ``XDocument``."""
    author = _author(tweet.get("author"))
    post_text = str(tweet.get("text") or "")
    article = tweet.get("article")
    if not post_text and not isinstance(article, Mapping) and not author.handle:
        raise UnsupportedContent("FxTwitter payload contains no readable post content")

    media = _post_media(tweet, "post")
    title: Optional[str] = None
    if isinstance(article, Mapping):
        rendered = reconstruct_article(article)
        title = str(rendered.get("title") or "") or None
        content_markdown = str(rendered.get("full_text") or "")
        content_text = str(rendered.get("plain_text") or "")
        media.extend(_article_media(article))
        cover = next((item.url for item in media if item.role == "cover"), None)
        if cover and cover not in content_markdown:
            content_markdown = f"![]({cover})\n\n{content_markdown}".rstrip()
        kind = "article"
    else:
        content_markdown = post_text
        content_text = post_text
        kind = "post"

    handle = author.handle or parsed.username
    canonical_url = f"https://x.com/{handle}/status/{parsed.post_id}"
    return XDocument(
        source_url=parsed.source_url,
        canonical_url=canonical_url,
        post_id=parsed.post_id,
        kind=kind,
        title=title,
        author=author,
        published_at=str(tweet.get("created_at")) if tweet.get("created_at") else None,
        post_text=post_text,
        content_text=content_text,
        content_markdown=content_markdown,
        media=_dedupe_media(media),
        quote=_quote(tweet.get("quote")),
        metrics=_metrics(tweet),
        language=str(tweet.get("lang")) if tweet.get("lang") else None,
    )
