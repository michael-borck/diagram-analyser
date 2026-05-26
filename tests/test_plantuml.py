"""Unit tests for the plantuml parser."""
from diagram_analyser.parsers import parse_plantuml


def test_basic_class_diagram():
    src = """@startuml
class Foo
class Bar
Foo --> Bar
@enduml
"""
    dtype, g = parse_plantuml(src)
    assert dtype == "uml"
    ids = {n.id for n in g.nodes}
    assert {"Foo", "Bar"} <= ids
    by_id = {n.id: n for n in g.nodes}
    assert by_id["Foo"].kind == "class"
    assert g.edge_count == 1


def test_inheritance_normalised():
    # B <|-- A means A inherits from B. Our parser should produce A -> B (child→parent).
    src = """@startuml
class A
class B
B <|-- A
@enduml
"""
    _, g = parse_plantuml(src)
    e = g.edges[0]
    assert e.source == "A" and e.target == "B"
    assert "extends" in (e.label or "")


def test_bracket_components():
    src = """@startuml
[Web] --> [API]
[API] --> [DB]
@enduml
"""
    _, g = parse_plantuml(src)
    ids = {n.id for n in g.nodes}
    assert {"Web", "API", "DB"} <= ids
    assert g.edge_count == 2


def test_mindmap_type():
    dtype, _ = parse_plantuml("@startmindmap\n* root\n** child\n@endmindmap")
    assert dtype == "mindmap"
