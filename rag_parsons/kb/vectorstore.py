from __future__ import annotations

import random

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

_COLLECTION_NAME = "indigenous_knowledge"
_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class VectorStore:
    def __init__(self, db_path: str = "chroma_db") -> None:
        self._client = chromadb.PersistentClient(path=db_path)
        self._ef = SentenceTransformerEmbeddingFunction(model_name=_EMBEDDING_MODEL)
        self._collection: chromadb.Collection | None = None

    def init_collection(self) -> None:
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._ef,
        )

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            self.init_collection()
        return self._collection  # type: ignore[return-value]

    def upsert_chunks(self, chunks: list[dict]) -> None:
        col = self._get_collection()
        col.upsert(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "page": c["page"]} for c in chunks],
        )

    def random_sample(self, n: int = 3) -> list[str]:
        col = self._get_collection()
        result = col.get(include=["documents"])
        documents: list[str] = result.get("documents") or []
        if not documents:
            return []
        k = min(n, len(documents))
        return random.sample(documents, k)

    def count(self) -> int:
        col = self._get_collection()
        return col.count()

    def get_sources(self) -> list[str]:
        col = self._get_collection()
        result = col.get(include=["metadatas"])
        metadatas: list[dict] = result.get("metadatas") or []
        return sorted({m["source"] for m in metadatas if "source" in m})

    def clear(self) -> None:
        try:
            self._client.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self._client.create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._ef,
        )
