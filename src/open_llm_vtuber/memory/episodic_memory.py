import json, os
from datetime import datetime
from typing import Dict, List, Optional

class EpisodicMemoryManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.episodes: List[Dict] = self._load()

    def save_episode(self, user_input: str, ai_response: str, context: Optional[Dict]=None):
        ep = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
            "context": context or {}
        }
        self.episodes.append(ep)
        self._save()

    def get_last_n(self, n=5) -> List[Dict]:
        return self.episodes[-n:]

    def clear_memory(self):
        self.episodes = []
        self._save()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                return json.load(open(self.file_path, "r", encoding="utf-8"))
            except:
                os.rename(self.file_path, self.file_path + ".broken")
        return []

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        json.dump(self.episodes, open(self.file_path, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
