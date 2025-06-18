"""
Summary Memory Manager v2
Genera y almacena:
- Resúmenes nivel 1 (cada level1_window episodios) con tags, sentimiento y preguntas pendientes.
- Resúmenes nivel 2 (cada level2_window resúmenes nivel 1) como meta‑resumen.
- Perfil dinámico basado en todos los resúmenes nivel 1.
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)

class SummaryMemoryManager:
    def __init__(
        self,
        episodic_memory: List[Dict],
        file_path: str = "src/open_llm_vtuber/data/summary_memory.json",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.3,
        level1_window: int = 20,
        level2_window: int = 5,
    ) -> None:
        self.file_path = file_path
        self.model = OpenAI(model_name=model_name, temperature=temperature)
        self.episodic_memory = episodic_memory
        self.level1_window = level1_window
        self.level2_window = level2_window
        # Almacena entradas de todos los niveles y perfiles
        self.summary_entries: List[Dict] = []
        self._load()

    def add_summary(self) -> None:
        """Genera nivel 1, etiquetas, sentimiento, preguntas, y nivel 2 cuando toca."""
        count = len(self.episodic_memory)
        if count < self.level1_window:
            return

        # Nivel 1: resumen de los últimos episodios
        recent = self.episodic_memory[-self.level1_window:]
        content = "\n\n".join(
            f"User: {ep['user_input']}\nAI: {ep['ai_response']}" for ep in recent
        )
        base_prompt = (
            "Resume la siguiente conversación entre un usuario y una IA. "
            "Destaca temas recurrentes, metas o datos importantes. "
            "Mantén humor inteligente y concisión.\n\n"
            f"{content}\n\n"
        )

        try:
            summary_text = self.model.complete(base_prompt + "Resumen:").text.strip()
            tags = [
                t.strip()
                for t in self.model.complete(base_prompt + "Extrae 5 etiquetas clave:").text.split(",")
            ]
            sentiment = self.model.complete(base_prompt + "Describe el tono emocional general:").text.strip()
            questions = [
                q.strip()
                for q in self.model.complete(base_prompt + "Identifica preguntas o temas sin respuesta:").text.split("\n")
                if q.strip()
            ]

            entry1 = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": 1,
                "episodes": count,
                "summary": summary_text,
                "tags": tags,
                "sentiment": sentiment,
                "unanswered_questions": questions,
            }
            self.summary_entries.append(entry1)
            logger.info("Level 1 summary created.")

            # Nivel 2: cada level2_window resúmenes nivel 1
            lvl1_entries = [e for e in self.summary_entries if e["level"] == 1]
            if len(lvl1_entries) % self.level2_window == 0:
                overviews = "\n\n".join(f"- {e['summary']}" for e in lvl1_entries[-self.level2_window:])
                overview_text = self.model.complete(
                    "Genera un meta‑resumen de estos resúmenes de conversación:\n\n"
                    f"{overviews}\n\nOverview:"
                ).text.strip()
                entry2 = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": 2,
                    "summaries_level1": len(lvl1_entries),
                    "overview": overview_text,
                }
                self.summary_entries.append(entry2)
                logger.info("Level 2 overview created.")

            # Guardar tras generar
            self._save()

        except Exception as e:
            logger.error("Error generando summary: %s", e)

    def get_latest_summary(self) -> Optional[str]:
        lvl1 = [e for e in self.summary_entries if e["level"] == 1]
        return lvl1[-1]["summary"] if lvl1 else None

    def get_latest_profile(self) -> Optional[Dict]:
        """Crea un perfil dinámico basado en todos los resúmenes nivel 1."""
        lvl1 = [e["summary"] for e in self.summary_entries if e["level"] == 1]
        if not lvl1:
            return None
        prompt = (
            "Basado en estos resúmenes de la personalidad del VTuber, "
            "crea un perfil conciso con valores, estilo y evolución:\n\n"
            + "\n".join(f"- {s}" for s in lvl1)
            + "\n\nPerfil:"
        )
        try:
            profile_text = self.model.complete(prompt).text.strip()
            return {"timestamp": datetime.utcnow().isoformat(), "profile": profile_text}
        except Exception as e:
            logger.error("Error generando profile: %s", e)
            return None

    def clear_memory(self) -> None:
        self.summary_entries = []
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def _load(self) -> None:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.summary_entries = json.load(f)
            except Exception:
                os.rename(self.file_path, self.file_path + ".broken")
                self.summary_entries = []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.summary_entries, f, indent=2, ensure_ascii=False)
