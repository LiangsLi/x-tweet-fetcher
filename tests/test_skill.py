"""Distribution checks for the bundled Agent Skill."""
from __future__ import annotations

import json
import re
from pathlib import Path

from xtf.models import SCHEMA_VERSION

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "fetch-x-post"


def test_skill_metadata_and_ui_prompt_are_complete():
    instructions = (SKILL / "SKILL.md").read_text()
    ui_metadata = (SKILL / "agents" / "openai.yaml").read_text()

    assert instructions.startswith("---\nname: fetch-x-post\ndescription:")
    assert "TODO" not in instructions
    assert "$fetch-x-post" in ui_metadata


def test_skill_json_examples_are_valid_and_cover_all_envelopes():
    reference = (SKILL / "references" / "output-schema.md").read_text()
    examples = [
        json.loads(block)
        for block in re.findall(r"```json\n(.*?)\n```", reference, flags=re.DOTALL)
    ]

    assert len(examples) == 3
    assert all(example["schema_version"] == SCHEMA_VERSION for example in examples)
    assert {example.get("kind") for example in examples if "error" not in example} == {
        "article",
        "post",
    }
    assert [example["error"]["code"] for example in examples if "error" in example] == [
        "upstream_unavailable"
    ]
