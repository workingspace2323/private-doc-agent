"""
utils/helpers.py
----------------
Shared utility functions used across the project.
"""

import os
import sys
import socket
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """
    Detect the machine's local network IP address.
    Returns '127.0.0.1' if detection fails.
    """
    try:
        # Connect to an external host (doesn't actually send data)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def check_environment() -> dict:
    """
    Validate that the environment is properly configured.
    Returns a dict of check results.
    """
    checks = {}

    # Python version
    ver = sys.version_info
    checks["python_ok"] = ver >= (3, 10)
    checks["python_version"] = f"{ver.major}.{ver.minor}.{ver.micro}"

    # API key
    checks["api_key_set"] = bool(os.getenv("ANTHROPIC_API_KEY"))

    # Documents folder
    doc_path = Path(os.getenv("DOCUMENTS_PATH", "./data/documents"))
    checks["docs_folder_exists"] = doc_path.exists()
    if doc_path.exists():
        supported = {".pdf", ".docx", ".txt", ".md"}
        doc_files = [f for f in doc_path.rglob("*") if f.suffix.lower() in supported]
        checks["doc_count"] = len(doc_files)
    else:
        checks["doc_count"] = 0

    # Vector store
    vs_path = Path(os.getenv("VECTOR_STORE_PATH", "./data/vectorstore"))
    checks["vector_store_exists"] = (
        (vs_path / "index.faiss").exists() and (vs_path / "metadata.json").exists()
    )

    # Key packages
    for pkg in ["faiss", "anthropic", "sentence_transformers", "langchain", "fastapi"]:
        try:
            __import__(pkg.replace("-", "_"))
            checks[f"pkg_{pkg}"] = True
        except ImportError:
            checks[f"pkg_{pkg}"] = False

    return checks


def print_startup_banner(host: str, port: int) -> None:
    """Print a nice startup banner with local and network URLs."""
    local_ip = get_local_ip()
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║         🔒  Private Document Agent               ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  Local:    http://localhost:{port:<21}║")
    print(f"║  Network:  http://{local_ip}:{port:<20}║")
    print("║                                                  ║")
    print("║  📱 Mobile: open Network URL on phone           ║")
    print("║     (same WiFi required)                         ║")
    print("╚══════════════════════════════════════════════════╝")
    print()


def format_file_size(num_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
