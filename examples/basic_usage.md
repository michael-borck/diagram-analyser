# Basic usage

`diagram-analyser` does structural analysis of mermaid / PlantUML / Graphviz / drawio diagrams (graph shape, cycles, naming) for the analyser family.

## Install

```bash
pip install diagram-analyser
```

For image diagrams (`.png`/`.jpg`) via a vision model, install the extra: `pip install "diagram-analyser[vision]"`.

## CLI

```bash
diagram-analyser path/to/diagram.mmd --json
```

## Python

```python
from diagram_analyser import DiagramAnalyser

result = DiagramAnalyser().analyse("path/to/diagram.mmd")  # DiagramAnalysis (pydantic)
print(result.model_dump_json(indent=2))
```

## HTTP

```bash
diagram-analyser serve
curl -F file=@path/to/diagram.mmd http://localhost:8013/analyse
```
