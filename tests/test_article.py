"""X Article Draft.js rendering regression tests."""
from __future__ import annotations

import json
from pathlib import Path

from xtf.article import reconstruct_article, render_article_content

FIXTURES = Path(__file__).parent / "fixtures"


def _article() -> dict:
    payload = json.loads((FIXTURES / "fxtwitter_article.json").read_text())
    return payload["tweet"]["article"]


def test_article_preserves_content_order_and_images():
    rendered = reconstruct_article(_article())["full_text"]
    assert rendered.index("First paragraph") < rendered.index("INLINE.jpg")
    assert rendered.index("INLINE.jpg") < rendered.index("Second paragraph")


def test_article_preserves_code_links_and_rich_blocks():
    rendered = reconstruct_article(_article())["full_text"]
    assert "```markdown" in rendered
    assert "name: verify-frontend-change" in rendered
    assert "## Verification" in rendered
    assert "Read the [guide](https://example.com/guide)" in rendered
    assert "\n\n---\n\n" in rendered
    assert "- **Important:** keep the code block" in rendered


def test_article_plain_text_retains_code_without_fence():
    plain = reconstruct_article(_article())["plain_text"]
    assert "name: verify-frontend-change" in plain
    assert "```markdown" not in plain
    assert "INLINE.jpg" not in plain


def test_inline_style_excludes_trailing_whitespace():
    rendered = render_article_content(
        {
            "content": {
                "blocks": [
                    {
                        "type": "unstyled",
                        "text": "Written by @alice ",
                        "inlineStyleRanges": [
                            {"offset": 0, "length": 11, "style": "Italic"}
                        ],
                    }
                ],
                "entityMap": {},
            }
        }
    )
    assert rendered == "_Written by_ @alice"
