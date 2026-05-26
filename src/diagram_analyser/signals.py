"""Graph-theoretic signals — same maths for every diagram format."""
from __future__ import annotations

import networkx as nx

from .schemas import Graph, NamingSignals, StructuralSignals

_CYCLE_SAMPLE_CAP = 5
_SHORT_LABEL_CAP = 10


def structural_signals(graph: Graph) -> StructuralSignals:
    """networkx-backed graph analysis: orphans, cycles, depth, components."""
    if graph.node_count == 0:
        return StructuralSignals(connected_components=0, is_dag=True)

    # Build a directed graph by default; undirected edges replicate both ways so
    # connected-component / orphan calculations still see them.
    G = nx.DiGraph()
    for n in graph.nodes:
        G.add_node(n.id)
    for e in graph.edges:
        G.add_edge(e.source, e.target)
        if e.kind == "undirected":
            G.add_edge(e.target, e.source)

    # Orphans = nodes with no incident edges in either direction.
    orphan_ids = [n for n in G.nodes() if G.in_degree(n) == 0 and G.out_degree(n) == 0]

    # Cycles — simple_cycles iterates lazily; cap so massive graphs don't blow up.
    cycles: list[list[str]] = []
    try:
        for i, cyc in enumerate(nx.simple_cycles(G)):
            if i >= _CYCLE_SAMPLE_CAP:
                break
            cycles.append(cyc + [cyc[0]] if cyc else cyc)
    except Exception:
        cycles = []

    cycle_count = _cycle_count(G)
    is_dag = nx.is_directed_acyclic_graph(G)

    # Longest path — only well-defined on a DAG; fall back to a cycle-aware heuristic.
    max_depth = _longest_path_length(G, is_dag)

    # Use the underlying undirected graph for connected-components (the standard
    # interpretation: "are all parts of this diagram connected?").
    components = nx.number_connected_components(G.to_undirected())

    return StructuralSignals(
        orphan_nodes=sorted(orphan_ids),
        cycle_count=cycle_count,
        cycles=cycles,
        max_depth=max_depth,
        is_dag=is_dag,
        connected_components=components,
    )


def _cycle_count(G: nx.DiGraph) -> int:
    """Number of simple cycles (counted up to a sanity cap to avoid pathological enumeration)."""
    try:
        count = 0
        for _ in nx.simple_cycles(G):
            count += 1
            if count >= 1000:  # safety
                break
        return count
    except Exception:
        return 0


def _longest_path_length(G: nx.DiGraph, is_dag: bool) -> int:
    """Number of nodes on the longest path (1 = single node)."""
    if G.number_of_nodes() == 0:
        return 0
    if is_dag:
        try:
            return nx.dag_longest_path_length(G) + 1
        except Exception:
            return 1
    # Cycle-bearing: use BFS depth from each node, taking the max over a node visit
    # cap so we don't try every node on a huge graph.
    best = 1
    for src in list(G.nodes())[:200]:
        # Manual BFS — track depth, allow revisits up to a small bound to break cycles.
        seen = {src}
        layer = [src]
        depth = 1
        while layer:
            depth += 1
            next_layer = []
            for n in layer:
                for nbr in G.successors(n):
                    if nbr not in seen:
                        seen.add(nbr)
                        next_layer.append(nbr)
            layer = next_layer
            if depth > 1000:  # safety
                break
        if depth - 1 > best:
            best = depth - 1
    return best


def naming_signals(graph: Graph) -> NamingSignals:
    """Label quality — proxy for diagram clarity."""
    if not graph.nodes:
        return NamingSignals()
    with_label = sum(1 for n in graph.nodes if n.label and n.label != n.id)
    coverage = round(with_label / len(graph.nodes), 4)
    lengths = [len(n.label) for n in graph.nodes if n.label]
    avg = round(sum(lengths) / len(lengths), 2) if lengths else 0.0
    short = [n.label for n in graph.nodes if n.label and len(n.label.strip()) <= 2][:_SHORT_LABEL_CAP]
    return NamingSignals(
        nodes_with_label=with_label,
        label_coverage=coverage,
        avg_label_length=avg,
        suspiciously_short_labels=short,
    )
