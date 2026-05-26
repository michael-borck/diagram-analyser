"""PlantUML parser — UML / mindmap / wbs / activity / sequence (pragmatic).

Catches:
  @startuml / @startmindmap / @startwbs / @startsalt → diagram type
  class Foo / actor Bob / participant X / [Component] — node declarations
  A --> B  /  A -- B  /  A ..> B  /  A <|-- B (inheritance)  /  A o-- B (aggregation)
  : (alias-style notes)
"""
from __future__ import annotations

import re

from ..schemas import Edge, Graph, Node


_TYPE_RE = re.compile(
    r"""@start(?P<type>uml|mindmap|wbs|salt|json|yaml|gantt|activity)""",
    re.I,
)

# Node decls in UML style — kind from keyword.
_NODE_KEYWORD_RE = re.compile(
    r"""^\s*(?P<kind>class|interface|abstract|actor|participant|usecase|component|entity|object|node|database|enum|annotation|circle)\s+
        (?:"(?P<qname>[^"]+)"|(?P<name>[\w.]+))
        (?:\s+as\s+(?P<alias>[\w.]+))?""",
    re.VERBOSE | re.I,
)

# Bracket-style components: [Name]
_BRACKET_NODE_RE = re.compile(r"""\[(?P<label>[^\[\]]+?)\](?!\s*-{1,2}|\s*\.{1,2})""")

# Edge — A <connector> B with optional labels.
# Connectors: --> ..> <-- <.. -- .. <|-- --|> *-- --* o-- --o
_EDGE_RE = re.compile(
    r"""
    (?P<src>"[^"]+"|\[[^\[\]]+\]|\w+)
    \s*
    (?P<conn>(?:<\|--|--\|>|\*--|--\*|o--|--o|<--|-->|<\.\.|\.\.>|--|\.\.))
    \s*
    (?P<tgt>"[^"]+"|\[[^\[\]]+\]|\w+)
    (?:\s*:\s*(?P<label>[^\n]+))?
    """,
    re.VERBOSE,
)


_UNDIRECTED_CONNECTORS = {"--", ".."}


def _strip_comments(text: str) -> str:
    out = []
    in_block = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("/'"):
            in_block = True
        if in_block:
            if "'/" in s:
                in_block = False
            continue
        if s.startswith("'") or s.startswith("//"):
            continue
        out.append(line)
    return "\n".join(out)


def _unquote(token: str) -> str:
    """[Foo] → Foo;  "Foo Bar" → Foo Bar;  Foo → Foo."""
    t = token.strip()
    if t.startswith('"') and t.endswith('"'):
        return t[1:-1]
    if t.startswith("[") and t.endswith("]"):
        return t[1:-1]
    return t


def parse_plantuml(text: str) -> tuple[str, Graph]:
    text = _strip_comments(text)

    diagram_type = "uml"
    m = _TYPE_RE.search(text)
    if m:
        diagram_type = m.group("type").lower()

    nodes: dict[str, Node] = {}

    for line in text.splitlines():
        m = _NODE_KEYWORD_RE.match(line)
        if m:
            name = m.group("qname") or m.group("name")
            alias = m.group("alias") or name
            kind = m.group("kind").lower()
            nodes[alias] = Node(id=alias, label=name, kind=kind)

    # Bracket-style components: nodes inside [...] when not a connector body.
    for bm in _BRACKET_NODE_RE.finditer(text):
        label = bm.group("label").strip()
        if label not in nodes:
            nodes[label] = Node(id=label, label=label, kind="component")

    edges: list[Edge] = []
    for em in _EDGE_RE.finditer(text):
        src = _unquote(em.group("src"))
        tgt = _unquote(em.group("tgt"))
        conn = em.group("conn")
        label = (em.group("label") or "").strip() or None
        # UML inheritance kind hint.
        edge_kind = "directed"
        rel_label = label
        if conn in _UNDIRECTED_CONNECTORS:
            edge_kind = "undirected"
        if conn == "<|--":
            rel_label = (rel_label + " " if rel_label else "") + "(extends)"
            src, tgt = tgt, src  # arrow points TO the parent; normalise child → parent
        elif conn == "--|>":
            rel_label = (rel_label + " " if rel_label else "") + "(extends)"
        elif conn in ("*--", "--*"):
            rel_label = (rel_label + " " if rel_label else "") + "(composition)"
        elif conn in ("o--", "--o"):
            rel_label = (rel_label + " " if rel_label else "") + "(aggregation)"
        elif conn in ("<--", "<.."):
            src, tgt = tgt, src

        edges.append(Edge(source=src, target=tgt, kind=edge_kind, label=rel_label))

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
