"""Canonical public surface for diagram-analyser (lens family uniformity)."""
import diagram_analyser as da


def test_canonical_names_importable():
    assert da.DiagramAnalyser is not None
    assert da.DiagramAnalysis is not None
    assert da.MANIFEST is not None
    assert da.DiagramAnalyserError is not None


def test_analyse_is_callable():
    assert callable(da.analyse)


def test_manifest_name():
    assert da.MANIFEST["name"] == "diagram-analyser"


def test_version_is_str():
    assert isinstance(da.__version__, str)


def test_canonical_names_in_all():
    for name in (
        "DiagramAnalyser",
        "DiagramAnalysis",
        "analyse",
        "MANIFEST",
        "__version__",
        "DiagramAnalyserError",
    ):
        assert name in da.__all__
