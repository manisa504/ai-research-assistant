import pytest
from agent import ask, route_question


@pytest.mark.parametrize("question,has_docs,mode,expected", [
    ("What is RAG?", False, "Auto", "general"),
    ("What were the findings?", True, "Auto", "documents"),
    ("Summarize the uploaded PDF", False, "Auto", "documents"),
    ("general: What is Python?", True, "Auto", "general"),
    ("What is Python?", True, "General", "general"),
    ("What is Python?", False, "Documents", "documents"),
])
def test_routes(question, has_docs, mode, expected):
    assert route_question(question, has_docs, mode) == expected


def test_missing_documents_does_not_call_llm():
    result = ask("Summarize the PDF", object())
    assert not result.supported
    assert "Upload PDFs" in result.text


def test_general_response_has_no_document_citations():
    class Client:
        def complete(self, system, prompt):
            return "Python is a programming language."
    result = ask("What is Python?", Client())
    assert result.route == "general"
    assert not result.sources


def test_empty_question_rejected():
    with pytest.raises(ValueError):
        ask(" ", object())
