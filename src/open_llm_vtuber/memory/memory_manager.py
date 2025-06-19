from typing import Dict, List, Optional, Tuple
from open_llm_vtuber.memory.episodic_memory import EpisodicMemoryManager
from open_llm_vtuber.memory.semantic_memory import SemanticMemoryManager
from open_llm_vtuber.memory.summary_memory import SummaryMemoryManager

class MemoryManager:
    def __init__(self,
                 episodic_path: str,
                 semantic_path: str,
                 semantic_emb_path: str,
                 summary_path: str,
                 summary_every: int = 20,
                 summary_level2: int = 5):
        self.episodic = EpisodicMemoryManager(file_path=episodic_path)
        self.semantic= SemanticMemoryManager(file_path=semantic_path, emb_path=semantic_emb_path)
        self.summary = SummaryMemoryManager(
            episodic_memory=self.episodic.episodes,
            file_path=summary_path,
            level1_window=summary_every,
            level2_window=summary_level2
        )

    def save_episode(self, episode: Dict):
        ui, ai = episode["user_input"], episode["ai_response"]
        ctx = episode.get("context")
        self.episodic.save_episode(ui, ai, ctx)
        last = self.episodic.get_last_n(1)[0]
        self.semantic.add_episode(last)
        self.summary.episodic_memory = self.episodic.episodes
        self.summary.add_summary()

    def get_last_n(self, n=5) -> List[Dict]:
        return self.episodic.get_last_n(n)

    def semantic_search(self, text: str, top_k=5) -> List[Tuple[Dict,float]]:
        return self.semantic.query(text, top_k=top_k)

    def latest_summary(self) -> Optional[str]:
        return self.summary.get_latest_summary()

    def latest_profile(self) -> Optional[Dict]:
        return self.summary.get_latest_profile()

    def clear_all(self):
        self.episodic.clear_memory()
        self.semantic.clear_memory()
        self.summary.clear_memory()
