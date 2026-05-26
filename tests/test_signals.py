"""Unit tests for networkx-backed structural & naming signals."""
from diagram_analyser.schemas import Edge, Graph, Node
from diagram_analyser.signals import naming_signals, structural_signals


def _graph(nodes: list[tuple[str, str]], edges: list[tuple[str, str]], *, kind: str = "directed") -> Graph:
    ns = [Node(id=i, label=l) for i, l in nodes]
    es = [Edge(source=s, target=t, kind=kind) for s, t in edges]
    return Graph(nodes=ns, edges=es, node_count=len(ns), edge_count=len(es))


class TestStructural:
    def test_empty(self):
        s = structural_signals(Graph())
        assert s.connected_components == 0
        assert s.is_dag is True

    def test_linear_chain_is_dag(self):
        g = _graph([("A", "A"), ("B", "B"), ("C", "C")], [("A", "B"), ("B", "C")])
        s = structural_signals(g)
        assert s.is_dag
        assert s.cycle_count == 0
        assert s.orphan_nodes == []
        assert s.max_depth == 3
        assert s.connected_components == 1

    def test_orphan(self):
        g = _graph([("A", "A"), ("B", "B"), ("C", "C")], [("A", "B")])
        s = structural_signals(g)
        assert s.orphan_nodes == ["C"]
        assert s.connected_components == 2

    def test_cycle_detected(self):
        g = _graph([("A", "A"), ("B", "B")], [("A", "B"), ("B", "A")])
        s = structural_signals(g)
        assert s.cycle_count >= 1
        assert s.is_dag is False
        assert len(s.cycles) >= 1

    def test_undirected_orphan(self):
        # Even with undirected edges, the orphan should still register.
        g = _graph([("A", "A"), ("B", "B"), ("C", "C")], [("A", "B")], kind="undirected")
        s = structural_signals(g)
        assert s.orphan_nodes == ["C"]


class TestNaming:
    def test_label_coverage(self):
        # A has label "Start" (≠ id), B has label "B" (= id) so it doesn't count.
        g = _graph([("A", "Start"), ("B", "B"), ("C", "End")], [])
        n = naming_signals(g)
        assert n.nodes_with_label == 2
        assert n.label_coverage == round(2 / 3, 4)

    def test_short_labels_flagged(self):
        g = _graph([("X", "X"), ("Y", "OK"), ("Z", "A")], [])
        n = naming_signals(g)
        assert "A" in n.suspiciously_short_labels
        # "OK" is 2 chars — included; "X" is 1 char — included.
        assert "OK" in n.suspiciously_short_labels
        assert "X" in n.suspiciously_short_labels
