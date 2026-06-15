"""diagram-analyser — structural analysis of diagrams for the lens family."""
from importlib.metadata import version as _v
from pathlib import Path

from .analyser import DiagramAnalyser
from .exceptions import DiagramAnalyserError, VisionUnavailableError
from .manifest import MANIFEST
from .schemas import (
    DiagramAnalysis,
    Edge,
    Graph,
    NamingSignals,
    Node,
    StructuralSignals,
    VisionInfo,
)

__version__ = _v("diagram-analyser")
del _v


def analyse(path: str | Path) -> DiagramAnalysis:
    """Analyse a diagram file and return a :class:`DiagramAnalysis`."""
    return DiagramAnalyser().analyse(Path(path))


__all__ = [
    "DiagramAnalyser",
    "DiagramAnalysis",
    "analyse",
    "MANIFEST",
    "__version__",
    "DiagramAnalyserError",
    "VisionUnavailableError",
    "Graph",
    "Node",
    "Edge",
    "StructuralSignals",
    "NamingSignals",
    "VisionInfo",
]
