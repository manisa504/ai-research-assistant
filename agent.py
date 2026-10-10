"""One rule-based decision, with an explicit UI override."""
import re

from rag import Answer, INSUFFICIENT


def route_question(question: str, has_documents: bool, mode: str = "Auto") -> str:
    if mode == "Documents":
        return "documents"
    if mode == "General":
        return "general"
    # Prefixes are a predictable escape hatch when documents are present.
    if re.match(r"\s*(general:|in general\b)", question, re.I):
        return "general"
    if has_documents or re.search(r"\b(uploaded|document|pdf|paper|report|notes|file)\b", question, re.I):
        return "documents"
    return "general"


def ask(question, client, index=None, mode="Auto", has_documents=False):
    if not question.strip() or len(question) > 2000:
        raise ValueError("Enter a question between 1 and 2,000 characters.")
    route = route_question(question, has_documents or index is not None, mode)
    if route == "documents":
        if index is None:
            return Answer(INSUFFICIENT + " Upload PDFs and build their index first.")
        return index.answer(question, client)
    return Answer(client.complete(
        "Answer concisely. You do not have access to uploaded documents in this mode. "
        "Do not claim to have read files or invent citations.", question,
    ), route="general")
