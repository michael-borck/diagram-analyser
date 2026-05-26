"""Graphviz / DOT parser — digraph and graph.

Handles:
  digraph Name { ... }   →  diagram_type = "digraph"
  graph Name { ... }      →  diagram_type = "graph" (undirected)
  A [label="Foo", shape=box];
  A -> B [label="x"];     (directed in digraph)
  A -- B;                 (undirected in graph)
"""
from __future__ import annotations

import re

from ..schemas import Edge, Graph, Node


_HEADER_RE = re.compile(r"""^\s*(?:strict\s+)?(?P<kind>digraph|graph)\b""", re.I)

# Node decl: id [attrs]   — id is bareword or quoted.
_NODE_DECL_RE = re.compile(
    r"""(?P<id>"[^"]+"|[A-Za-z_][\w.]*)\s*\[(?P<attrs>[^\]]*)\]""",
)

# Edge: A -> B [attrs?]   or   A -- B [attrs?]   — also chains A -> B -> C.
_EDGE_RE = re.compile(
    r"""(?P<src>"[^"]+"|[A-Za-z_][\w.]*)\s*(?P<conn>->|--)\s*(?P<tgt>"[^"]+"|[A-Za-z_][\w.]*)(?:\s*\[(?P<attrs>[^\]]*)\])?""",
)

_ATTR_RE = re.compile(r"""(\w+)\s*=\s*(?:"([^"]*)"|(\S+?))(?:[,\s]|$)""")


def _unquote(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def _parse_attrs(blob: str | None) -> dict[str, str]:
    if not blob:
        return {}
    out: dict[str, str] = {}
    for m in _ATTR_RE.finditer(blob + " "):
        key = m.group(1)
        val = m.group(2) if m.group(2) is not None else m.group(3)
        out[key] = (val or "").strip()
    return out


def _strip_comments(text: str) -> str:
    # Strip /* ... */ blocks and // line comments.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def parse_graphviz(text: str) -> tuple[str, Graph]:
    text = _strip_comments(text)

    diagram_type = "digraph"
    m = _HEADER_RE.search(text)
    if m:
        diagram_type = m.group("kind").lower()

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    # Node decls with attrs (so we capture labels).
    for nm in _NODE_DECL_RE.finditer(text):
        nid = _unquote(nm.group("id"))
        if nid.lower() in ("node", "edge", "graph"):  # Graphviz attr-defaults block
            continue
        attrs = _parse_attrs(nm.group("attrs"))
        nodes[nid] = Node(
            id=nid,
            label=attrs.get("label", nid),
            kind=attrs.get("shape"),
        )

    # Edges (and any nodes only seen via edges).
    for em in _EDGE_RE.finditer(text):
        src = _unquote(em.group("src"))
        tgt = _unquote(em.group("tgt"))
        attrs = _parse_attrs(em.group("attrs"))
        conn = em.group("conn")
        edges.append(Edge(
            source=src,
            target=tgt,
            kind="directed" if conn == "->" else "undirected",
            label=attrs.get("label"),
        ))
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
