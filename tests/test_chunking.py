from rag.chunking import chunk_text


def test_chunk_text_splits_long_text():
    text = "This is a sentence. " * 200  # long enough to require multiple chunks
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(isinstance(c, str) and c.strip() for c in chunks)


def test_chunk_text_empty_input_returns_empty_list():
    assert chunk_text("") == []


def test_chunk_text_short_text_returns_single_chunk():
    text = "Short customer support policy text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text
