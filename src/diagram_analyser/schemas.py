"""Pydantic schemas for diagram-analyser output."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str
    label: str = ""
    kind: str | None = Field(None, description="Format-specific node hint (e.g. 'decision', 'actor', 'class').")


class Edge(BaseModel):
    source: str
    target: str
    kind: str = Field("directed", description="'directed' or 'undirected'.")
    label: str | None = None


class Graph(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


class StructuralSignals(BaseModel):
    """Graph-theoretic structure."""

    orphan_nodes: list[str] = Field(
        default_factory=list,
        description="Node IDs with no incident edges.",
    )
    cycle_count: int = 0
    cycles: list[list[str]] = Field(
        default_factory=list,
        description="Sample of cycles (cell-path lists). Capped for response size.",
    )
    max_depth: int = Field(
        0, description="Longest path from any root to a leaf (cycle-safe).",
    )
    is_dag: bool = True
    connected_components: int = 0


class NamingSignals(BaseModel):
    """Label-quality signals (a rough proxy for diagram clarity)."""

    nodes_with_label: int = 0
    label_coverage: float = Field(0.0, description="nodes_with_label / total nodes, 0–1.")
    avg_label_length: float = 0.0
    suspiciously_short_labels: list[str] = Field(
        default_factory=list,
        description="Labels of length 1–2 chars (likely placeholders).",
    )


class VisionInfo(BaseModel):
    """Provenance for the image-diagram path."""

    provider: str
    model: str
    raw_description: str = ""
    extracted_structure: bool = False
    error: str | None = None


class DiagramAnalysis(BaseModel):
    """Top-level result returned by DiagramAnalyser.analyse()."""

    file_path: str
    file_format: str = Field(description="'mermaid' | 'plantuml' | 'graphviz' | 'drawio' | 'image'")
    diagram_type: str | None = Field(
        None,
        description="Sub-type within the format (e.g. mermaid 'flowchart', plantuml 'uml').",
    )
    graph: Graph
    structure: StructuralSignals
    naming: NamingSignals
    vision: VisionInfo | None = None
