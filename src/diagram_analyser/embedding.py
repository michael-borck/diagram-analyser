"""Diagram-source embedding via the family's shared helper (lens-embed).

A single pinned text model across the family means this vector is comparable to
other members' text vectors — for cross-artefact and cohort-distinctiveness
signals downstream. Embeds the diagram SOURCE (mermaid/PlantUML/Graphviz text);
image diagrams (the vision path) have no source text, so embedding is None
there for now. Opt-in and degradable: returns None without the [embeddings]
extra or on any failure.
"""

from __future__ import annotations


def embed_document(text: str) -> list[float] | None:
    """Pooled, L2-normalised vector, or None if embeddings are off."""
    if not text or not text.strip():
        return None
    try:
        from lens_embed import backend_available, embed_long_text
    except ImportError:
        return None
    if not backend_available("text"):
        return None
    try:
        return embed_long_text(text)
    except Exception:
        return None
