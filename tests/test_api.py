"""HTTP smoke tests — the family contract surface."""
from pathlib import Path

from fastapi.testclient import TestClient

from diagram_analyser.api import app
from diagram_analyser.manifest import MANIFEST


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == MANIFEST["version"]


def test_manifest():
    r = client.get("/manifest")
    assert r.status_code == 200
    m = r.json()
    assert m["name"] == "diagram-analyser"
    assert m["auto_routable"] is True
    assert ".mmd" in m["extensions"]
    assert ".drawio" in m["extensions"]


def test_analyse_empty_returns_422():
    r = client.post("/analyse", files={"file": ("x.mmd", b"", "text/plain")})
    assert r.status_code == 422


def test_analyse_mermaid(tmp_path: Path):
    src = "flowchart TD\nA --> B\nB --> C\n"
    r = client.post("/analyse", files={"file": ("flow.mmd", src.encode(), "text/plain")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["file_format"] == "mermaid"
    assert body["graph"]["node_count"] == 3


def test_analyse_unsupported_returns_400():
    r = client.post("/analyse", files={"file": ("x.txt", b"hi", "text/plain")})
    assert r.status_code == 400
