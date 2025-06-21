import json
import os
import torch
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer, util


class SemanticMemoryManager:
    def __init__(self, file_path: str, emb_path: str, model_name="all-MiniLM-L6-v2"):
        self.file_path = file_path
        self.emb_path = emb_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Carga segura sin usar .to(device) si no es necesario
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device="cpu")  # o "cuda" si tienes GPU compatible

        try:
            self.model = self.model.to(self.device)
        except NotImplementedError:
            # fallback en caso de error por meta tensor
            print("⚠️ Warning: El modelo de embeddings no puede moverse al dispositivo. Se usará en CPU.")
            self.model = self.model.to("cpu")

        self.episodes: List[Dict] = []
        self.embeddings: torch.Tensor = None
        self._load()

    def add_episode(self, episode: Dict):
        txt = f"{episode['user_input']} {episode['ai_response']}"
        emb = self.model.encode(txt, convert_to_tensor=True, normalize_embeddings=True)
        if self.embeddings is None:
            self.embeddings = emb.unsqueeze(0)
        else:
            self.embeddings = torch.vstack([self.embeddings, emb])
        self.episodes.append(episode)
        self._save()

    def query(self, text: str, top_k=5) -> List[Tuple[Dict, float]]:
        if not self.episodes or self.embeddings is None:
            return []
        q = self.model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
        hits = util.semantic_search(q, self.embeddings, top_k=top_k)[0]
        return [(self.episodes[h["corpus_id"]], float(h["score"])) for h in hits]

    def clear_memory(self):
        self.episodes = []
        self.embeddings = None
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        if os.path.exists(self.emb_path):
            os.remove(self.emb_path)

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.episodes = json.load(f)
            except Exception:
                self.episodes = []

        if os.path.exists(self.emb_path):
            try:
                self.embeddings = torch.load(self.emb_path)
            except Exception:
                self.embeddings = None

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)
        if self.embeddings is not None:
            torch.save(self.embeddings, self.emb_path)
