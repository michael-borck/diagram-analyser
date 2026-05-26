"""Text-diagram parsers — each produces a (diagram_type, Graph) tuple from raw source.

These are pragmatic (regex + light state), not full grammars. They handle the shapes
typical of student diagrams; corner cases (deeply nested subgraphs, full UML notation)
parse approximately. The structural signals computed downstream from the resulting
Graph are the same regardless of which parser produced it.
"""
from .mermaid import parse_mermaid
from .plantuml import parse_plantuml
from .graphviz import parse_graphviz
from .drawio import parse_drawio

__all__ = ["parse_mermaid", "parse_plantuml", "parse_graphviz", "parse_drawio"]
