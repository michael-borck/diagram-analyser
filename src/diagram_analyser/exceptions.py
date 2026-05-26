class DiagramAnalyserError(Exception):
    """Domain error from diagram-analyser (unsupported format, parse failure, etc.)."""


class VisionUnavailableError(DiagramAnalyserError):
    """Image input requires the [vision] extra + an ANTHROPIC_API_KEY env var."""
