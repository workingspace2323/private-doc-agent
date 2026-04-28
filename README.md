# 🔒 Private Document Agent

A fully local, private AI agent that answers questions **exclusively** from your confidential documents.
No document content ever leaves your machine (only the question + retrieved excerpts go to Claude API).

---

## 📁 Folder Structure

```
private-doc-agent/
├── core/
│   ├── __init__.py
│   ├── document_loader.py   ← Loads PDF, DOCX, TXT, MD files
│   ├── chunking.py          ← Splits docs into overlapping chunks
│   ├── embeddings.py        ← Local sentence-transformer embeddings
│   ├── vector_store.py      ← FAISS index (save/load/search)
│   ├── retriever.py         ← Retrieves top-k relevant chunks
│   └── agent.py             ← LangChain RAG agent (Claude API)
├── data/
│   ├── documents/           ← PUT YOUR DOCUMENTS HERE
│   └── vectorstore/         ← Auto-created FAISS index
├── static/
│   ├── index.html           ← Mobile-first chat UI
│   ├── manifest.json        ← PWA manifest
│   └── service-worker.js   ← PWA offline support
├── utils/
│   └── __init__.py
├── app.py                   ← FastAPI backend
├── main.py                  ← CLI entrypoint
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup Guide (Step by Step)

### Step 1: Prerequisites

- Python 3.10 or 3.11 (recommended)
- Git (optional)
- ~2GB free disk space (for the embedding model)

Check your Python version:
```bash
python --version
```

### Step 2: Create a virtual environment

```bash
# Create the environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

This will install FastAPI, FAISS, LangChain, sentence-transformers, Anthropic SDK, and other packages.
The first run downloads the `all-MiniLM-L6-v2` embedding model (~90MB) automatically.

### Step 4: Set up your API key

```bash
# Copy the example env file
cp .env.example .env

# Open .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxx
```

Get your API key from: https://console.anthropic.com/

### Step 5: Add your documents

Place your PDF, DOCX, TXT, or MD files in `data/documents/`:
```bash
cp /path/to/your/document.pdf data/documents/
cp /path/to/your/report.docx  data/documents/
# ... add as many as needed, even 2000+ page PDFs work
```

The system is already set up with two sample documents to test with.

### Step 6: Ingest documents

```bash
python main.py ingest
```

This will:
1. Load all documents from `data/documents/`
2. Split them into ~800-word overlapping chunks
3. Create local embeddings (runs entirely on your CPU)
4. Build and save the FAISS vector index

For 2000+ page documents, this may take 5-20 minutes on first run.
The vector store is cached — re-ingestion is only needed when you add new documents.

---

## 🚀 Running the App

### Start the web server

```bash
python app.py
```

OR

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

You'll see:
```
🔒 Private Document Agent
  Local:  http://localhost:8000
  Mobile: http://192.168.1.x:8000
```

Open http://localhost:8000 in your browser.

### CLI usage (no browser needed)

```bash
# Ask a single question
python main.py query "What is the annual leave entitlement?"

# With verbose chunk output
python main.py query "What is the project budget?" --verbose

# See statistics
python main.py stats
```

---

## 📱 Mobile Access (Option A — Recommended)

### Access on Android or iPhone via WiFi

1. Make sure your phone is on the **same WiFi** as your computer.
2. Start the server: `python app.py`
3. Note the "Mobile" URL shown at startup (e.g., `http://192.168.1.42:8000`)
4. Open that URL in your phone's browser (Chrome on Android, Safari on iPhone).

**Finding your IP manually:**
```bash
# Linux/macOS:
hostname -I
# OR
ifconfig | grep "inet "

# Windows:
ipconfig | findstr "IPv4"
```

### Install as PWA (Option C — Looks Like a Native App)

**On Android (Chrome):**
1. Open `http://YOUR_IP:8000` in Chrome
2. Tap the **⋮ menu** (top right)
3. Tap **"Add to Home screen"** or **"Install app"**
4. Tap **"Install"**
5. The app appears on your home screen like a native app ✓

**On iPhone (Safari):**
1. Open `http://YOUR_IP:8000` in Safari
2. Tap the **Share button** (box with arrow)
3. Tap **"Add to Home Screen"**
4. Tap **"Add"**
5. App icon appears on your home screen ✓

PWA features included:
- Offline UI caching (the chat interface loads without internet)
- Full-screen mode (no browser chrome)
- Home screen icon
- Splash screen

---

## 📦 Convert to APK (Option B — Android App)

This wraps the web UI into a native Android APK using WebView.

### Method 1: Using Bubblewrap (Google's official PWA-to-APK tool)

Prerequisites: Node.js 16+, Android SDK, Java 11+

