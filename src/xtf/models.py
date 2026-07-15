"""Stable reader-first document models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Author:
    name: str = ""
    handle: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "handle": self.handle.lstrip("@")}


@dataclass(frozen=True)
class Media:
    type: str
    role: str
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail: Optional[str] = None
    duration: Optional[float] = None
    variants: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "role": self.role,
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "thumbnail": self.thumbnail,
            "duration": self.duration,
            "variants": list(self.variants),
        }


@dataclass(frozen=True)
class Metrics:
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    bookmarks: int = 0
    views: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "likes": self.likes,
            "reposts": self.reposts,
            "replies": self.replies,
            "bookmarks": self.bookmarks,
            "views": self.views,
        }


@dataclass(frozen=True)
class Quote:
    post_id: Optional[str]
    text: str
    author: Author
    published_at: Optional[str]
    media: List[Media] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "text": self.text,
            "author": self.author.to_dict(),
            "published_at": self.published_at,
            "media": [item.to_dict() for item in self.media],
            "metrics": self.metrics.to_dict(),
        }


@dataclass(frozen=True)
class XDocument:
    source_url: str
    canonical_url: str
    post_id: str
    kind: str
    title: Optional[str]
    author: Author
    published_at: Optional[str]
    post_text: str
    content_text: str
    content_markdown: str
    media: List[Media] = field(default_factory=list)
    quote: Optional[Quote] = None
    metrics: Metrics = field(default_factory=Metrics)
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "source": "x",
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "post_id": self.post_id,
            "kind": self.kind,
            "title": self.title,
            "author": self.author.to_dict(),
            "published_at": self.published_at,
            "post_text": self.post_text,
            "content_text": self.content_text,
            "content_markdown": self.content_markdown,
            "media": [item.to_dict() for item in self.media],
            "quote": self.quote.to_dict() if self.quote else None,
            "metrics": self.metrics.to_dict(),
            "language": self.language,
        }
