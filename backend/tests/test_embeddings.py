"""Tests for embedding utility."""
from __future__ import annotations

import pytest

from app.embeddings import embed_batch, embed_text


def test_embed_text_returns_vector():
    """embed_text returns list of floats."""
    vec = embed_text("Hello world")
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert all(isinstance(x, float) for x in vec)


def test_embed_batch_returns_matching_count():
    """embed_batch returns equal count of vectors."""
    texts = ["billing issue", "reset password", "server error"]
    vecs = embed_batch(texts)
    assert len(vecs) == len(texts)
    for v in vecs:
        assert isinstance(v, list)
        assert len(v) > 0


def test_embed_batch_empty():
    """Empty list returns empty list."""
    assert embed_batch([]) == []
