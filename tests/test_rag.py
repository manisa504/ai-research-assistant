import json

import pytest

from document_processor import TextChunk
from rag import RAGIndex, INSUFFICIENT, validate_answer


HITS = [{"id": "S1", "filename": "notes.pdf", "page": 2, "chunk": 1,
         "text": "The trial enrolled 120 participants.", "score": 0.8}]


def output(source="S1", quote="120 participants"):
    return json.dumps({"supported": True, "claims": [{"text": "120 participants enrolled.",
                       "evidence": [{"id": source, "quote": quote}]}]})


def test_valid_citation_is_created_from_metadata():
    result = validate_answer(output(), HITS)
    assert result.supported
    assert "[notes.pdf, p. 2]" in result.text
    assert result.sources[0]["quote"] == "120 participants"


@pytest.mark.parametrize("raw", [output("S99"), output(quote="500 participants"), "bad JSON",
    '{"supported":true,"claims":[]}', '{"supported":false}',
    '{"supported":true,"claims":[{"text":"invented","evidence":[]}]}'])
def test_unverifiable_answers_abstain(raw):
    result = validate_answer(raw, HITS)
    assert not result.supported
    assert result.text == INSUFFICIENT
    assert not result.sources


class FakeBedrock:
    def embed(self, text):
        return [1.0, 0.0] if "ocean" in text else [0.0, 1.0]


def test_faiss_search_returns_relevant_page():
    client = FakeBedrock()
    chunks = [TextChunk("notes.pdf", 1, 1, "ocean temperature"),
              TextChunk("notes.pdf", 3, 2, "forest coverage")]
    index = RAGIndex.build(chunks, client)
    hits = index.retrieve("ocean", client, top_k=1)
    assert len(hits) == 1
    assert hits[0]["page"] == 1
    assert hits[0]["score"] == pytest.approx(1)


@pytest.mark.parametrize("vectors", [[[0, 0]], [[float("nan"), 0]], [[1, 0], [0, 1]]])
def test_bad_embedding_matrix_rejected(vectors):
    with pytest.raises(ValueError):
        RAGIndex([TextChunk("notes.pdf", 1, 1, "ocean")], vectors)


def test_index_build_failure_does_not_return_partial_index():
    class Failing:
        def embed(self, text):
            raise RuntimeError("Bedrock unavailable")
    with pytest.raises(RuntimeError, match="unavailable"):
        RAGIndex.build([TextChunk("notes.pdf", 1, 1, "ocean")], Failing())
