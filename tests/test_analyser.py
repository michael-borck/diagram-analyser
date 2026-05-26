"""End-to-end tests for the dispatcher."""
from pathlib import Path

import pytest

from diagram_analyser import DiagramAnalyser, DiagramAnalyserError, DiagramAnalysis


def test_mermaid_e2e(tmp_path: Path):
    f = tmp_path / "flow.mmd"
    f.write_text("flowchart TD\nA --> B\nB --> C\n")
    r = DiagramAnalyser().analyse(f)
    assert isinstance(r, DiagramAnalysis)
    assert r.file_format == "mermaid"
    assert r.graph.node_count == 3
    assert r.structure.is_dag


def test_plantuml_e2e(tmp_path: Path):
    f = tmp_path / "model.puml"
    f.write_text("@startuml\nclass A\nclass B\nA --> B\n@enduml\n")
    r = DiagramAnalyser().analyse(f)
    assert r.file_format == "plantuml"
    assert r.graph.edge_count == 1


def test_graphviz_e2e(tmp_path: Path):
    f = tmp_path / "g.dot"
    f.write_text('digraph G { A -> B [label="x"]; }\n')
    r = DiagramAnalyser().analyse(f)
    assert r.file_format == "graphviz"
    assert r.graph.edges[0].label == "x"


def test_drawio_e2e(tmp_path: Path):
    f = tmp_path / "d.drawio"
    f.write_text("""<mxfile><diagram><mxGraphModel><root>
      <mxCell id="0"/><mxCell id="1" parent="0"/>
      <mxCell id="2" value="A" vertex="1"/>
      <mxCell id="3" value="B" vertex="1"/>
      <mxCell id="4" source="2" target="3" edge="1"/>
    </root></mxGraphModel></diagram></mxfile>""")
    r = DiagramAnalyser().analyse(f)
    assert r.file_format == "drawio"
    assert r.graph.node_count == 2


def test_missing_file_raises():
    with pytest.raises(DiagramAnalyserError, match="not found"):
        DiagramAnalyser().analyse("/nope/missing.mmd")


def test_unsupported_extension_raises(tmp_path: Path):
    f = tmp_path / "x.txt"
    f.write_text("not a diagram")
    with pytest.raises(DiagramAnalyserError, match="Unsupported extension"):
        DiagramAnalyser().analyse(f)


def test_image_without_vision_returns_error_in_vision_info(tmp_path: Path):
    """Image path should not raise — it should return a result with vision.error set."""
    f = tmp_path / "fake.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\nfake")  # not a real PNG but enough for path dispatch
    r = DiagramAnalyser().analyse(f)
    assert r.file_format == "image"
    assert r.vision is not None
    # Either anthropic isn't installed OR no API key set OR API call fails — any of those
    # should land in vision.error; the analyser must NOT raise.
    assert r.vision.error is not None
