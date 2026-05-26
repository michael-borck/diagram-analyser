"""Unit tests for the Graphviz / DOT parser."""
from diagram_analyser.parsers import parse_graphviz


def test_digraph_basic():
    src = """
    digraph G {
      A [label="Start"];
      B [label="End", shape=box];
      A -> B;
    }
    """
    dtype, g = parse_graphviz(src)
    assert dtype == "digraph"
    by_id = {n.id: n for n in g.nodes}
    assert by_id["A"].label == "Start"
    assert by_id["B"].kind == "box"
    assert g.edge_count == 1
    assert g.edges[0].kind == "directed"


def test_graph_undirected():
    _, g = parse_graphviz("graph G { A -- B; }")
    assert g.edges[0].kind == "undirected"


def test_edge_label():
    _, g = parse_graphviz('digraph G { A -> B [label="yes"]; }')
    assert g.edges[0].label == "yes"


def test_attrs_defaults_block_ignored():
    # `node [shape=box];` is an attr-defaults block, not a node declaration.
    src = 'digraph G { node [shape=box]; A -> B; }'
    _, g = parse_graphviz(src)
    ids = {n.id for n in g.nodes}
    assert ids == {"A", "B"}


def test_comments_stripped():
    _, g = parse_graphviz("digraph G { /* block */ A -> B; // line\n }")
    assert g.edge_count == 1
