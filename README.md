# diagram-analyser

**Structural analysis of diagrams** — the [lens-family](https://github.com/michael-borck/lens-analysers)
member that reads diagrams as *graphs* (nodes + edges) rather than as raster images.

Supports four text formats out of the box:

| Format | Extensions |
|---|---|
| Mermaid | `.mmd`, `.mermaid` |
| PlantUML | `.puml`, `.plantuml` |
| Graphviz / DOT | `.dot`, `.gv` |
| drawio (XML) | `.drawio` |

Plus an **optional `[vision]` path** for image diagrams (`.png`/`.jpg`) via Anthropic Claude Vision —
explicit-only, since those extensions auto-route to image-analyser.

> `image-analyser` sees raster pixels; this one parses the diagram's *structure* —
> nodes, edges, orphans, cycles, depth, naming. Built for design-unit assessment
> (CS/IS architecture, ER, UML, flowcharts).

## Install

```bash
pip install diagram-analyser                       # text formats — pure Python
pip install 'diagram-analyser[vision]'             # adds image-diagram support
```

For the vision path, set one of:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Use

**Python:**

```python
from diagram_analyser import DiagramAnalyser

result = DiagramAnalyser().analyse("architecture.mmd")
print(result.diagram_type)              # "flowchart"
print(result.graph.node_count)          # 7
print(result.structure.orphan_nodes)    # []
print(result.structure.cycle_count)     # 1
print(result.structure.is_dag)          # False

# Image diagram (needs [vision] extra + ANTHROPIC_API_KEY):
result = DiagramAnalyser().analyse("diagram.png")
print(result.vision.raw_description)
```

**CLI:**

```bash
diagram-analyser flow.mmd                  # human summary
diagram-analyser model.puml --json         # raw JSON
diagram-analyser arch.png                  # vision path (needs API key)
diagram-analyser serve                     # HTTP API on port 8013
diagram-analyser manifest                  # capability manifest
```

**HTTP** (`diagram-analyser serve` on port 8013):

```bash
curl -F file=@flow.mmd http://localhost:8013/analyse
curl http://localhost:8013/health
```

## Signals

For every diagram (text or vision-extracted):

- **Graph** — nodes (id, label, kind), edges (source, target, kind, label), counts.
- **Structure** — `orphan_nodes` (disconnected), `cycle_count` + sample cycles, `max_depth`,
  `is_dag`, `connected_components`.
- **Naming quality** — label coverage, average label length, suspiciously short labels.
- **Diagram type** — for mermaid: `flowchart` / `classDiagram` / `erDiagram` / `sequenceDiagram` /
  `stateDiagram`; for PlantUML: `uml` / `mindmap` / `wbs`; for graphviz: `digraph` / `graph`;
  for drawio: best-effort from cell hints.

## The family

Part of the [lens analyser family](https://github.com/michael-borck/lens-analysers).

| What you want | Use |
|---|---|
| Raster image (any kind) | **image-analyser** |
| Structured diagram (mermaid/UML/drawio/dot) | **diagram-analyser** (this) |
| Image *of* a diagram | image-analyser detects + auto-analyser cascades to here, or `diagram-analyser file.png` directly |
| Any file → right engine | **auto-analyser** |

## Limits

- v1 text parsers are pragmatic — not full grammars. They get nodes, edges, and the diagram
  type for ~all realistic student diagrams; corner cases (subgraphs, deeply nested mermaid
  classes) may parse approximately.
- Vision path produces structure only as well as the LLM extracts it. We surface the raw
  description so you can verify.

## License

MIT
