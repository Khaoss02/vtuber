import json, os, logging
from datetime import datetime
from typing import List, Dict, Optional
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)

class SummaryMemoryManager:
    def __init__(self, episodic_memory: List[Dict], file_path: str,
                 model_name="gpt-4o-mini", temperature=0.3,
                 level1_window=20, level2_window=5):
        self.file_path       = file_path
        self.model           = OpenAI(model_name=model_name, temperature=temperature)
        self.episodic_memory = episodic_memory
        self.level1_window   = level1_window
        self.level2_window   = level2_window
        self.summary_entries: List[Dict] = []
        self._load()

    def add_summary(self):
        cnt = len(self.episodic_memory)
        if cnt < self.level1_window:
            return
        recent = self.episodic_memory[-self.level1_window:]
        content = "\n\n".join(f"User: {e['user_input']}\nAI: {e['ai_response']}" for e in recent)
        bp = content + "\n\n"
        try:
            summary = self.model.complete("Resume:\n\n"+bp).text.strip()
            tags     = [t.strip() for t in self.model.complete("Tags:\n\n"+bp).text.split(",")]
            sentiment= self.model.complete("Sentiment:\n\n"+bp).text.strip()
            questions= [q.strip() for q in self.model.complete("Questions:\n\n"+bp).text.split("\n") if q.strip()]
            e1 = {"timestamp": datetime.utcnow().isoformat(), "level":1,
                  "episodes":cnt, "summary":summary,
                  "tags":tags, "sentiment":sentiment, "unanswered_questions":questions}
            self.summary_entries.append(e1)

            lvl1 = [x for x in self.summary_entries if x["level"]==1]
            if len(lvl1) % self.level2_window == 0:
                over = "\n".join(f"- {x['summary']}" for x in lvl1[-self.level2_window:])
                ov = self.model.complete("Overview:\n\n"+over).text.strip()
                e2 = {"timestamp": datetime.utcnow().isoformat(),
                      "level":2, "summaries_level1":len(lvl1), "overview":ov}
                self.summary_entries.append(e2)

            self._save()
        except Exception as err:
            logger.error("Error in add_summary: %s", err)

    def get_latest_summary(self) -> Optional[str]:
        lvl1 = [x for x in self.summary_entries if x["level"]==1]
        return lvl1[-1]["summary"] if lvl1 else None

    def get_latest_profile(self) -> Optional[Dict]:
        lvl1 = [x["summary"] for x in self.summary_entries if x["level"]==1]
        if not lvl1: return None
        prompt = "Perfil:\n" + "\n".join(f"- {s}" for s in lvl1)
        try:
            p = self.model.complete(prompt).text.strip()
            return {"timestamp": datetime.utcnow().isoformat(), "profile":p}
        except:
            return None

    def clear_memory(self):
        self.summary_entries = []
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                self.summary_entries = json.load(open(self.file_path,"r",encoding="utf-8"))
            except:
                os.rename(self.file_path, self.file_path+".broken")
                self.summary_entries = []

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        json.dump(self.summary_entries, open(self.file_path,"w",encoding="utf-8"),
                  indent=2, ensure_ascii=False)
