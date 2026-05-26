"""Unit tests for the drawio XML parser."""
import pytest

from diagram_analyser.exceptions import DiagramAnalyserError
from diagram_analyser.parsers import parse_drawio


_SAMPLE = """<mxfile>
  <diagram>
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Start" style="rounded=1;" vertex="1" parent="1"/>
        <mxCell id="3" value="End" style="shape=ellipse;" vertex="1" parent="1"/>
        <mxCell id="4" source="2" target="3" edge="1" parent="1"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


def test_basic_vertex_edge():
    dtype, g = parse_drawio(_SAMPLE)
    assert dtype == "drawio"
    by_id = {n.id: n for n in g.nodes}
    assert by_id["2"].label == "Start"
    assert by_id["3"].kind == "ellipse"
    assert g.edge_count == 1
    assert g.edges[0].source == "2"
    assert g.edges[0].target == "3"


def test_skips_root_and_default_parent():
    _, g = parse_drawio(_SAMPLE)
    assert all(n.id not in ("0", "1") for n in g.nodes)


def test_strips_html_in_label():
    # Real drawio XML escapes the HTML inside `value=` — that's what we'd
    # see on disk after the parser unescapes it.
    src = """<mxfile><diagram><mxGraphModel><root>
      <mxCell id="0"/><mxCell id="1" parent="0"/>
      <mxCell id="2" value="&lt;font&gt;Foo&lt;/font&gt;" vertex="1"/>
    </root></mxGraphModel></diagram></mxfile>"""
    _, g = parse_drawio(src)
    assert g.nodes[0].label == "Foo"


def test_invalid_xml_raises():
    with pytest.raises(DiagramAnalyserError, match="not valid XML"):
        parse_drawio("<not xml")


def test_empty_input():
    _, g = parse_drawio("")
    assert g.node_count == 0
