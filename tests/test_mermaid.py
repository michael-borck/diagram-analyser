"""Unit tests for the mermaid parser."""
from diagram_analyser.parsers import parse_mermaid


def test_flowchart_basic():
    src = """
    flowchart TD
      A[Start] --> B{Decision}
      B -->|yes| C[Do]
      B -->|no| D[Skip]
    """
    dtype, g = parse_mermaid(src)
    assert dtype == "flowchart"
    ids = {n.id for n in g.nodes}
    assert ids == {"A", "B", "C", "D"}
    by_id = {n.id: n for n in g.nodes}
    assert by_id["B"].kind == "decision"
    assert by_id["A"].label == "Start"
    assert by_id["A"].kind == "rect"
    # 3 edges, two with labels
    assert g.edge_count == 3
    labels = {e.label for e in g.edges}
    assert "yes" in labels and "no" in labels


def test_graph_type_alias():
    dtype, g = parse_mermaid("graph LR\n  A --> B")
    assert dtype == "graph"
    assert g.node_count == 2
    assert g.edge_count == 1


def test_class_diagram_type():
    dtype, g = parse_mermaid("classDiagram\nClass01 <|-- Class02")
    assert dtype == "classdiagram"


def test_undirected_edge():
    _, g = parse_mermaid("graph LR\nA --- B")
    assert g.edges[0].kind == "undirected"


def test_comment_stripped():
    _, g = parse_mermaid("graph LR\n%% comment\nA --> B")
    assert g.edge_count == 1
