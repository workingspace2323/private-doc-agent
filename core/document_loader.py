from pathlib import Path
from docx import Document
from pypdf import PdfReader

def load_documents_from_folder(folder_path):
    docs = []

    folder = Path(folder_path)

    for file_path in folder.glob("*"):
        try:
            ext = file_path.suffix.lower()

            text = ""

            if ext == ".txt":
                text = file_path.read_text(errors="ignore")

            elif ext == ".docx":
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])

            elif ext == ".pdf":
                reader = PdfReader(file_path)
                text = "\n".join([page.extract_text() or "" for page in reader.pages])

            else:
                continue

            docs.append({
                "text": text,
                "source": file_path.name
            })

        except Exception as e:
            print(f"Failed to load {file_path.name}: {e}")

    return docs