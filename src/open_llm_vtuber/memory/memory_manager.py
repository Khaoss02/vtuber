"""
MemoryManager
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
• EpisodicMemoryManager  – chronological log (JSON)
• SemanticMemoryManager  – pgvector‑backed embedding search
• SummaryMemoryManager   – periodic summaries + profile
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from open_llm_vtuber.memory.episodic_memory import EpisodicMemoryManager
from open_llm_vtuber.memory.semantic_memory import SemanticMemoryManager
from open_llm_vtuber.memory.summary_memory import SummaryMemoryManager


class MemoryManager:
    def __init__(
        self,
        episodic_path: str = "src/open_llm_vtuber/data/episodic_memory.json",
        semantic_path: str = "src/open_llm_vtuber/data/semantic_memory.json",
        semantic_emb_path: str = "src/open_llm_vtuber/data/semantic_embeddings.pt",
        summary_path: str = "src/open_llm_vtuber/data/summary_memory.json",
        summary_every: int = 20,
        summary_level2: int = 5,
    ) -> None:
        self.episodic = EpisodicMemoryManager(file_path=episodic_path)
        self.semantic = SemanticMemoryManager(
            file_path=semantic_path,
            emb_path=semantic_emb_path,
        )
        self.summary = SummaryMemoryManager(
            episodic_memory=self.episodic.episodes,
            file_path=summary_path,
            level1_window=summary_every,
            level2_window=summary_level2,
        )

    # ------------------------------------------------------------------ #
    # Write
    # ------------------------------------------------------------------ #
    def save_episode(self, episode: Dict) -> None:
        """Store episode in episodic, semantic and summary memories."""
        ui = episode["user_input"]
        ai = episode["ai_response"]
        ctx = episode.get("context")

        # episodic
        self.episodic.save_episode(ui, ai, ctx)

        # semantic (embed last)
        last = self.episodic.get_last_n(1)[0]
        self.semantic.add_episode(last)

        # summary
        self.summary.episodic_memory = self.episodic.episodes
        self.summary.add_summary()

    # ------------------------------------------------------------------ #
    # Read helpers
    # ------------------------------------------------------------------ #
    def get_last_n(self, n: int = 5) -> List[Dict]:
        return self.episodic.get_last_n(n)

    def semantic_search(self, text: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        return self.semantic.query(text, top_k=top_k)

    def latest_summary(self) -> Optional[str]:
        return self.summary.get_latest_summary()

    def latest_profile(self) -> Optional[Dict]:
        return self.summary.get_latest_profile()

    # ------------------------------------------------------------------ #
    # Reset
    # ------------------------------------------------------------------ #
    def clear_all(self) -> None:
        self.episodic.clear_memory()
        self.semantic.clear_memory()
        self.summary.clear_memory()
