import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SummaryMemoryManager:
    def __init__(
        self,
        episodic_memory: List[Dict],
        file_path: str,
        model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct",
        temperature: float = 0.3,
        level1_window: int = 20,
        level2_window: int = 5,
    ):
        # Import local para evitar ciclos
        from open_llm_vtuber.agent.chat_hf_local import HFLocalChat

        self.file_path = file_path
        self.model = HFLocalChat(model_name=model_name)
        self.episodic_memory = episodic_memory
        self.level1_window = level1_window
        self.level2_window = level2_window
        self.summary_entries: List[Dict] = []
        self._load()

    def add_summary(self):
        cnt = len(self.episodic_memory)
        if cnt < self.level1_window:
            return
        recent = self.episodic_memory[-self.level1_window:]
        content = "\n\n".join(
            f"User: {e['user_input']}\nAI: {e['ai_response']}" for e in recent
        )
        prompt_base = content + "\n\n"
        try:
            # Generar resumen
            summary = self.model.chat(f"Resumen:\n\n{prompt_base}")
            # Generar etiquetas
            tags_text = self.model.chat(f"Etiquetas:\n\n{prompt_base}")
            tags = [t.strip() for t in tags_text.split(",") if t.strip()]
            # Análisis de sentimiento
            sentiment = self.model.chat(f"Sentimiento:\n\n{prompt_base}")
            # Extraer preguntas
            questions_text = self.model.chat(f"Preguntas:\n\n{prompt_base}")
            questions = [q.strip() for q in questions_text.splitlines() if q.strip()]

            e1 = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": 1,
                "episodes": cnt,
                "summary": summary,
                "tags": tags,
                "sentiment": sentiment,
                "unanswered_questions": questions,
            }
            self.summary_entries.append(e1)

            lvl1 = [x for x in self.summary_entries if x["level"] == 1]
            if len(lvl1) % self.level2_window == 0:
                over = "\n".join(f"- {x['summary']}" for x in lvl1[-self.level2_window:])
                ov = self.model.chat(f"Visión general:\n\n{over}")
                e2 = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": 2,
                    "summaries_level1": len(lvl1),
                    "overview": ov,
                }
                self.summary_entries.append(e2)

            self._save()
        except Exception as err:
            logger.error("Error en add_summary: %s", err)

    def get_latest_summary(self) -> Optional[str]:
        lvl1 = [x for x in self.summary_entries if x["level"] == 1]
        return lvl1[-1]["summary"] if lvl1 else None

    def get_latest_profile(self) -> Optional[Dict]:
        lvl1_summaries = [x["summary"] for x in self.summary_entries if x["level"] == 1]
        if not lvl1_summaries:
            return None
        prompt = "Perfil:\n" + "\n".join(f"- {s}" for s in lvl1_summaries)
        try:
            profile_text = self.model.chat(prompt)
            return {"timestamp": datetime.utcnow().isoformat(), "profile": profile_text}
        except Exception as err:
            logger.error("Error en get_latest_profile: %s", err)
            return None

    def clear_memory(self):
        self.summary_entries = []
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                self.summary_entries = json.load(
                    open(self.file_path, "r", encoding="utf-8")
                )
            except Exception:
                os.rename(self.file_path, self.file_path + ".broken")
                self.summary_entries = []

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.summary_entries, f, indent=2, ensure_ascii=False)
