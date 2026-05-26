"""CLI entry point for diagram-analyser."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    from lens_contract import run_contract_subcommands

    from .manifest import MANIFEST

    if run_contract_subcommands(
        MANIFEST,
        app_path="diagram_analyser.api:app",
        default_port=8013,
        env_prefix="DIAGRAM_ANALYSER",
    ):
        return

    parser = argparse.ArgumentParser(
        prog="diagram-analyser",
        description="Structural analysis of mermaid / PlantUML / Graphviz / drawio diagrams (plus image diagrams via optional vision)",
        epilog="subcommands: `serve` (HTTP API on port 8013), `manifest` (capability manifest)",
    )
    parser.add_argument("file", type=Path, help="Diagram file to analyse")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args()

    _run(args)


def _run(args) -> None:
    from .analyser import DiagramAnalyser
    from .exceptions import DiagramAnalyserError

    try:
        result = DiagramAnalyser().analyse(args.file)
    except DiagramAnalyserError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(result.model_dump_json(indent=2))
        return

    _print_summary(result)


def _print_summary(result) -> None:
    print(f"File:        {result.file_path}")
    print(f"Format:      {result.file_format}  ({result.diagram_type or '?'})")
    g = result.graph
    print(f"Graph:       {g.node_count} nodes, {g.edge_count} edges")
    s = result.structure
    print(f"DAG:         {'yes' if s.is_dag else 'no'}")
    print(f"Components:  {s.connected_components}")
    print(f"Max depth:   {s.max_depth}")
    if s.orphan_nodes:
        sample = ", ".join(s.orphan_nodes[:5])
        more = f" (+{len(s.orphan_nodes)-5} more)" if len(s.orphan_nodes) > 5 else ""
        print(f"Orphans:     {len(s.orphan_nodes)}  [{sample}{more}]")
    else:
        print("Orphans:     none")
    if s.cycle_count:
        print(f"Cycles:      {s.cycle_count}")
        for cyc in s.cycles[:3]:
            print(f"             - {' → '.join(cyc)}")
    n = result.naming
    print(f"Labels:      {n.nodes_with_label}/{g.node_count}  ({n.label_coverage:.0%} have a label distinct from id)")
    if n.avg_label_length:
        print(f"Avg label:   {n.avg_label_length} chars")
    if n.suspiciously_short_labels:
        print(f"Short labels: {', '.join(n.suspiciously_short_labels)}")
    if result.vision:
        v = result.vision
        if v.error:
            print(f"Vision:      error — {v.error}")
        else:
            print(f"Vision:      {v.provider}/{v.model} extracted_structure={v.extracted_structure}")


if __name__ == "__main__":
    main()
