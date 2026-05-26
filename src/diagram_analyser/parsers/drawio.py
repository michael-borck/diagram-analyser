"""drawio XML parser — vertices + edges from mxCell elements.

drawio XML can be raw or compressed (mxfile.diagram contents zlib+base64 in some
exports). For v1 we handle the raw / uncompressed form (the default for diagrams
saved with 'Compressed: false' or for hand-authored exports). Compressed mxfile
returns an empty graph with a clear hint in the file_format / diagram_type.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from ..exceptions import DiagramAnalyserError
from ..schemas import Edge, Graph, Node


def parse_drawio(text: str) -> tuple[str, Graph]:
    """Return (diagram_type, Graph)."""
    text = (text or "").strip()
    if not text:
        return "drawio", Graph()

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise DiagramAnalyserError(f"drawio: not valid XML: {e}") from e

    # Find all <mxCell> elements (could be at any depth depending on diagram nesting).
    cells = list(root.iter("mxCell"))
    if not cells:
        # mxfile with compressed inner diagram payload? We don't decompress in v1.
        diagram_node = root.find(".//diagram")
        if diagram_node is not None and (diagram_node.text or "").strip():
            return "drawio-compressed", Graph()
        return "drawio", Graph()

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    for c in cells:
        cid = c.get("id") or ""
        if cid in ("0", "1"):
            # drawio root + default-parent placeholders; not real cells.
            continue
        if c.get("edge") == "1":
            source = c.get("source")
            target = c.get("target")
            value = (c.get("value") or "").strip() or None
            if source and target:
                edges.append(Edge(
                    source=source,
                    target=target,
                    kind="directed",
                    label=value,
                ))
            continue
        if c.get("vertex") == "1":
            label = (c.get("value") or "").strip()
            # Strip HTML — drawio labels are often <font>…</font>.
            label = _strip_html(label)
            style = c.get("style") or ""
            kind = _kind_from_style(style)
            nodes[cid] = Node(id=cid, label=label or cid, kind=kind)
            continue

    # Backfill any nodes that edges reference but we didn't capture (rare).
    for e in edges:
        for nid in (e.source, e.target):
            if nid not in nodes:
                nodes[nid] = Node(id=nid, label=nid)

    node_list = list(nodes.values())
    return "drawio", Graph(
        nodes=node_list,
        edges=edges,
        node_count=len(node_list),
        edge_count=len(edges),
    )


def _strip_html(text: str) -> str:
    """Best-effort HTML strip — drawio labels often wrap in <font> / <div>."""
    import re

    return re.sub(r"<[^>]+>", "", text or "").strip()


def _kind_from_style(style: str) -> str | None:
    """Tease a node 'kind' out of a drawio style string (e.g. 'shape=actor;...')."""
    if not style:
        return None
    for token in style.split(";"):
        token = token.strip()
        if token.startswith("shape="):
            return token.split("=", 1)[1] or None
        if token in ("ellipse", "rhombus", "rectangle", "cylinder", "actor", "umlActor"):
            return token
    if style.startswith("rounded=1"):
        return "rounded-rect"
    return None