```bash
# Install Bubblewrap CLI
npm install -g @bubblewrap/cli

# Initialize (answer the prompts — use your computer's local IP)
bubblewrap init --manifest http://YOUR_LOCAL_IP:8000/static/manifest.json

# Build the APK
bubblewrap build
```

The generated `app-release-unsigned.apk` can be installed on any Android device
with "Install from unknown sources" enabled.

### Method 2: Using WebIntoApp.com (Easiest, no code)

1. Ensure your server has a public URL (use ngrok: `ngrok http 8000`)
2. Copy the public URL (e.g., `https://abc123.ngrok.io`)
3. Go to https://webintoapp.com
4. Paste the URL → configure app name "DocAgent"
5. Download the generated APK
6. Install on Android phone (enable "Unknown sources" in Settings → Security)

### Method 3: Using ngrok + any PWA-to-APK converter

```bash
# Install ngrok (https://ngrok.com/download)
# Then expose your local server:
ngrok http 8000

# Use the https URL with any of these services:
# - https://pwabuilder.com (Microsoft, free, recommended)
# - https://appmaker.xyz
# - https://webintoapp.com
```

**Installing the APK on Android:**
1. Copy the APK to your phone (email, WhatsApp, USB, etc.)
2. Open the APK file on your phone
3. If prompted, go to Settings → Security → Enable "Install unknown apps" for your file manager
4. Tap "Install" and confirm

---

## 🔍 Example Queries to Test

Using the sample documents included:

```
"How many days of annual leave do employees get?"
"What is the notice period after probation?"
"What is the Project Alpha budget?"
"Who is the Tech Lead for Project Alpha?"
"When is the go-live date for Project Alpha?"
"What programming language is used for the backend?"
"How much is the learning budget per employee?"
"What encryption standard is used for data at rest?"
```

An out-of-scope query (to test the "not found" behaviour):
```
"What is the capital of France?"
→ Expected: "Answer not found in documents."
```

---

## 🛠️ Configuration Options (.env)

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `VECTOR_STORE_PATH` | `./data/vectorstore` | Where the FAISS index is saved |
| `DOCUMENTS_PATH` | `./data/documents` | Where to look for documents |
| `CHUNK_SIZE` | `3200` | Characters per chunk (~800 words) |
| `CHUNK_OVERLAP` | `400` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |

**Tuning tips:**
- Larger `CHUNK_SIZE` → more context per chunk, but fewer chunks retrieved
- Higher `TOP_K_RESULTS` → more context for Claude, but slower and more tokens
- For technical/legal docs: increase `TOP_K_RESULTS` to 7-10

---

## 🏗️ Architecture Decisions

| Decision | Choice | Why |
|---|---|---|
| **Framework** | LangChain | Better streaming, Anthropic-native, flexible prompt templates |
| **Vector DB** | FAISS | No server needed, pure file-based, handles millions of vectors |
| **Embeddings** | sentence-transformers (local) | Documents are confidential — no remote embedding API |
| **LLM** | Anthropic Claude | Best instruction-following, strong at "answer only from context" |
| **Frontend** | FastAPI + vanilla HTML | No build step, works on any device, easy PWA conversion |
| **Mobile** | PWA + WebView APK | No app store needed, works on both Android and iOS |

---

## 🔒 Privacy Architecture

```
Your Documents → Local Chunking → Local Embeddings (CPU)
                                         ↓
                                   FAISS on disk
                                         ↓
User Query → Embed Query (local) → Find top-5 chunks (local)
                                         ↓
                              [Chunk texts + Question] → Claude API
                                         ↓
                                      Answer
```

**What leaves your machine:** Only the question text + the top-5 retrieved chunk texts.
**What stays local:** All documents, all embeddings, the full vector index.

---

## ❓ Troubleshooting

**"No vector store found"**
→ Run `python main.py ingest` first.

**"ANTHROPIC_API_KEY not set"**
→ Copy `.env.example` to `.env` and add your key.

**Phone can't connect to server**
→ Ensure both devices are on the same WiFi. Check firewall settings.
→ Try: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`

**PDF text not extracting**
→ Some PDFs are image-based scans. Use OCR tools like Adobe Acrobat or `ocrmypdf` to convert them first:
→ `pip install ocrmypdf && ocrmypdf input.pdf output.pdf`

**Slow ingestion**
→ Normal for large documents. The embedding model runs on CPU.
→ If you have an NVIDIA GPU: `pip install faiss-gpu` and sentence-transformers uses CUDA automatically.

**"Answer not found" for questions that should match**
→ Lower the `MIN_SIMILARITY_THRESHOLD` in `core/retriever.py` (default 0.25)
→ Increase `TOP_K_RESULTS` in `.env`
