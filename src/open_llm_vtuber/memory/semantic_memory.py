import json, os
import torch
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer, util

class SemanticMemoryManager:
    def __init__(self, file_path: str, emb_path: str, model_name="all-MiniLM-L6-v2"):
        self.file_path = file_path
        self.emb_path  = emb_path
        self.model     = SentenceTransformer(model_name)
        self.episodes: List[Dict] = []
        self.embeddings: torch.Tensor = None
        self._load()

    def add_episode(self, episode: Dict):
        txt = f"{episode['user_input']} {episode['ai_response']}"
        emb = self.model.encode(txt, convert_to_tensor=True, normalize_embeddings=True)
        self.embeddings = emb.unsqueeze(0) if self.embeddings is None else torch.vstack([self.embeddings, emb])
        self.episodes.append(episode)
        self._save()

    def query(self, text: str, top_k=5) -> List[Tuple[Dict, float]]:
        if not self.episodes:
            return []
        q = self.model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
        hits = util.semantic_search(q, self.embeddings, top_k=top_k)[0]
        return [(self.episodes[h["corpus_id"]], float(h["score"])) for h in hits]

    def clear_memory(self):
        self.episodes, self.embeddings = [], None
        if os.path.exists(self.file_path): os.remove(self.file_path)
        if os.path.exists(self.emb_path): os.remove(self.emb_path)

    def _load(self):
        if os.path.exists(self.file_path):
            self.episodes = json.load(open(self.file_path, "r", encoding="utf-8"))
        if os.path.exists(self.emb_path):
            self.embeddings = torch.load(self.emb_path)

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        json.dump(self.episodes, open(self.file_path, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        if self.embeddings is not None:
            torch.save(self.embeddings, self.emb_path)
