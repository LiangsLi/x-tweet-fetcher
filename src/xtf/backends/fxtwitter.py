"""FxTwitter backend — single tweets and user profiles, zero dependencies.

Output of ``fetch_tweet`` reproduces the v1 ``tweet`` dict byte-for-byte
(including the article full-text reconstruction from Draft.js blocks).
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List

from .. import http
from ..exceptions import NotFound, UpstreamDown, XtfError
from ..models import Profile
from ..parsers.article import reconstruct_article
from ..parsers.fxtwitter_json import extract_media
from .base import Backend

API = "https://api.fxtwitter.com"
API_V2 = f"{API}/2"


def _response_payload(data: Dict[str, Any], field: str, identifier: str) -> Dict[str, Any]:
    """Validate an FxTwitter envelope and return its post object."""
    code = data.get("code")
    if code == 404:
        raise NotFound(f"tweet {identifier} not found")
    if code != 200:
        raise UpstreamDown(
            f"FxTwitter returned code {code}: {data.get('message', 'Unknown')}"
        )
    payload = data.get(field)
    if not isinstance(payload, dict):
        raise UpstreamDown(f"FxTwitter response is missing the {field!r} object")
    return payload


def normalize_tweet_json(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """FxTwitter tweet object -> v1-compatible tweet dict. Pure."""
    tweet_data: Dict[str, Any] = {
        "text": tweet.get("text", ""),
        "author": tweet.get("author", {}).get("name", ""),
        "screen_name": tweet.get("author", {}).get("screen_name", ""),
        "likes": tweet.get("likes", 0),
        "retweets": tweet.get("retweets", tweet.get("reposts", 0)),
        "bookmarks": tweet.get("bookmarks", 0),
        "views": tweet.get("views", 0),
        "replies_count": tweet.get("replies", 0),
        "created_at": tweet.get("created_at", ""),
        "is_note_tweet": tweet.get("is_note_tweet", False),
        "lang": tweet.get("lang", ""),
    }

    media = extract_media(tweet)
    if media:
        tweet_data["media"] = media

    if tweet.get("quote"):
        qt = tweet["quote"]
        tweet_data["quote"] = {
            "text": qt.get("text", ""),
            "author": qt.get("author", {}).get("name", ""),
            "screen_name": qt.get("author", {}).get("screen_name", ""),
            "likes": qt.get("likes", 0),
            "retweets": qt.get("retweets", qt.get("reposts", 0)),
            "views": qt.get("views", 0),
        }
        quote_media = extract_media(qt)
        if quote_media:
            tweet_data["quote"]["media"] = quote_media

    article = tweet.get("article")
    if article:
        tweet_data["article"] = reconstruct_article(article)
        tweet_data["is_article"] = True
    else:
        tweet_data["is_article"] = False

    return tweet_data


class FxTwitterBackend(Backend):
    name = "fxtwitter"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def available(self) -> bool:
        return True  # public API; failures surface per-call

    def fetch_tweet(self, username: str, tweet_id: str) -> Dict[str, Any]:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            data = http.get_json(
                f"{API_V2}/status/{tweet_id}", headers=headers, timeout=self.timeout
            )
            tweet = _response_payload(data, "status", tweet_id)
        except UpstreamDown as v2_error:
            print(
                f"[fxtwitter] v2 failed ({v2_error}); trying legacy endpoint...",
                file=sys.stderr,
            )
            data = http.get_json(
                f"{API}/{username}/status/{tweet_id}",
                headers=headers,
                timeout=self.timeout,
            )
            tweet = _response_payload(data, "tweet", f"{username}/{tweet_id}")
        return normalize_tweet_json(tweet)

    def fetch_user_info(self, username: str) -> Profile:
        data = http.get_json(f"{API}/{username}", timeout=10)
        u = data.get("user", {})
        if not u:
            raise NotFound(f"user @{username} not found")
        return Profile(
            username=u.get("screen_name", username),
            display_name=u.get("name", ""),
            bio=u.get("description", ""),
            tweets_count=u.get("tweets", 0),
            followers=u.get("followers", 0),
            following=u.get("following", 0),
            joined=u.get("joined", ""),
        )

    def fetch_user_info_dict(self, username: str) -> Dict[str, Any]:
        """v1-compatible extended profile dict (includes avatar/banner/etc)."""
        data = http.get_json(f"{API}/{username}", timeout=10)
        u = data.get("user", {})
        if not u:
            raise NotFound(f"user @{username} not found")
        return {
            "username": u.get("screen_name", username),
            "display_name": u.get("name", ""),
            "bio": u.get("description", ""),
            "tweets_count": u.get("tweets", 0),
            "followers": u.get("followers", 0),
            "following": u.get("following", 0),
            "joined": u.get("joined", ""),
            "avatar": u.get("avatar_url", ""),
            "banner": u.get("banner_url", ""),
            "likes": u.get("likes", 0),
            "website": u.get("website", ""),
        }


def supplement_views(tweets: List[Dict], max_supplement: int = 50) -> List[Dict]:
    """Fill missing view counts via FxTwitter. Best-effort, never raises."""
    for tw in tweets[:max_supplement]:
        if tw.get("views", 0) != 0:
            continue
        author = tw.get("author", "")
        if not author or not author.startswith("@"):
            continue
        username = author.lstrip("@")
        tweet_id = tw.get("tweet_id") or tw.get("id")
        if not tweet_id:
            continue
        try:
            data = http.get_json(
                f"{API}/{username}/status/{tweet_id}", timeout=5, retries=0
            )
            views = data.get("tweet", {}).get("views", 0)
            if views:
                tw["views"] = views
                print(f"[views] {username}/{str(tweet_id)[:8]}... -> {views}", file=sys.stderr)
        except XtfError:
            pass
    return tweets
