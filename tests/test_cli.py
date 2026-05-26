"""CLI smoke tests."""
import json
import subprocess
import sys
from pathlib import Path


def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "diagram_analyser.cli", *map(str, args)],
        capture_output=True,
        text=True,
    )


def test_missing_file_nonzero(tmp_path: Path):
    r = _run(tmp_path / "nope.mmd")
    assert r.returncode != 0


def test_human_summary(tmp_path: Path):
    f = tmp_path / "x.mmd"
    f.write_text("flowchart TD\nA --> B\nB --> C\n")
    r = _run(f)
    assert r.returncode == 0, r.stderr
    assert "Format:" in r.stdout
    assert "Graph:" in r.stdout
    assert "nodes" in r.stdout


def test_json_output(tmp_path: Path):
    f = tmp_path / "x.mmd"
    f.write_text("flowchart TD\nA --> B\n")
    r = _run(f, "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["file_format"] == "mermaid"
    assert data["graph"]["node_count"] == 2


def test_manifest_subcommand():
    r = _run("manifest")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["name"] == "diagram-analyser"
