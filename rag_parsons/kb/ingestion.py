from __future__ import annotations

import uuid
import warnings
from pathlib import Path

from pypdf import PdfReader

from rag_parsons.kb.vectorstore import VectorStore

_MAX_PAGES = 200
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


def load_pdfs(livros_dir: str) -> list[Path]:
    path = Path(livros_dir)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {livros_dir}")
    pdfs = sorted(path.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in: {livros_dir}")
    return pdfs


def extract_text(pdf_path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    total = len(reader.pages)
    if total > _MAX_PAGES:
        warnings.warn(
            f"{pdf_path.name} has {total} pages (limit {_MAX_PAGES}). "
            f"Only first {_MAX_PAGES} pages will be indexed.",
            stacklevel=2,
        )
    for i, page in enumerate(reader.pages[:_MAX_PAGES]):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append((i + 1, text))
    return pages


def chunk_text(
    page_num: int,
    text: str,
    source: str,
    chunk_size: int = _CHUNK_SIZE,
    overlap: int = _CHUNK_OVERLAP,
) -> list[dict]:
    words = text.split()
    chunks: list[dict] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)
        chunks.append(
            {
                "id": str(uuid.uuid4()),
                "text": chunk_text_str,
                "source": source,
                "page": page_num,
            }
        )
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def ingest_all(livros_dir: str, vector_store: VectorStore) -> int:
    pdfs = load_pdfs(livros_dir)
    total_chunks = 0
    for pdf_path in pdfs:
        pages = extract_text(pdf_path)
        chunks: list[dict] = []
        for page_num, text in pages:
            chunks.extend(chunk_text(page_num, text, pdf_path.name))
        if chunks:
            vector_store.upsert_chunks(chunks)
            total_chunks += len(chunks)
        print(f"  {pdf_path.name} — {len(chunks)} chunks")
    return total_chunks
