"""Render the Draft.js payload used by X Articles as readable Markdown."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


_BLOCK_PREFIXES = {
    "header-one": "# ",
    "header-two": "## ",
    "header-three": "### ",
    "header-four": "#### ",
    "header-five": "##### ",
    "header-six": "###### ",
    "blockquote": "> ",
    "unordered-list-item": "- ",
}

_STYLE_MARKERS = {
    "Bold": ("**", "**"),
    "Italic": ("_", "_"),
    "Strikethrough": ("~~", "~~"),
    "Monospace": ("`", "`"),
    "CODE": ("`", "`"),
}


def _normalize_entity_map(raw: Any) -> dict[str, dict[str, Any]]:
    """Accept both Draft.js entity-map encodings returned by FxTwitter."""
    entities: dict[str, dict[str, Any]] = {}
    if isinstance(raw, Mapping):
        items: Iterable[tuple[Any, Any]] = raw.items()
    elif isinstance(raw, list):
        items = ((entry.get("key"), entry.get("value")) for entry in raw if isinstance(entry, Mapping))
    else:
        return entities

    for key, value in items:
        if key is not None and isinstance(value, Mapping):
            entities[str(key)] = dict(value)
    return entities


def _safe_http_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    if not value.startswith(("https://", "http://")):
        return ""
    if any(char in value for char in (")", "\n", "\r")):
        return ""
    return value


def _media_urls(article: Mapping[str, Any]) -> dict[str, str]:
    media_id_to_url: dict[str, str] = {}
    media_objects = [article.get("cover_media"), *(article.get("media_entities") or [])]
    for media in media_objects:
        if not isinstance(media, Mapping):
            continue
        media_id = media.get("media_id") or media.get("id")
        info = media.get("media_info")
        if media_id is None or not isinstance(info, Mapping):
            continue
        url = _safe_http_url(info.get("original_img_url"))
        if url:
            media_id_to_url[str(media_id)] = url
    return media_id_to_url


def _entity_wrappers(
    text: str,
    ranges: Any,
    entities: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int, int, str, str]]:
    wrappers: list[tuple[int, int, int, str, str]] = []
    if not isinstance(ranges, list):
        return wrappers
    for item in ranges:
        if not isinstance(item, Mapping):
            continue
        entity = entities.get(str(item.get("key")))
        if not entity or entity.get("type") != "LINK":
            continue
        data = entity.get("data")
        url = _safe_http_url(data.get("url") if isinstance(data, Mapping) else None)
        start = item.get("offset")
        length = item.get("length")
        if url and isinstance(start, int) and isinstance(length, int) and 0 <= start < len(text):
            end = min(len(text), start + max(length, 0))
            if end > start:
                wrappers.append((start, end, 0, "[", f"]({url})"))
    return wrappers


def _style_wrappers(text: str, ranges: Any) -> list[tuple[int, int, int, str, str]]:
    wrappers: list[tuple[int, int, int, str, str]] = []
    if not isinstance(ranges, list):
        return wrappers
    for item in ranges:
        if not isinstance(item, Mapping):
            continue
        marker = _STYLE_MARKERS.get(str(item.get("style")))
        start = item.get("offset")
        length = item.get("length")
        if marker and isinstance(start, int) and isinstance(length, int) and 0 <= start < len(text):
            end = min(len(text), start + max(length, 0))
            # Markdown emphasis delimiters cannot sit next to whitespace.
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if end > start:
                wrappers.append((start, end, 1, marker[0], marker[1]))
    return wrappers


def _render_inline(
    text: str,
    block: Mapping[str, Any],
    entities: Mapping[str, Mapping[str, Any]],
) -> str:
    """Apply non-destructive Markdown wrappers around Draft.js text ranges."""
    wrappers = _entity_wrappers(text, block.get("entityRanges"), entities)
    wrappers.extend(_style_wrappers(text, block.get("inlineStyleRanges")))
    if not wrappers:
        return text

    openings: dict[int, list[tuple[int, int, str]]] = {}
    closings: dict[int, list[tuple[int, int, str]]] = {}
    for start, end, priority, opening, closing in wrappers:
        openings.setdefault(start, []).append((end, priority, opening))
        closings.setdefault(end, []).append((start, priority, closing))

    out: list[str] = []
    for index in range(len(text) + 1):
        # Inner ranges close before outer ranges; outer ranges open first.
        for _start, _priority, marker in sorted(
            closings.get(index, []), key=lambda item: (item[0], item[1]), reverse=True
        ):
            out.append(marker)
        for _end, _priority, marker in sorted(
            openings.get(index, []), key=lambda item: (-item[0], item[1])
        ):
            out.append(marker)
        if index < len(text):
            out.append(text[index])
    return "".join(out)


def _first_block_entity(
    block: Mapping[str, Any], entities: Mapping[str, Mapping[str, Any]]
) -> Mapping[str, Any] | None:
    ranges = block.get("entityRanges")
    if not isinstance(ranges, list):
        return None
    for item in ranges:
        if isinstance(item, Mapping):
            entity = entities.get(str(item.get("key")))
            if entity:
                return entity
    return None


def _render_atomic(
    block: Mapping[str, Any],
    entities: Mapping[str, Mapping[str, Any]],
    media_id_to_url: Mapping[str, str],
) -> str:
    entity = _first_block_entity(block, entities)
    if not entity:
        return str(block.get("text") or "").strip()

    entity_type = entity.get("type")
    data = entity.get("data")
    data = data if isinstance(data, Mapping) else {}
    if entity_type == "MARKDOWN":
        return str(data.get("markdown") or "").strip()
    if entity_type == "DIVIDER":
        return "---"
    if entity_type == "MEDIA":
        media_items = data.get("mediaItems")
        if isinstance(media_items, list):
            for item in media_items:
                if not isinstance(item, Mapping):
                    continue
                url = media_id_to_url.get(str(item.get("mediaId")))
                if url:
                    return f"![]({url})"
        return ""
    if entity_type == "TWEET" and data.get("tweetId"):
        return f"https://x.com/i/status/{data['tweetId']}"
    return str(block.get("text") or "").strip()


def render_article_content(article: Mapping[str, Any]) -> str:
    """Render all supported X Article blocks in their original order."""
    content = article.get("content")
    if not isinstance(content, Mapping):
        return ""
    blocks = content.get("blocks")
    if not isinstance(blocks, list):
        return ""

    entities = _normalize_entity_map(content.get("entityMap"))
    media_id_to_url = _media_urls(article)
    rendered: list[str] = []
    ordered_number = 0
    previous_type = ""

    for block in blocks:
        if not isinstance(block, Mapping):
            continue
        block_type = str(block.get("type") or "unstyled")
        if block_type == "atomic":
            value = _render_atomic(block, entities, media_id_to_url)
        else:
            text = str(block.get("text") or "")
            value = _render_inline(text, block, entities)
            depth = block.get("depth") if isinstance(block.get("depth"), int) else 0
            indent = "  " * max(depth, 0)
            if block_type == "ordered-list-item":
                ordered_number = ordered_number + 1 if previous_type == block_type else 1
                value = f"{indent}{ordered_number}. {value}"
            else:
                ordered_number = 0
                prefix = _BLOCK_PREFIXES.get(block_type, "")
                value = f"{indent}{prefix}{value}" if prefix else value
        if value.strip():
            rendered.append(value.rstrip())
        previous_type = block_type
    return "\n\n".join(rendered)


def render_article_text(article: Mapping[str, Any]) -> str:
    """Render searchable plain text while retaining code and embedded-post URLs."""
    content = article.get("content")
    if not isinstance(content, Mapping):
        return ""
    blocks = content.get("blocks")
    if not isinstance(blocks, list):
        return ""
    entities = _normalize_entity_map(content.get("entityMap"))
    rendered: list[str] = []
    for block in blocks:
        if not isinstance(block, Mapping):
            continue
        if block.get("type") != "atomic":
            value = str(block.get("text") or "").strip()
        else:
            entity = _first_block_entity(block, entities)
            if not entity:
                value = str(block.get("text") or "").strip()
            else:
                data = entity.get("data")
                data = data if isinstance(data, Mapping) else {}
                entity_type = entity.get("type")
                if entity_type == "MARKDOWN":
                    markdown = str(data.get("markdown") or "").strip()
                    lines = markdown.splitlines()
                    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1] == "```":
                        lines = lines[1:-1]
                    value = "\n".join(lines).strip()
                elif entity_type == "TWEET" and data.get("tweetId"):
                    value = f"https://x.com/i/status/{data['tweetId']}"
                else:
                    value = ""
        if value:
            rendered.append(value)
    return "\n\n".join(rendered)


def reconstruct_article(article: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an FxTwitter Article object and retain its complete content."""
    article_data: dict[str, Any] = {
        "title": article.get("title", ""),
        "preview_text": article.get("preview_text", ""),
        "created_at": article.get("created_at", ""),
    }
    full_text = render_article_content(article)
    plain_text = render_article_text(article)
    if full_text:
        article_data.update(
            full_text=full_text,
            plain_text=plain_text,
            word_count=len(full_text.split()),
            char_count=len(full_text),
        )

    images: list[dict[str, str]] = []
    cover = article.get("cover_media")
    if isinstance(cover, Mapping):
        info = cover.get("media_info")
        url = _safe_http_url(info.get("original_img_url") if isinstance(info, Mapping) else None)
        if url:
            images.append({"type": "cover", "url": url})
    for media in article.get("media_entities") or []:
        if not isinstance(media, Mapping):
            continue
        info = media.get("media_info")
        url = _safe_http_url(info.get("original_img_url") if isinstance(info, Mapping) else None)
        if url:
            images.append({"type": "image", "url": url})
    if images:
        article_data["images"] = images
        article_data["image_count"] = len(images)
    return article_data
