"""Capability manifest for the lens family (consumed by auto-analyser)."""
from __future__ import annotations

from lens_contract import make_manifest

# Auto-routable for the text-diagram extensions (nothing else claims these).
# Image extensions (.png/.jpg/...) are NOT listed: those auto-route to image-analyser,
# so the image-diagram path is explicit-only (CLI / API invocation by name, or the
# auto-analyser cascade when image-analyser flags is_diagram=True).
MANIFEST = make_manifest(
    name="diagram-analyser",
    accepts=["diagram", "graph", "uml", "flowchart"],
    extensions=[".mmd", ".mermaid", ".puml", ".plantuml", ".dot", ".gv", ".drawio"],
    auto_routable=True,
    produces="DiagramAnalysis",
)
