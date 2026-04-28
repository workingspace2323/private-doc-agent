import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.document_loader import load_documents_from_folder
from core.chunking import chunk_documents
from core.embeddings import embed_texts
from core.vector_store import VectorStore

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_PATH = BASE_DIR / "data" / "documents"
VECTOR_PATH = BASE_DIR / "data" / "vectorstore"

DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)
VECTOR_PATH.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------- UI ----------------
@app.get("/")
def home():
    return FileResponse("static/index.html")


# ---------------- UPLOAD ----------------
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    file_path = DOCUMENTS_PATH / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"message": "Uploaded", "file": file.filename}


# ---------------- LIST FILES ----------------
@app.get("/api/files")
def list_files():
    return {"files": os.listdir(DOCUMENTS_PATH)}


# ---------------- REBUILD INDEX ----------------
@app.get("/api/rebuild")
def rebuild_index():
    docs = load_documents_from_folder(str(DOCUMENTS_PATH))

    if not docs:
        return {"error": "No documents found"}

    chunks = chunk_documents(docs)
    texts = [c["text"] for c in chunks if "text" in c]

    try:
        embeddings = embed_texts(texts)
    except Exception as e:
        return {"error": f"Embedding failed: {str(e)}"}

    store = VectorStore(str(VECTOR_PATH))
    store.build(embeddings, chunks)
    store.save()

    return {"status": "index_ready", "chunks": len(chunks)}


# ---------------- QUERY ----------------
@app.post("/api/query")
async def query(question: str = Form(...), filename: str = Form(default="")):

    print("Query:", question)

    store = VectorStore(str(VECTOR_PATH))

    if not store.exists():
        return {"answer": "Index not built yet"}

    store.load()

    try:
        query_vec = embed_texts([question])[0]
        results = store.search(query_vec, k=3)

        if not results:
            return {"answer": "No relevant data found"}

        context = "\n\n".join([r["text"] for r in results if "text" in r])

        return {"answer": context[:1000]}

    except Exception as e:
        print("ERROR:", str(e))
        return {"answer": f"Error: {str(e)}"}


# ---------------- DELETE FILE ----------------
@app.delete("/api/delete")
def delete_file(filename: str = Query(...)):
    file_path = DOCUMENTS_PATH / filename

    if file_path.exists():
        file_path.unlink()
        return {"status": "deleted"}

    return {"error": "file not found"}