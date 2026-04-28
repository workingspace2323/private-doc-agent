def chunk_documents(docs, chunk_size=800, chunk_overlap=100):
    chunks = []

    for doc in docs:
        try:
            # FIX: support multiple keys safely
            text = doc.get("text") or doc.get("content") or ""

            if not text:
                continue

            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk = text[i:i + chunk_size]

                chunks.append({
                    "text": chunk,
                    "source": doc.get("source", "unknown")
                })

        except Exception as e:
            print(f"Failed to chunk document: {e}")

    return chunks