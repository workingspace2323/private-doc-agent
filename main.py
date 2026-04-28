"""
main.py
-------
Command-line interface for the Private Document Agent.

Commands:
  python main.py ingest [--path PATH]   — Load documents and build vector store
  python main.py query "your question"  — Ask a question (no web server)
  python main.py stats                  — Show vector store statistics
  python main.py serve                  — Start the web server (same as app.py)
"""

import argparse
import logging
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def get_config():
    return {
        "vector_store_path": os.getenv("VECTOR_STORE_PATH", "./data/vectorstore"),
        "documents_path": os.getenv("DOCUMENTS_PATH", "./data/documents"),
        "chunk_size": int(os.getenv("CHUNK_SIZE", "3200")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "400")),
        "top_k": int(os.getenv("TOP_K_RESULTS", "5")),
    }


def cmd_ingest(args):
    """Ingest documents and build the FAISS vector store."""
    from core.document_loader import load_documents_from_folder
    from core.chunking import chunk_documents
    from core.embeddings import embed_texts
    from core.vector_store import VectorStore

    config = get_config()
    doc_path = args.path or config["documents_path"]

    print(f"\n📂 Loading documents from: {doc_path}")
    documents = load_documents_from_folder(doc_path)
    print(f"   ✓ Loaded {len(documents)} document(s)")

    print(f"\n✂️  Chunking documents (size={config['chunk_size']}, overlap={config['chunk_overlap']})...")
    chunks = chunk_documents(
        documents,
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
    )
    print(f"   ✓ Created {len(chunks)} chunks")

    print(f"\n🔢 Embedding chunks (this may take a few minutes for large documents)...")
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, show_progress=True)
    print(f"   ✓ Created embeddings of shape {embeddings.shape}")

    print(f"\n💾 Building and saving FAISS index...")
    store = VectorStore(store_path=config["vector_store_path"])
    store.add(embeddings, chunks)
    store.save()
    print(f"   ✓ Vector store saved to {config['vector_store_path']}")

    print(f"\n✅ Ingestion complete!")
    print(f"   Documents: {len(documents)}")
    print(f"   Chunks: {len(chunks)}")
    print(f"   Vectors: {store.total_chunks}")
    print(f"\n👉 Start the web app: python app.py")


def cmd_query(args):
    """Answer a question from the command line."""
    from core.vector_store import VectorStore
    from core.retriever import Retriever
    from core.agent import DocumentAgent

    config = get_config()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)

    if not VectorStore.exists(config["vector_store_path"]):
        print(f"❌ No vector store found. Run: python main.py ingest")
        sys.exit(1)

    store = VectorStore.load(config["vector_store_path"])
    retriever = Retriever(store, top_k=config["top_k"])
    agent = DocumentAgent(retriever, top_k=config["top_k"])

    question = args.question
    print(f"\n❓ Question: {question}")
    print("-" * 60)

    result = agent.answer(question)

    print(f"\n📝 Answer:\n{result['answer']}")

    if result["sources"]:
        print(f"\n📚 Sources:")
        for src in result["sources"]:
            print(f"   • {src}")

    if args.verbose and result["chunks"]:
        print(f"\n🔍 Retrieved chunks:")
        for i, chunk in enumerate(result["chunks"], 1):
            print(f"\n  Chunk {i}: {chunk['filename']} (similarity: {chunk['similarity']:.2%})")
            print(f"  {chunk['text'][:200]}...")


def cmd_stats(args):
    """Show vector store statistics."""
    from core.vector_store import VectorStore

    config = get_config()

    if not VectorStore.exists(config["vector_store_path"]):
        print(f"❌ No vector store found at {config['vector_store_path']}")
        print("   Run: python main.py ingest")
        return

    store = VectorStore.load(config["vector_store_path"])

    print(f"\n📊 Vector Store Statistics")
    print(f"   Path: {config['vector_store_path']}")
    print(f"   Total vectors: {store.total_chunks:,}")

    # Count unique documents
    filenames = set(m["filename"] for m in store.metadata)
    print(f"   Unique documents: {len(filenames)}")
    for fn in sorted(filenames):
        count = sum(1 for m in store.metadata if m["filename"] == fn)
        print(f"     • {fn}: {count} chunks")


def cmd_serve(args):
    """Start the FastAPI web server."""
    import uvicorn
    host = args.host or "0.0.0.0"
    port = args.port or 8000
    print(f"\n🚀 Starting server on http://{host}:{port}")
    print(f"   Local:   http://localhost:{port}")
    print(f"   Network: http://<your-ip>:{port}  (access from mobile on same WiFi)")
    uvicorn.run("app:app", host=host, port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(
        description="Private Document Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ingest                       # Ingest ./data/documents/
  python main.py ingest --path /my/docs       # Ingest custom path
  python main.py query "What is the policy?"  # Ask a question
  python main.py query "..." --verbose        # Show retrieved chunks too
  python main.py stats                        # Show index stats
  python main.py serve                        # Start web server
  python main.py serve --port 8080            # Custom port
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Load documents and build vector store")
    p_ingest.add_argument("--path", help="Path to documents folder (overrides .env)")

    # query
    p_query = subparsers.add_parser("query", help="Ask a question from the command line")
    p_query.add_argument("question", help="The question to ask")
    p_query.add_argument("--verbose", "-v", action="store_true", help="Show retrieved chunks")

    # stats
    subparsers.add_parser("stats", help="Show vector store statistics")

    # serve
    p_serve = subparsers.add_parser("serve", help="Start the web server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
