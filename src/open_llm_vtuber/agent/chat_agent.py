# src/open_llm_vtuber/agent/chat_agent.py

import logging
from llama_index import GPTSimpleVectorIndex, LLMPredictor, PromptHelper, ServiceContext
from llama_index.llms.openai import OpenAI
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatAgent:
    def __init__(self, index_path: str = "index.json", openai_api_key: str = None):
        """
        Inicializa el agente con un índice y el modelo LLM.

        :param index_path: Ruta al archivo JSON del índice de llama-index.
        :param openai_api_key: API key de OpenAI (opcional si la tienes en variables de entorno).
        """
        self.index_path = index_path

        # Configura la API key de OpenAI
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key

        # Parámetros para el LLM y prompt
        max_input_size = 4096
        num_output = 512
        max_chunk_overlap = 20

        prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)
        llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.7, model_name="gpt-4o-mini"))

        service_context = ServiceContext.from_defaults(
            llm_predictor=llm_predictor,
            prompt_helper=prompt_helper
        )

        # Carga o crea el índice
        try:
            logger.info(f"Cargando índice desde {self.index_path}...")
            self.index = GPTSimpleVectorIndex.load_from_disk(self.index_path, service_context=service_context)
            logger.info("Índice cargado correctamente.")
        except Exception as e:
            logger.error(f"No se pudo cargar el índice: {e}")
            logger.info("Creando un índice vacío.")
            self.index = None  # o crear uno nuevo desde documentos si tienes

    def chat(self, user_input: str) -> str:
        """
        Procesa el input del usuario y devuelve la respuesta del índice + LLM.

        :param user_input: Texto de entrada del usuario.
        :return: Respuesta generada.
        """
        if not self.index:
            return "No hay índice cargado para responder. Por favor crea o carga uno."

        try:
            response = self.index.query(user_input)
            return response.response  # llama-index devuelve un objeto Response con atributo .response
        except Exception as e:
            logger.error(f"Error al consultar el índice: {e}")
            return f"Error procesando tu pregunta: {e}"


if __name__ == "__main__":
    # Prueba rápida por consola
    openai_key = os.getenv("OPENAI_API_KEY")
    agent = ChatAgent(index_path="index.json", openai_api_key=openai_key)
    print("ChatAgent listo. Escribe 'salir' para terminar.")

    while True:
        user_msg = input("Tú: ")
        if user_msg.lower() in ("salir", "exit", "quit"):
            break
        answer = agent.chat(user_msg)
        print("VTuber:", answer)
