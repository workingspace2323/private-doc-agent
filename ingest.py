import os
from pathlib import Path

from core.document_loader import load_documents_from_folder
from core.chunking import chunk_documents
from core.embeddings import embed_texts
from core.vector_store import VectorStore

# ---------------- CONFIG ----------------
DOCUMENTS_PATH = "./data/documents"
VECTOR_STORE_PATH = "./data/vectorstore"

CHUNK_SIZE = 3200
CHUNK_OVERLAP = 400


def main():
    print("\n🚀 STARTING VECTOR INDEX BUILD...\n")

    # Ensure folder exists
    Path(DOCUMENTS_PATH).mkdir(parents=True, exist_ok=True)

    # 1. Load documents
    docs = load_documents_from_folder(DOCUMENTS_PATH)
    print(f"📄 Documents loaded: {len(docs)}")

    if not docs:
        print("❌ No documents found in data/documents/")
        return

    # 2. Chunk documents
    chunks = chunk_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"✂️ Chunks created: {len(chunks)}")

    if not chunks:
        print("❌ No chunks created")
        return

    # 3. Extract text
    texts = [c["text"] for c in chunks]

    # 4. Create embeddings
    embeddings = embed_texts(texts, show_progress=True)
    print(f"🧠 Embeddings created: {len(embeddings)}")

    # 5. Save vector store
    store = VectorStore(VECTOR_STORE_PATH)
    store.add(embeddings, chunks)
    store.save()

    print("\n✅ VECTOR INDEX READY!\n")


if __name__ == "__main__":
    main()