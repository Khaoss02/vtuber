# src/open_llm_vtuber/memory/memory_manager.py
from __future__ import annotations
import datetime
from pathlib import Path
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer

class MemoryManager:
    def __init__(self, db_path: str = "data/memory"):
        self.client = chromadb.PersistentClient(
            path="postgresql://postgres:vtuber@localhost:5432/postgres"
        )
        self.collection = self.client.get_or_create_collection("chat_memories")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.encode(texts, normalize_embeddings=True).tolist()

    def add_memory(self, role: str, text: str) -> None:
        summary = text[:200]  # placeholder; puedes cambiarlos por un resumen LLM
        meta = {"role": role, "timestamp": str(datetime.datetime.utcnow())}
        self.collection.add(
            documents=[summary],
            metadatas=[meta],
            ids=[f"{meta['timestamp']}_{role}"],
            embeddings=self._embed([summary]),
        )

    def retrieve(self, query: str, k: int = 4) -> List[str]:
        results = self.collection.query(
            query_embeddings=self._embed([query]),
            n_results=k,
        )
        return results["documents"][0] if results["documents"] else []
