"""Semantic Memory Manager
Embeds past episodes and enables semantic search using SentenceTransformers.
Designed to enchufarse a EpisodicMemoryManager: cada vez que guardes un
episodio, llama a `semantic_memory.add_episode(episode)`.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

import torch
from sentence_transformers import SentenceTransformer, util


class SemanticMemoryManager:
    """Semantic retrieval layer on top of SentenceTransformers.

    Internamente mantiene:
    - `episodes`: lista de episodios (dicts del mismo esquema que EpisodicMemory)
    - `embeddings`: matriz torch con los vectores normalizados
    Para producción puedes migrar a FAISS/pgvector; la interfaz se mantiene.
    """

    def __init__(
        self,
        file_path: str = "src/open_llm_vtuber/data/semantic_memory.json",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
        emb_path: str = "src/open_llm_vtuber/data/semantic_embeddings.pt",  # 🔄 NUEVO
    ) -> None:
        self.file_path = file_path
        self.emb_path = emb_path                                  # 🔄 NUEVO
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(embedding_model_name, device=self.device)

        self.episodes: List[Dict] = []
        self.embeddings: torch.Tensor | None = None
        self._load_from_disk()                                    # Carga episodios + embeddings

    # ------------------------------------------------------------------ #
    #  API pública
    # ------------------------------------------------------------------ #

    def add_episode(self, episode: Dict) -> None:
        """Embebe y almacena un episodio."""
        text = f"{episode['user_input']} {episode['ai_response']}"
        emb = self.model.encode(text, convert_to_tensor=True, normalize_embeddings=True)

        self.embeddings = (
            emb.unsqueeze(0) if self.embeddings is None else torch.vstack([self.embeddings, emb])
        )
        self.episodes.append(episode)
        self._save_to_disk()                                      # Persiste episodios + embeddings

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Devuelve los *top‑k* episodios más similares (con score de similitud)."""
        if not self.episodes:
            return []

        q_emb = self.model.encode(query_text, convert_to_tensor=True, normalize_embeddings=True)
        hits = util.semantic_search(q_emb, self.embeddings, top_k=top_k)[0]
        # 🔄 DEVOLVEMOS EL SCORE ORIGINAL, SIN 1‑score
        return [(self.episodes[h["corpus_id"]], float(h["score"])) for h in hits]

    # ------------------------------------------------------------------ #
    #  Persistencia
    # ------------------------------------------------------------------ #

    def _load_from_disk(self) -> None:
        """Carga episodios y embeddings (si existen)."""
        # Episodios
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.episodes = json.load(f)
            except Exception:
                os.rename(self.file_path, self.file_path + ".broken")
                self.episodes = []

        # Embeddings
        if os.path.exists(self.emb_path):
            try:
                self.embeddings = torch.load(self.emb_path, map_location=self.device)
            except Exception:
                os.rename(self.emb_path, self.emb_path + ".broken")
                self.embeddings = None
        elif self.episodes:
            # Si faltan embeddings, los regeneramos y los guardamos
            texts = [f"{ep['user_input']} {ep['ai_response']}" for ep in self.episodes]
            self.embeddings = self.model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
            torch.save(self.embeddings, self.emb_path)

    def _save_to_disk(self) -> None:
        """Guarda episodios y embeddings."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        # Episodios
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)

        # Embeddings
        if self.embeddings is not None:
            torch.save(self.embeddings, self.emb_path)

    # ------------------------------------------------------------------ #
    #  Reset opcional (por si lo necesitas)
    # ------------------------------------------------------------------ #
    def clear_memory(self) -> None:
        """Borra episodios y embeddings."""
        self.episodes = []
        self.embeddings = None
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        if os.path.exists(self.emb_path):
            os.remove(self.emb_path)
