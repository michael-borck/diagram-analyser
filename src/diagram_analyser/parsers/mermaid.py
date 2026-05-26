"""Mermaid parser — flowchart / class / ER / sequence / state.

Handles the shapes:
  graph TD / flowchart LR / classDiagram / erDiagram / sequenceDiagram / stateDiagram
  A[Label] / A(Label) / A{Decision} / A>Async] — shape hints captured as node 'kind'
  A --> B  /  A -->|edge label| B  /  A --- B  /  A -- text --- B  (edges)
"""
from __future__ import annotations

import re

from ..schemas import Edge, Graph, Node


# Header (first non-blank, non-comment line) — captures the diagram type.
_TYPE_RE = re.compile(
    r"""^\s*(graph|flowchart|classDiagram|erDiagram|sequenceDiagram|stateDiagram(?:-v2)?|gantt|pie|journey|mindmap|gitGraph)\b""",
    re.I,
)

# Node-shape patterns: A[label] / A(label) / A{decision} / A>async] / A((round)) / A[[subroutine]]
# Captured on demand when an id appears in an edge or stand-alone.
_NODE_DECL_RE = re.compile(
    r"""(?P<id>[A-Za-z_][\w.]*)(?P<shape>\[\[|\(\(|\[|\(|\{|>)(?P<label>[^\]\)\}>]*?)(?:\]\]|\)\)|\]|\)|\}|\])""",
)

# Edge connector — capture both ends + optional |label| or -- text --
# Forms: -->, -->|x|, ---, -- x ---, -.->, ==>, ==>|x|
_EDGE_RE = re.compile(
    r"""
    (?P<src>[A-Za-z_][\w.]*?)                                   # source id (non-greedy so trailing shape doesn't get glued)
    (?:\[[^\]]*\]|\([^)]*\)|\{[^}]*\}|>[^\]]*\])?               # optional shape on source
    \s*
    (?:
        (?P<arrow>-{2,3}>|={2,3}>|-\.->|-{3}|={3})              # connector
        \s*
        (?:\|\s*(?P<lbl1>[^|]*?)\s*\|)?                          # optional |label|
    |
        --\s*(?P<mid>[^->]+?)\s*-->                              # -- text -->
    |
        --\s*(?P<mid2>[^-]+?)\s*---                              # -- text ---
    )
    \s*
    (?:\[[^\]]*\]|\([^)]*\)|\{[^}]*\}|>[^\]]*\])?               # optional shape consumed before target
    (?P<tgt>[A-Za-z_][\w.]*)
    """,
    re.VERBOSE,
)


_SHAPE_KIND = {
    "[": "rect",
    "(": "round",
    "{": "decision",
    ">": "async",
    "[[": "subroutine",
    "((": "circle",
}


def _strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("%%") or stripped.startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def parse_mermaid(text: str) -> tuple[str, Graph]:
    """Return (diagram_type, Graph)."""
    text = _strip_comments(text)

    diagram_type = "graph"
    for line in text.splitlines():
        m = _TYPE_RE.match(line)
        if m:
            diagram_type = m.group(1).lower()
            break

    # Normalise — flowchart and graph are the same shape for our purposes.
    if diagram_type == "flowchart":
        diagram_type = "flowchart"

    # First pass: harvest node declarations with shapes / labels.
    nodes: dict[str, Node] = {}
    for m in _NODE_DECL_RE.finditer(text):
        nid = m.group("id")
        shape = m.group("shape")
        label = (m.group("label") or "").strip().strip('"').strip("'")
        kind = _SHAPE_KIND.get(shape)
        existing = nodes.get(nid)
        if existing is None or (not existing.label and label):
            nodes[nid] = Node(id=nid, label=label or nid, kind=kind)

    # Second pass: edges. We tolerate node-shape syntax embedded around ids.
    edges: list[Edge] = []
    for m in _EDGE_RE.finditer(text):
        src = m.group("src")
        tgt = m.group("tgt")
        if not src or not tgt:
            continue
        label = m.group("lbl1") or m.group("mid") or m.group("mid2")
        if label:
            label = label.strip()
        arrow = m.group("arrow") or ""
        kind = "undirected" if arrow.endswith("---") or arrow == "---" else "directed"
        edges.append(Edge(source=src, target=tgt, kind=kind, label=label or None))
        # Backfill any nodes mentioned only via edges.
        for nid in (src, tgt):
            if nid not in nodes:
                nodes[nid] = Node(id=nid, label=nid)

    node_list = list(nodes.values())
    return diagram_type, Graph(
        nodes=node_list,
        edges=edges,
        node_count=len(node_list),
        edge_count=len(edges),
    )
