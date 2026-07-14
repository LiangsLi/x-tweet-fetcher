"""Unified data models.

Every backend normalizes its raw output into these dataclasses, so agent
callers see a single schema regardless of whether data came from FxTwitter,
Nitter HTML, or a browser snapshot.

``to_dict()`` intentionally reproduces the v1 JSON field names and
omission rules (optional fields absent rather than null) so existing
integrations keep working byte-for-byte.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Author:
    """Stable author shape exposed by the reader API."""

    name: str = ""
    handle: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "handle": self.handle.lstrip("@")}


@dataclass(frozen=True)
class Media:
    """A post or Article media item. URLs are retained, not downloaded."""

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
    """Reader-first representation of a public X post or embedded Article."""

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


def _drop_empty(d: Dict[str, Any], keys: tuple) -> Dict[str, Any]:
    for k in keys:
        if not d.get(k):
            d.pop(k, None)
    return d


@dataclass
class Tweet:
    """A tweet from any backend (timeline / list / search entry)."""

    author: str = ""            # "@handle"
    author_name: str = ""
    text: str = ""
    time_ago: str = ""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    tweet_id: str = ""
    media: List[str] = field(default_factory=list)
    retweeted_by: Optional[str] = None
    quoted_tweet: Optional["Tweet"] = None

    @classmethod
    def from_snapshot_entry(cls, d: Dict[str, Any]) -> "Tweet":
        qt = d.get("quoted_tweet")
        return cls(
            author=d.get("author", ""),
            author_name=d.get("author_name", d.get("author", "")),
            text=d.get("text", ""),
            time_ago=d.get("time_ago", ""),
            likes=d.get("likes", 0),
            retweets=d.get("retweets", 0),
            replies=d.get("replies", 0),
            views=d.get("views", 0),
            tweet_id=str(d.get("tweet_id", "") or ""),
            media=list(d.get("media", []) or []),
            retweeted_by=d.get("retweeted_by"),
            quoted_tweet=cls.from_snapshot_entry(qt) if qt else None,
        )

    @classmethod
    def from_nitter_entry(cls, d: Dict[str, Any]) -> "Tweet":
        """Normalize nitter_html parser output (username/display_name/time keys)."""
        user = d.get("username", "")
        return cls(
            author=f"@{user}" if user and not user.startswith("@") else user,
            author_name=d.get("display_name", user),
            text=d.get("text", ""),
            time_ago=d.get("time", ""),
            likes=d.get("likes", 0),
            retweets=d.get("retweets", 0),
            replies=d.get("replies", 0),
            views=d.get("views", 0),
            tweet_id=str(d.get("tweet_id", "") or ""),
            media=list(d.get("media_urls", []) or []),
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "author": self.author,
            "author_name": self.author_name,
            "text": self.text,
            "time_ago": self.time_ago,
            "likes": self.likes,
            "retweets": self.retweets,
            "replies": self.replies,
            "views": self.views,
            "tweet_id": self.tweet_id,
        }
        if self.media:
            d["media"] = self.media
        if self.retweeted_by:
            d["retweeted_by"] = self.retweeted_by
        if self.quoted_tweet:
            d["quoted_tweet"] = self.quoted_tweet.to_dict()
        return d


@dataclass
class Reply:
    """A reply under a tweet."""

    author: str = ""
    author_name: str = ""
    text: str = ""
    time_ago: str = ""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    tweet_id: str = ""
    media: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    thread_replies: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_snapshot_entry(cls, d: Dict[str, Any]) -> "Reply":
        return cls(
            author=d.get("author", ""),
            author_name=d.get("author_name", d.get("author", "")),
            text=d.get("text", ""),
            time_ago=d.get("time_ago", "") or "",
            likes=d.get("likes", 0),
            retweets=d.get("retweets", 0),
            replies=d.get("replies", 0),
            views=d.get("views", 0),
            tweet_id=str(d.get("tweet_id", "") or ""),
            media=list(d.get("media", []) or []),
            links=list(d.get("links", []) or []),
            thread_replies=list(d.get("thread_replies", []) or []),
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "author": self.author,
            "author_name": self.author_name,
            "text": self.text,
            "time_ago": self.time_ago,
            "likes": self.likes,
            "replies": self.replies,
            "views": self.views,
        }
        if self.retweets:
            d["retweets"] = self.retweets
        if self.tweet_id:
            d["tweet_id"] = self.tweet_id
        if self.media:
            d["media"] = self.media
        if self.links:
            d["links"] = self.links
        if self.thread_replies:
            d["thread_replies"] = self.thread_replies
        return d


@dataclass
class Profile:
    username: str = ""
    display_name: str = ""
    bio: str = ""
    tweets_count: int = 0
    following: int = 0
    followers: int = 0
    joined: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
            "tweets_count": self.tweets_count,
            "following": self.following,
            "followers": self.followers,
            "joined": self.joined,
        }


@dataclass
class Article:
    article_id: str = ""
    url: str = ""
    title: str = ""
    author: str = ""
    author_handle: str = ""
    content: str = ""
    paragraphs: List[str] = field(default_factory=list)
    word_count: int = 0
    char_count: int = 0
    is_partial: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "url": self.url,
            "title": self.title,
            "author": self.author,
            "author_handle": self.author_handle,
            "content": self.content,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "is_partial": self.is_partial,
            "paragraphs": self.paragraphs,
        }
