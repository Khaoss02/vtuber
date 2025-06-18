"""ChatAgent with advanced memory and personality summary integration"""

from __future__ import annotations
import logging
import os
from typing import Optional

from llama_index import GPTSimpleVectorIndex, LLMPredictor, PromptHelper, ServiceContext
from llama_index.llms.openai import OpenAI
from open_llm_vtuber.memory.memory_manager import MemoryManager

logging.basicConfig(level=logging.INFO)
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

        prompt_helper = PromptHelper(max_input_size=4096, num_output=512, max_chunk_overlap=20)
        llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.7, model_name="gpt-4o-mini"))
        self.service_context = ServiceContext.from_defaults(
            llm_predictor=llm_predictor, prompt_helper=prompt_helper
        )

        try:
            self.index = GPTSimpleVectorIndex.load_from_disk(index_path, service_context=self.service_context)
            logger.info("Vector index loaded.")
        except Exception as exc:
            logger.warning(f"No vector index: {exc}. Continuing without RAG.")
            self.index = None

        self.memory = MemoryManager(
            episodic_path=episodic_path,
            semantic_path=semantic_path,
            semantic_emb_path=semantic_emb_path,
            summary_path=summary_path,
        )

    def chat(self, user_input: str) -> str:
        # Obtén resumen y perfil
        summary = self.memory.latest_summary()
        profile = self.memory.latest_profile()
        if summary:
            logger.info(f"Latest summary:\n{summary}")
        if profile:
            logger.info(f"Personality profile:\n{profile['profile']}")

        # Construye prompt enriquecido
        enriched = ""
        if profile:
            enriched += f"VTuber profile:\n{profile['profile']}\n\n"
        if summary:
            enriched += f"Recent summary:\n{summary}\n\n"
        enriched += f"User says: {user_input}\nVTuber responds:"

        # Genera respuesta (RAG o LLM)
        if self.index:
            try:
                resp = self.index.query(enriched)
                response_text = resp.response
            except Exception:
                response_text = self._call_llm(enriched)
        else:
            response_text = self._call_llm(enriched)

        # Guarda en memoria avanzada
        episode = {"user_input": user_input, "ai_response": response_text}
        self.memory.save_episode(episode)

        return response_text

    def _call_llm(self, prompt: str) -> str:
        return self.service_context.llm_predictor.llm.complete(prompt).text

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    agent = ChatAgent(openai_api_key=api_key)
    print("VTuber ready. Type 'exit' to quit.")
    while True:
        msg = input("You: ")
        if msg.lower() in {"exit", "quit", "salir"}:
            break
        print("VTuber:", agent.chat(msg))
