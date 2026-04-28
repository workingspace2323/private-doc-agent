#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — One-command launcher for the Private Document Agent
# Usage: ./start.sh [--port 8000] [--ingest]
# ─────────────────────────────────────────────────────────────────────────────

set -e

PORT=8000
DO_INGEST=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift ;;
    --ingest) DO_INGEST=true ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
  shift
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🔒 Private Document Agent          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo -e "${RED}❌ Python not found. Install Python 3.10+${NC}"
  exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo -e "   Python: $($PYTHON --version)"

# ── Check/create venv ─────────────────────────────────────────────────────────
if [ ! -d "venv" ]; then
  echo -e "\n${YELLOW}📦 Creating virtual environment...${NC}"
  $PYTHON -m venv venv
fi

source venv/bin/activate
echo -e "   Venv: activated"

# ── Install dependencies ──────────────────────────────────────────────────────
if ! python -c "import fastapi" &>/dev/null; then
  echo -e "\n${YELLOW}📥 Installing dependencies (first run only)...${NC}"
  pip install -r requirements.txt -q
  echo -e "${GREEN}   ✓ Dependencies installed${NC}"
fi

# ── Check .env ────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo -e "\n${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
  cp .env.example .env
  echo -e "${RED}   ❗ Edit .env and add your ANTHROPIC_API_KEY before continuing.${NC}"
  echo -e "   Run: nano .env"
  exit 1
fi

source .env
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
  echo -e "\n${RED}❌ ANTHROPIC_API_KEY not set in .env${NC}"
  echo -e "   Edit .env and add your key from https://console.anthropic.com/"
  exit 1
fi
echo -e "   API key: ✓"

# ── Check documents ───────────────────────────────────────────────────────────
DOCS_PATH="${DOCUMENTS_PATH:-./data/documents}"
mkdir -p "$DOCS_PATH"

DOC_COUNT=$(find "$DOCS_PATH" -name "*.pdf" -o -name "*.docx" -o -name "*.txt" -o -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo -e "   Documents found: $DOC_COUNT"

# ── Ingest if needed ──────────────────────────────────────────────────────────
VS_PATH="${VECTOR_STORE_PATH:-./data/vectorstore}"

if [ "$DO_INGEST" = true ] || [ ! -f "$VS_PATH/index.faiss" ]; then
  if [ "$DOC_COUNT" -eq 0 ]; then
    echo -e "\n${YELLOW}⚠️  No documents found in $DOCS_PATH${NC}"
    echo -e "   Add your PDF/DOCX/TXT files to: $DOCS_PATH"
    echo -e "   Sample documents are already there to test with."
  fi
  echo -e "\n${YELLOW}📚 Running document ingestion...${NC}"
  python main.py ingest
  echo -e "${GREEN}   ✓ Ingestion complete${NC}"
else
  echo -e "   Vector store: ✓ (already built)"
fi

# ── Get local IP ─────────────────────────────────────────────────────────────
LOCAL_IP=$(python -c "import socket; s=socket.socket(); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "YOUR_IP")

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🚀 Starting server...                       ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Local:   http://localhost:${PORT}              ║${NC}"
echo -e "${GREEN}║  Mobile:  http://${LOCAL_IP}:${PORT}           ║${NC}"
echo -e "${GREEN}║  (Phone must be on same WiFi)                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Launch server ─────────────────────────────────────────────────────────────
exec uvicorn app:app --host 0.0.0.0 --port "$PORT" --log-level info
