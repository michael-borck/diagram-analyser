"""DiagramAnalyser — dispatch by extension, then compute uniform structural signals."""
from __future__ import annotations

from pathlib import Path

from .exceptions import DiagramAnalyserError
from .parsers import parse_drawio, parse_graphviz, parse_mermaid, parse_plantuml
from .schemas import DiagramAnalysis, Graph
from .signals import naming_signals, structural_signals

_TEXT_DISPATCH = {
    ".mmd": ("mermaid", parse_mermaid),
    ".mermaid": ("mermaid", parse_mermaid),
    ".puml": ("plantuml", parse_plantuml),
    ".plantuml": ("plantuml", parse_plantuml),
    ".dot": ("graphviz", parse_graphviz),
    ".gv": ("graphviz", parse_graphviz),
    ".drawio": ("drawio", parse_drawio),
}

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class DiagramAnalyser:
    """Parse a diagram (text or image) and return graph-theoretic + naming signals."""

    def analyse(self, path: str | Path) -> DiagramAnalysis:
        path = Path(path)
        if not path.exists():
            raise DiagramAnalyserError(f"File not found: {path}")

        suffix = path.suffix.lower()

        if suffix in _TEXT_DISPATCH:
            file_format, parse_fn = _TEXT_DISPATCH[suffix]
            try:
                text = path.read_text(errors="ignore")
            except Exception as e:
                raise DiagramAnalyserError(f"Could not read {path}: {e}") from e
            diagram_type, graph = parse_fn(text)
            return DiagramAnalysis(
                file_path=str(path),
                file_format=file_format,
                diagram_type=diagram_type,
                graph=graph,
                structure=structural_signals(graph),
                naming=naming_signals(graph),
                vision=None,
            )

        if suffix in _IMAGE_EXTENSIONS:
            # Defer import so the [vision] extra is only needed when actually used.
            from .vision import extract_from_image

            diagram_type, graph, vision_info = extract_from_image(path)
            return DiagramAnalysis(
                file_path=str(path),
                file_format="image",
                diagram_type=diagram_type,
                graph=graph,
                structure=structural_signals(graph),
                naming=naming_signals(graph),
                vision=vision_info,
            )

        raise DiagramAnalyserError(
            f"Unsupported extension: {suffix}. Supported text: {sorted(_TEXT_DISPATCH)}; "
            f"image (needs [vision]): {sorted(_IMAGE_EXTENSIONS)}."
        )
