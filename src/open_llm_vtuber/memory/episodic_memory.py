"""Episodic Memory Manager
Stores every user–AI exchange as an "episode" with timestamp and optional
context metadata, writing everything to disk so it persists between
sessions.  Embeddings/retrieval will be added in later modules.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class EpisodicMemoryManager:
    """Light‑weight long‑term memory buffer persisted to a JSON file.

    Each episode has the structure::
        {
            "timestamp": "2025-06-18T05:44:11.123456",
            "user_input": "...",
            "ai_response": "...",
            "context": {"mood": "happy", "session_id": "xyz"}
        }
    """

    def __init__(self, file_path: str = "src/open_llm_vtuber/data/episodic_memory.json") -> None:
        self.file_path = file_path
        # Load existing memory or start with an empty list
        self.episodes: List[Dict] = self._load_memory()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def save_episode(
        self,
        user_input: str,
        ai_response: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Save one interaction (episode) to memory and disk."""
        episode = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
            "context": context or {},
        }
        self.episodes.append(episode)
        self._save_to_disk()

    def get_last_n(self, n: int = 5) -> List[Dict]:
        """Return the last *n* episodes (default 5)."""
        return self.episodes[-n:]

    def search_memory(self, keyword: str, /) -> List[Dict]:
        """Naïve keyword search over user_input and ai_response fields."""
        kw = keyword.lower()
        return [ep for ep in self.episodes if kw in ep["user_input"].lower() or kw in ep["ai_response"].lower()]

    def clear_memory(self) -> None:
        """**Erase** all stored episodes and overwrite the on‑disk file.

        ⚠️  Use with care: this wipes the bot's entire episodic history.
        """
        self.episodes = []
        self._save_to_disk()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_memory(self) -> List[Dict]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Corrupted file → start fresh but keep a backup
                os.rename(self.file_path, self.file_path + ".broken")
        # No file or bad contents → start empty list
        return []

    def _save_to_disk(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)