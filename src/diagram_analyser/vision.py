"""Image-diagram extraction via Anthropic Claude Vision.

Behind the `[vision]` extra. We send the image to Claude with a prompt asking
for JSON-shaped node/edge extraction, parse it, and produce a Graph + VisionInfo.

Failure modes (no API key, no anthropic package installed, LLM returned
unstructured text) surface as VisionInfo.error rather than raising — the
analyser still returns a valid (empty) DiagramAnalysis so callers can see what
went wrong.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from .schemas import Edge, Graph, Node, VisionInfo

# Keep the prompt deterministic — same shape every call simplifies parsing.
_PROMPT = """You are reading an image of a diagram (flowchart, UML, ER, architecture, sequence, state, or similar).

Extract the diagram's structure as STRICT JSON in exactly this shape — no prose, no markdown fences:

{
  "diagram_type": "flowchart" | "uml" | "er" | "sequence" | "state" | "architecture" | "mindmap" | "other",
  "nodes": [{"id": "n1", "label": "Start", "kind": "rect|decision|actor|class|entity|null"}],
  "edges": [{"source": "n1", "target": "n2", "kind": "directed|undirected", "label": null}]
}

If you cannot extract structure, return: {"diagram_type": "unknown", "nodes": [], "edges": []}.
Use the visible text labels as both id (slugified) and label. Be concise."""

_DEFAULT_MODEL = "claude-sonnet-4-5"


def vision_available() -> tuple[bool, str | None]:
    """(installed, reason_if_not) — does NOT check for API key here."""
    try:
        import anthropic  # noqa: F401

        return True, None
    except Exception as e:
        return False, f"anthropic SDK not installed (pip install 'diagram-analyser[vision]'): {e}"


def _media_type_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def extract_from_image(path: str | Path, *, model: str = _DEFAULT_MODEL) -> tuple[str, Graph, VisionInfo]:
    """Return (diagram_type, Graph, VisionInfo). Never raises — errors land in VisionInfo.error."""
    info = VisionInfo(provider="anthropic", model=model)

    installed, reason = vision_available()
    if not installed:
        info.error = reason
        return "unknown", Graph(), info

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        info.error = "ANTHROPIC_API_KEY environment variable is not set"
        return "unknown", Graph(), info

    image_path = Path(path)
    try:
        image_bytes = image_path.read_bytes()
    except Exception as e:
        info.error = f"could not read image: {e}"
        return "unknown", Graph(), info

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": _media_type_for(image_path),
                                "data": base64.standard_b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": _PROMPT},
                    ],
                }
            ],
        )
    except Exception as e:
        info.error = f"anthropic API call failed: {e}"
        return "unknown", Graph(), info

    raw_text = ""
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "text":
            raw_text = block.text
            break
    info.raw_description = raw_text

    diagram_type, graph = _parse_llm_json(raw_text, info)
    return diagram_type, graph, info


def _parse_llm_json(text: str, info: VisionInfo) -> tuple[str, Graph]:
    """Pull JSON out of the LLM response — tolerates accidental fences."""
    if not text:
        info.error = (info.error or "") + " empty model response"
        return "unknown", Graph()

    candidate = text.strip()
    # Strip ```json fences if the model added them despite the prompt.
    if candidate.startswith("```"):
        candidate = candidate.strip("`").lstrip("json").strip()
    # Greedy slice to the outermost {...}.
    first = candidate.find("{")
    last = candidate.rfind("}")
    if first == -1 or last == -1 or last <= first:
        info.error = (info.error or "") + " no JSON object in response"
        return "unknown", Graph()

    try:
        data = json.loads(candidate[first : last + 1])
    except json.JSONDecodeError as e:
        info.error = (info.error or "") + f" JSON parse failed: {e}"
        return "unknown", Graph()

    nodes = [
        Node(id=str(n.get("id", "")), label=str(n.get("label", "")), kind=n.get("kind") or None)
        for n in (data.get("nodes") or [])
        if n.get("id")
    ]
    edges = [
        Edge(
            source=str(e.get("source", "")),
            target=str(e.get("target", "")),
            kind=str(e.get("kind") or "directed"),
            label=e.get("label") or None,
        )
        for e in (data.get("edges") or [])
        if e.get("source") and e.get("target")
    ]
    info.extracted_structure = bool(nodes or edges)
    return data.get("diagram_type") or "unknown", Graph(
        nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges)
    )
