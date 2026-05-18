from __future__ import annotations

from rag_parsons.kb.vectorstore import VectorStore

_DEFAULT_N = 3
_MIN_N = 1
_MAX_N = 5


class Retriever:
    def __init__(self, vector_store: VectorStore) -> None:
        self._store = vector_store

    def get_context(self, n: int = _DEFAULT_N) -> list[str]:
        n = max(_MIN_N, min(_MAX_N, n))
        passages = self._store.random_sample(n)
        return passages
