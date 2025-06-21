from pathlib import Path
from typing import List
from loguru import logger

from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.core.indices.vector_store.base import GPTVectorStoreIndex
from llama_index.core.indices.prompt_helper import PromptHelper
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .chat_hf_local import HFLocalChat
from .hf_multimodal import HFScreenAgent  # Si lo necesitas en chat_agent, sino importalo en run_server.py


DEFAULT_DOCS_DIR: Path = Path("data") / "knowledge"
DEFAULT_INDEX_DIR: Path = Path("data") / "index"


class ChatAgent:
    """
    Agente de conversación con:
      • RAG sobre documentos locales (GPTVectorStoreIndex)
      • Embeddings HF (bge-small-en-v1.5 - 133 MB)
      • LLM multimodal local Qwen 2.5-VL-3B-Instruct
    """

    def __init__(
        self,
        docs_dir: Path = DEFAULT_DOCS_DIR,
        index_dir: Path = DEFAULT_INDEX_DIR,
        hf_llm_name: str = "Qwen/Qwen2.5-VL-3B-Instruct",
        hf_embed_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:

        # Forzamos device cpu para embeddings para evitar error meta tensor
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=hf_embed_name,
            device="cpu",
        )

        Settings.prompt_helper = PromptHelper(
            context_window=4096,
            num_output=512,
            chunk_overlap_ratio=0.10,
        )

        # Cargamos el LLM local sin hacer .to() manual
        self.llm = HFLocalChat(model_name=hf_llm_name)

        docs_dir.mkdir(parents=True, exist_ok=True)
        index_dir.mkdir(parents=True, exist_ok=True)
        self.storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))

        if any(index_dir.iterdir()):
            logger.info("Cargando índice vectorial existente…")
            self.index = load_index_from_storage(self.storage_context)
        else:
            logger.info("Creando índice vectorial nuevo…")
            documents = self._load_docs(docs_dir)
            self.index = GPTVectorStoreIndex.from_documents(
                documents, storage_context=self.storage_context
            )
            self.storage_context.persist()

    def chat(self, message: str) -> str:
        # 1) Recuperamos contexto relevante
        nodes = self.index.as_retriever(similarity_top_k=3).retrieve(message)
        context = "\n\n".join(node.get_content() for node in nodes)

        # 2) Construimos prompt para el modelo
        prompt = (
            "### Contexto\n"
            f"{context}\n\n"
            "### Pregunta\n"
            f"{message}\n\n"
            "### Respuesta (en español):"
        )

        # 3) Generamos respuesta con el LLM local
        return self.llm.chat(prompt)

    def add_documents(self, paths: List[Path]) -> None:
        new_docs = []
        for p in paths:
            new_docs.extend(SimpleDirectoryReader(str(p)).load_data())
        self.index.insert_nodes(new_docs)
        self.storage_context.persist()

    @staticmethod
    def _load_docs(docs_dir: Path):
        if any(docs_dir.iterdir()):
            logger.info(f"Cargando documentos desde {docs_dir}")
            return SimpleDirectoryReader(str(docs_dir)).load_data()
        logger.warning(f"{docs_dir} está vacío; índice sin documentos.")
        return []
