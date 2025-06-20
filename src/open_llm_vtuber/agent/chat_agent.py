"""ChatAgent with advanced memory and personality integration"""

from __future__ import annotations
import logging
import os
from typing import Optional, Dict, Any

from llama_index import GPTSimpleVectorIndex, LLMPredictor, PromptHelper, ServiceContext
from llama_index.llms.openai import OpenAI

from open_llm_vtuber.memory.memory_manager import MemoryManager
from open_llm_vtuber.personality import Personality

logger = logging.getLogger(__name__)

class ChatAgent:
    def __init__(
        self,
        index_path: str = "index.json",
        openai_api_key: Optional[str] = None,
        episodic_path: str = "src/open_llm_vtuber/data/episodic_memory.json",
        semantic_path: str = "src/open_llm_vtuber/data/semantic_memory.json",
        semantic_emb_path: str = "src/open_llm_vtuber/data/semantic_embeddings.pt",
        summary_path: str = "src/open_llm_vtuber/data/summary_memory.json",
    ) -> None:
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key

        ph = PromptHelper(4096, 512, 20)
        llmp = LLMPredictor(llm=OpenAI(temperature=0.7, model_name="gpt-4o-mini"))
        self.service_ctx = ServiceContext.from_defaults(
            llm_predictor=llmp, prompt_helper=ph
        )

        try:
            self.index = GPTSimpleVectorIndex.load_from_disk(
                index_path, service_context=self.service_ctx
            )
            logger.info("Vector index loaded.")
        except Exception as e:
            logger.warning("No vector index: %s", e)
            self.index = None

        self.memory = MemoryManager(
            episodic_path, semantic_path, semantic_emb_path, summary_path
        )
        self.personality = Personality()

    def chat(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        summary = self.memory.latest_summary()
        profile = self.memory.latest_profile()

        enriched = ""
        if profile:
            enriched += f"VTuber profile:\n{profile['profile']}\n\n"
        if summary:
            enriched += f"Recent summary:\n{summary}\n\n"
        enriched += f"User says: {user_input}\nVTuber responds:"

        if self.index:
            try:
                resp = self.index.query(enriched)
                text = resp.response
            except Exception:
                text = self._call_llm(enriched)
        else:
            text = self._call_llm(enriched)

        styled = self.personality.apply_personality_to_response(text)

        episode = {
            "user_input": user_input,
            "ai_response": styled,
            "context": context or {}
        }
        self.memory.save_episode(episode)

        return styled

    def _call_llm(self, prompt: str) -> str:
        return self.service_ctx.llm_predictor.llm.complete(prompt).text
