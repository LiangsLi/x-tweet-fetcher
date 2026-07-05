"""CLI compatibility tests: v1 flags accepted, JSON envelopes preserved."""
import json
import subprocess
import sys
from pathlib import Path


from xtf.cli import build_parser

ROOT = Path(__file__).parent.parent


def test_all_v1_flags_accepted():
    parser = build_parser()
    args = parser.parse_args([
        "--url", "https://x.com/a/status/1", "--pretty", "--text-only",
        "--timeout", "10", "--port", "9377",
        "--nitter", "nitter.example.com", "--backend", "nitter", "--lang", "en",
    ])
    assert args.url and args.pretty and args.text_only
    assert args.backend == "nitter"


def test_short_flags():
    parser = build_parser()
    args = parser.parse_args(["-u", "https://x.com/a/status/1", "-r", "-p", "-t"])
    assert args.url and args.replies and args.pretty and args.text_only


def test_mutually_exclusive_modes_exit_1():
    proc = subprocess.run(
        [sys.executable, "-m", "xtf.cli", "--url", "https://x.com/a/status/1",
         "--user", "alice"],
        capture_output=True, text=True,
        cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 1


def test_invalid_url_json_envelope():
    proc = subprocess.run(
        [sys.executable, "-m", "xtf.cli", "--url", "https://example.com/nope"],
        capture_output=True, text=True,
        cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert out["url"] == "https://example.com/nope"
    assert "error" in out                      # v1 field
    assert out["error_code"] == "invalid_input"  # v2 addition


def test_compat_shim_exists_and_parses():
    shim = ROOT / "scripts" / "fetch_tweet.py"
    assert shim.exists()
    proc = subprocess.run(
        [sys.executable, str(shim), "--url", "https://not-a-tweet"],
        capture_output=True, text=True,
        cwd=ROOT, env={"PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 1
    assert "error" in json.loads(proc.stdout)
