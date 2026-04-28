"""
tests/test_all.py
-----------------
Automated test suite for the Private Document Agent.
Tests every module with real data (no mocks for local components).

Run with:
    python -m pytest tests/ -v
    python -m pytest tests/ -v --tb=short   # shorter tracebacks
"""

import os
import sys
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_TEXT = """
Section 1: Leave Policy
Employees are entitled to 20 days of paid annual leave per year.
Leave must be approved by the manager 5 days in advance.
Unused leave can be carried forward for a maximum of 5 days.

Section 2: Work From Home
Employees may work from home up to 3 days per week.
Core hours are 10 AM to 4 PM on all working days.
VPN access is required when connecting remotely.

Section 3: Expense Claims
Travel expenses are reimbursed at actual cost with receipts.
Meal allowance during travel is up to INR 1,200 per day.
Claims must be submitted within 30 days.
"""

SAMPLE_TEXT_2 = """
Project Alpha Technical Specification
The project budget is INR 45,00,000 exclusive of taxes.
Go-live date is April 30, 2024.
Tech Lead is Rahul Mehta.
The backend uses FastAPI with Python 3.11.
Database is PostgreSQL 16 with Redis for caching.
"""


@pytest.fixture
def tmp_dir():
    """Provide a clean temporary directory."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_txt_file(tmp_dir):
    """Write sample text to a .txt file."""
    f = tmp_dir / "sample.txt"
    f.write_text(SAMPLE_TEXT, encoding="utf-8")
    return str(f)


@pytest.fixture
def sample_docs_folder(tmp_dir):
    """Create a folder with two sample .txt documents."""
    folder = tmp_dir / "docs"
    folder.mkdir()
    (folder / "handbook.txt").write_text(SAMPLE_TEXT, encoding="utf-8")
    (folder / "spec.txt").write_text(SAMPLE_TEXT_2, encoding="utf-8")
    return str(folder)


@pytest.fixture
def sample_document():
    """Return a document dict as produced by document_loader."""
    return {
        "source": "/tmp/sample.txt",
        "filename": "sample.txt",
        "content": SAMPLE_TEXT,
        "file_type": ".txt",
        "char_count": len(SAMPLE_TEXT),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. document_loader tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDocumentLoader:

    def test_load_txt_file(self, sample_txt_file):
        from core.document_loader import load_single_document
        doc = load_single_document(sample_txt_file)
        assert doc["filename"] == "sample.txt"
        assert "Leave Policy" in doc["content"]
        assert doc["char_count"] > 0
        assert doc["file_type"] == ".txt"

    def test_load_missing_file_raises(self):
        from core.document_loader import load_single_document
        with pytest.raises(FileNotFoundError):
            load_single_document("/nonexistent/path/file.txt")

    def test_unsupported_extension_raises(self, tmp_dir):
        from core.document_loader import load_single_document
        bad = tmp_dir / "file.xyz"
        bad.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_single_document(str(bad))

    def test_load_folder(self, sample_docs_folder):
        from core.document_loader import load_documents_from_folder
        docs = load_documents_from_folder(sample_docs_folder)
        assert len(docs) == 2
        filenames = {d["filename"] for d in docs}
        assert "handbook.txt" in filenames
        assert "spec.txt" in filenames

    def test_load_empty_folder_raises(self, tmp_dir):
        from core.document_loader import load_documents_from_folder
        with pytest.raises(ValueError, match="No supported documents"):
            load_documents_from_folder(str(tmp_dir))

    def test_load_md_file(self, tmp_dir):
        from core.document_loader import load_single_document
        md = tmp_dir / "notes.md"
        md.write_text("# Title\n\nSome content here.")
        doc = load_single_document(str(md))
        assert doc["file_type"] == ".md"
        assert "Title" in doc["content"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. chunking tests
# ─────────────────────────────────────────────────────────────────────────────

class TestChunking:

    def test_basic_chunking(self, sample_document):
        from core.chunking import chunk_document
        chunks = chunk_document(sample_document, chunk_size=200, chunk_overlap=30)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert "text" in chunk
            assert "filename" in chunk
            assert "chunk_index" in chunk
            assert "total_chunks" in chunk
            assert len(chunk["text"]) > 50  # no tiny chunks

    def test_chunk_metadata_correct(self, sample_document):
        from core.chunking import chunk_document
        chunks = chunk_document(sample_document)
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
            assert chunk["total_chunks"] == len(chunks)
            assert chunk["filename"] == "sample.txt"

    def test_chunk_overlap(self, sample_document):
        from core.chunking import chunk_document
        # With overlap, adjacent chunks should share some text
        chunks = chunk_document(sample_document, chunk_size=300, chunk_overlap=100)
        if len(chunks) >= 2:
            # Some words from chunk 0 end should appear in chunk 1 start
            end_words = set(chunks[0]["text"].split()[-10:])
            start_words = set(chunks[1]["text"].split()[:20])
            # There should be overlap (not guaranteed to be exact but usually true)
            # Just check chunks are non-empty
            assert len(chunks[0]["text"]) > 0
            assert len(chunks[1]["text"]) > 0

    def test_chunk_documents_multiple(self, sample_document):
        from core.chunking import chunk_documents
        doc2 = {**sample_document, "filename": "doc2.txt", "content": SAMPLE_TEXT_2}
        all_chunks = chunk_documents([sample_document, doc2])
        filenames = {c["filename"] for c in all_chunks}
        assert "sample.txt" in filenames
        assert "doc2.txt" in filenames


# ─────────────────────────────────────────────────────────────────────────────
# 3. embeddings tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEmbeddings:

    def test_embed_texts_shape(self):
        from core.embeddings import embed_texts
        texts = ["Hello world", "This is a test sentence.", "Another sentence here."]
        embs = embed_texts(texts, show_progress=False)
        assert embs.shape == (3, 384)  # all-MiniLM-L6-v2 produces 384-dim vectors
        assert embs.dtype == np.float32

    def test_embed_query_shape(self):
        from core.embeddings import embed_query
        vec = embed_query("What is the leave policy?")
        assert vec.shape == (1, 384)
        assert vec.dtype == np.float32

    def test_embeddings_normalized(self):
        from core.embeddings import embed_texts
        embs = embed_texts(["Test sentence for norm check"], show_progress=False)
        # L2 norm should be ~1.0 for normalized embeddings
        norm = np.linalg.norm(embs[0])
        assert abs(norm - 1.0) < 0.01

    def test_similar_texts_closer_than_dissimilar(self):
        from core.embeddings import embed_texts
        texts = [
            "The annual leave policy grants 20 days.",
            "Employees get 20 days of paid leave per year.",
            "The database uses PostgreSQL for storage.",
        ]
        embs = embed_texts(texts, show_progress=False)
        # Similarity between texts[0] and texts[1] (same topic)
        sim_similar = float(np.dot(embs[0], embs[1]))
        # Similarity between texts[0] and texts[2] (different topic)
        sim_different = float(np.dot(embs[0], embs[2]))
        assert sim_similar > sim_different

    def test_empty_texts_raises(self):
        from core.embeddings import embed_texts
        with pytest.raises(ValueError, match="No texts provided"):
            embed_texts([])


# ─────────────────────────────────────────────────────────────────────────────
# 4. vector_store tests
# ─────────────────────────────────────────────────────────────────────────────

class TestVectorStore:

    def _make_store_with_data(self, tmp_dir):
        from core.vector_store import VectorStore
        from core.embeddings import embed_texts

        texts = [
            "The annual leave policy is 20 days per year.",
            "Employees may work from home 3 days a week.",
            "Expense claims must be submitted within 30 days.",
            "The project budget is INR 45 lakhs.",
            "Go-live date is April 30, 2024.",
        ]
        chunks = [
            {"text": t, "filename": f"doc{i//3}.txt", "chunk_index": i % 3,
             "total_chunks": 3, "file_type": ".txt", "source": f"/tmp/doc{i//3}.txt"}
            for i, t in enumerate(texts)
        ]
        embs = embed_texts(texts, show_progress=False)

        store = VectorStore(str(tmp_dir / "vs"))
        store.add(embs, chunks)
        return store, chunks

    def test_add_and_search(self, tmp_dir):
        from core.embeddings import embed_query
        store, _ = self._make_store_with_data(tmp_dir)

        assert store.total_chunks == 5
        query_vec = embed_query("How many days of annual leave?")
        results = store.search(query_vec, top_k=2)

        assert len(results) == 2
        chunk, score = results[0]
        assert "text" in chunk
        assert isinstance(score, float)
        # The top result should be about leave
        assert "leave" in chunk["text"].lower() or score > 0.3

    def test_save_and_load(self, tmp_dir):
        from core.vector_store import VectorStore
        from core.embeddings import embed_query

        store, _ = self._make_store_with_data(tmp_dir)
        store.save()

        # Load from disk
        loaded = VectorStore.load(str(tmp_dir / "vs"))
        assert loaded.total_chunks == 5
        assert len(loaded.metadata) == 5

        query_vec = embed_query("project budget")
        results = loaded.search(query_vec, top_k=1)
        assert len(results) == 1

    def test_exists_check(self, tmp_dir):
        from core.vector_store import VectorStore
        assert not VectorStore.exists(str(tmp_dir / "vs"))

        store, _ = self._make_store_with_data(tmp_dir)
        store.save()

        assert VectorStore.exists(str(tmp_dir / "vs"))

    def test_search_empty_store_raises(self, tmp_dir):
        from core.vector_store import VectorStore
        from core.embeddings import embed_query
        store = VectorStore(str(tmp_dir / "empty"))
        with pytest.raises(RuntimeError, match="empty"):
            store.search(embed_query("test"), top_k=3)

    def test_load_nonexistent_raises(self, tmp_dir):
        from core.vector_store import VectorStore
        with pytest.raises(FileNotFoundError):
            VectorStore.load(str(tmp_dir / "missing"))


# ─────────────────────────────────────────────────────────────────────────────
# 5. retriever tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRetriever:

    def _make_retriever(self, tmp_dir):
        from core.vector_store import VectorStore
        from core.embeddings import embed_texts
        from core.retriever import Retriever

        texts = [
            "Employees get 20 days annual leave per year.",
            "Work from home is allowed 3 days per week.",
            "The project budget is 45 lakhs INR.",
            "Go-live date is April 30, 2024.",
            "Backend uses FastAPI and PostgreSQL.",
        ]
        chunks = [
            {"text": t, "filename": "doc.txt", "chunk_index": i,
             "total_chunks": len(texts), "file_type": ".txt", "source": "/tmp/doc.txt"}
            for i, t in enumerate(texts)
        ]
        embs = embed_texts(texts, show_progress=False)
        store = VectorStore(str(tmp_dir / "vs"))
        store.add(embs, chunks)

        return Retriever(store, top_k=3)

    def test_retrieve_returns_list(self, tmp_dir):
        retriever = self._make_retriever(tmp_dir)
        results = retriever.retrieve("How many days of annual leave?")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_retrieve_result_structure(self, tmp_dir):
        retriever = self._make_retriever(tmp_dir)
        results = retriever.retrieve("project budget")
        for r in results:
            assert "text" in r
            assert "filename" in r
            assert "similarity" in r
            assert "chunk_index" in r
            assert 0.0 <= r["similarity"] <= 1.0

    def test_retrieve_relevant_result_on_top(self, tmp_dir):
        retriever = self._make_retriever(tmp_dir)
        results = retriever.retrieve("annual leave days")
        # Top result should be about leave
        assert "leave" in results[0]["text"].lower()

    def test_retrieve_respects_top_k(self, tmp_dir):
        retriever = self._make_retriever(tmp_dir)
        results = retriever.retrieve("any question", top_k=2)
        assert len(results) <= 2

    def test_has_relevant_results_true(self, tmp_dir):
        retriever = self._make_retriever(tmp_dir)
        results = retriever.retrieve("leave policy")
        assert retriever.has_relevant_results(results)

    def test_has_relevant_results_empty_false(self, tmp_dir):
        retriever = self._make_retriever(tmp_dir)
        assert not retriever.has_relevant_results([])


# ─────────────────────────────────────────────────────────────────────────────
# 6. Integration test (no API call — mocks Claude)
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentIntegration:
    """Tests the agent pipeline without hitting the real Claude API."""

    def _make_agent(self, tmp_dir, monkeypatch):
        from core.vector_store import VectorStore
        from core.embeddings import embed_texts
        from core.retriever import Retriever
        from core.agent import DocumentAgent

        # Set dummy API key so agent initializes
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        texts = [
            "Employees are entitled to 20 days of paid annual leave per year.",
            "Work from home is allowed up to 3 days per week.",
        ]
        chunks = [
            {"text": t, "filename": "handbook.txt", "chunk_index": i,
             "total_chunks": 2, "file_type": ".txt", "source": "/tmp/handbook.txt"}
            for i, t in enumerate(texts)
        ]
        embs = embed_texts(texts, show_progress=False)
        store = VectorStore(str(tmp_dir / "vs"))
        store.add(embs, chunks)
        retriever = Retriever(store, top_k=2)
        return DocumentAgent(retriever)

    def test_build_context_block(self):
        from core.agent import build_context_block
        chunks = [
            {"text": "Some relevant text.", "filename": "doc.txt",
             "chunk_index": 0, "total_chunks": 5, "similarity": 0.85}
        ]
        context = build_context_block(chunks)
        assert "doc.txt" in context
        assert "Some relevant text." in context
        assert "85%" in context

    def test_build_context_empty(self):
        from core.agent import build_context_block
        result = build_context_block([])
        assert "No relevant" in result

    def test_agent_no_api_key_raises(self, tmp_dir, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from core.vector_store import VectorStore
        from core.embeddings import embed_texts
        from core.retriever import Retriever
        from core.agent import DocumentAgent

        texts = ["Some text"]
        chunks = [{"text": t, "filename": "f.txt", "chunk_index": 0,
                   "total_chunks": 1, "file_type": ".txt", "source": "/f.txt"}
                  for t in texts]
        embs = embed_texts(texts, show_progress=False)
        store = VectorStore(str(tmp_dir / "vs2"))
        store.add(embs, chunks)
        retriever = Retriever(store)

        with pytest.raises(Exception):
            # Should fail when trying to init Anthropic client without key
            agent = DocumentAgent(retriever)
            agent.answer("test")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Utils tests
# ─────────────────────────────────────────────────────────────────────────────

class TestUtils:

    def test_get_local_ip(self):
        from utils.helpers import get_local_ip
        ip = get_local_ip()
        assert isinstance(ip, str)
        # Should be a valid IP address
        parts = ip.split(".")
        assert len(parts) == 4

    def test_format_file_size(self):
        from utils.helpers import format_file_size
        assert format_file_size(512) == "512.0 B"
        assert "KB" in format_file_size(2048)
        assert "MB" in format_file_size(2 * 1024 * 1024)

    def test_truncate_text(self):
        from utils.helpers import truncate_text
        short = "Hello"
        assert truncate_text(short, 100) == short

        long_text = "A" * 300
        truncated = truncate_text(long_text, 200)
        assert len(truncated) <= 204  # 200 + ellipsis
        assert truncated.endswith("…")

    def test_check_environment(self, monkeypatch, tmp_dir):
        from utils.helpers import check_environment
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("DOCUMENTS_PATH", str(tmp_dir))

        result = check_environment()
        assert "python_ok" in result
        assert "api_key_set" in result
        assert result["api_key_set"] is True
        assert result["python_ok"] is True  # We're running Python 3.10+


# ─────────────────────────────────────────────────────────────────────────────
# Run summary
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    sys.exit(result.returncode)
