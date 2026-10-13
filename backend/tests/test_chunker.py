import pytest

from app.domain.entities import DocumentSection
from app.infrastructure.chunking.recursive_chunker import RecursiveTextChunker


def test_short_section_becomes_single_chunk():
    chunker = RecursiveTextChunker(chunk_size=500, overlap=50)
    chunks = chunker.split([DocumentSection(text="Texto curto.", page=3, ocr=True)])
    assert len(chunks) == 1
    assert chunks[0].page == 3 and chunks[0].ocr is True


def test_long_text_respects_size_and_keeps_metadata():
    paragraph = "O aluno deve cumprir a carga horária mínima do estágio supervisionado. " * 10
    text = "\n\n".join([paragraph] * 8)
    chunker = RecursiveTextChunker(chunk_size=800, overlap=100)
    chunks = chunker.split([DocumentSection(text=text, page=7, heading="Estágio")])
    assert len(chunks) > 1
    assert all(len(c.text) <= 800 for c in chunks)
    assert all(c.page == 7 and c.heading == "Estágio" for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_overlap_repeats_context_between_chunks():
    sentences = [f"Frase número {i} do regulamento acadêmico." for i in range(60)]
    chunker = RecursiveTextChunker(chunk_size=300, overlap=120)
    pieces = chunker.split_text(" ".join(sentences))
    assert len(pieces) > 2
    for previous, current in zip(pieces, pieces[1:]):
        first_word_block = current.split(".")[0]
        assert first_word_block in previous


def test_table_sections_are_not_split():
    table = "\n".join(f"Disciplina: Cálculo {i}; Carga: 60h" for i in range(100))
    chunker = RecursiveTextChunker(chunk_size=300, overlap=50)
    chunks = chunker.split([DocumentSection(text=table, kind="table")])
    assert len(chunks) == 1


def test_invalid_overlap():
    with pytest.raises(ValueError):
        RecursiveTextChunker(chunk_size=100, overlap=100)
