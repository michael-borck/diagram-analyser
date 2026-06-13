"""Diagram embedding wiring — field presence + graceful degradation."""
from __future__ import annotations
import importlib.util
import pytest
from diagram_analyser.embedding import embed_document
from diagram_analyser.schemas import DiagramAnalysis

_TEXT = importlib.util.find_spec("lens_embed") is not None and importlib.util.find_spec("sentence_transformers") is not None

def test_field_default_none():
    assert "embedding" in DiagramAnalysis.model_fields
    assert DiagramAnalysis.model_fields["embedding"].default is None

def test_empty_is_none():
    assert embed_document("") is None

@pytest.mark.skipif(_TEXT, reason="embeddings extra installed")
def test_none_without_backend():
    assert embed_document("graph TD; A-->B; B-->C;") is None

@pytest.mark.skipif(not _TEXT, reason="needs lens-embed[text]")
def test_vector_with_backend():
    v = embed_document("graph TD;\n A[Start]-->B[Process];\n B-->C[End];\n\n" * 5)
    assert isinstance(v, list) and len(v) == 384
