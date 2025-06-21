from typing import List, Dict

class SummaryMemoryManager:
    def __init__(self, episodic_memory: List[Dict], file_path: str,
                 model_name="Qwen/Qwen2.5-VL-3B-Instruct", temperature=0.3,
                 level1_window=20, level2_window=5):
        from open_llm_vtuber.agent.chat_hf_local import HFLocalChat  # Import local para romper ciclo
        self.file_path = file_path
        self.model = HFLocalChat(model_name=model_name, temperature=temperature)
        self.episodic_memory = episodic_memory
        self.level1_window = level1_window
        self.level2_window = level2_window
        self.summary_entries: List[Dict] = []
        self._load()
