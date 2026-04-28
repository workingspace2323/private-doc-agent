import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.document_loader import load_documents_from_folder
from core.chunking import chunk_documents
from core.embeddings import embed_texts
from core.vector_store import VectorStore
from core.llm import ask_llm


# ---------------- APP ----------------
app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_PATH = BASE_DIR / "data" / "documents"
VECTOR_PATH = BASE_DIR / "data" / "vectorstore"

DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)
VECTOR_PATH.mkdir(parents=True, exist_ok=True)

# ---------------- STATIC ----------------
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


# ---------------- FILE LIST ----------------
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

    embeddings = embed_texts(texts)

    store = VectorStore(str(VECTOR_PATH))
    store.build(embeddings, chunks)
    store.save()

    return {"status": "index_ready", "chunks": len(chunks)}


# ---------------- QUERY ----------------
@app.post("/api/query")
async def query(
    question: str = Form(...),
    filename: str = Form(default="")
):

    store = VectorStore(str(VECTOR_PATH))

    if not store.exists():
        return {"answer": "Index not built yet"}

    store.load()

    query_vec = embed_texts([question])[0]
    results = store.search(query_vec, k=3)

    if not results:
        return {"answer": "No relevant data found"}

    context = "\n\n".join([r.get("text", "") for r in results])
    answer = ask_llm(question, context)

    return {"answer": answer}


# ---------------- DELETE FILE (FINAL WORKING VERSION) ----------------
@app.delete("/api/delete")
def delete_file(filename: str = Query(...)):

    safe_name = Path(filename).name
    file_path = DOCUMENTS_PATH / safe_name

    print("\n[DELETE REQUEST]", safe_name)
    print("[FULL PATH]", file_path)
    print("[EXISTS]", file_path.exists())

    if not file_path.exists():
        return {"error": "file not found", "file": safe_name}

    try:
        file_path.unlink()
        print("[DELETED SUCCESSFULLY]", file_path)

        return {
            "status": "deleted",
            "file": safe_name
        }

    except Exception as e:
        return {"error": str(e)}