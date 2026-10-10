from io import BytesIO
from pathlib import Path

import pymupdf
import streamlit as st
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class Upload(BytesIO):
    def __init__(self, name: str, data: bytes):
        super().__init__(data)
        self.name = name


def test_initial_ui_enables_questions_and_disables_index():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "AI Research Assistant"
    assert not app.text_input[0].disabled
    assert app.button[0].disabled
    assert not app.button[1].disabled
    assert [metric.value for metric in app.metric] == ["0", "0", "0"]


def test_upload_preview_bad_file_isolation_and_removal(monkeypatch):
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), "The study measured ocean temperature.")
        document.new_page()  # Blank pages must not shift citations.
        pdf_bytes = document.tobytes()

    uploads = [Upload("study.pdf", pdf_bytes), Upload("broken.pdf", b"broken")]
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: uploads)
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ["1", "2", "1"]
    assert "not a valid PDF" in app.error[0].value
    assert "No extractable text" in app.warning[0].value
    assert app.session_state["chunks"][0].page_number == 1
    app.selectbox[0].select(2).run()
    assert not app.exception
    assert app.text[0].value == "No extractable text on this page."

    uploads.clear()
    app.run()
    assert not app.exception
    assert app.session_state["chunks"] == []
    assert app.session_state["parsed_documents"] == {}


def test_index_answer_and_upload_change_invalidates_evidence(monkeypatch):
    import bedrock_client
    import json

    pdf = (APP_PATH.parent / "sample_docs/research_notes.pdf").read_bytes()
    uploads = [Upload("research_notes.pdf", pdf)]
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: uploads)

    class Client:
        def embed(self, text):
            return [1.0, 0.0]
        def complete(self, system, prompt):
            source_id = next(line.split(":")[0] for line in prompt.splitlines() if "ocean temperature" in line)
            return json.dumps({"supported": True, "claims": [{"text": "The team measured ocean temperature.",
                "evidence": [{"id": source_id, "quote": "ocean temperature"}]}]})
    monkeypatch.setattr(bedrock_client, "BedrockClient", Client)
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["rag_index"].index.ntotal == 2
    app.text_input[0].set_value("What did the team measure?")
    app.button[1].click().run()
    assert not app.exception
    assert app.session_state["last_answer"].supported
    assert "research_notes.pdf, p. 1" in app.session_state["last_answer"].text
    uploads.clear()
    app.run()
    assert not app.exception
    assert "rag_index" not in app.session_state
    assert "last_answer" not in app.session_state
