"""
LangChain‑free multi‑tool runner.
Tools exposed: chat, recent_memory, semantic_memory_search
"""

from __future__ import annotations
from typing import Callable

from open_llm_vtuber.agent.chat_agent import ChatAgent
from open_llm_vtuber.memory.memory_manager import MemoryManager

# Instancias principales
memory = MemoryManager()
chat_agent = ChatAgent()

# Herramientas expuestas (simulan agente)
TOOLS: dict[str, Callable] = {
    "chat": chat_agent.chat,
    "recent_memory": lambda n=5: memory.get_last_n(int(n)),
    "semantic_memory_search": lambda q: memory.semantic_search(q, top_k=3),
}


def handle_message(content: str, context: dict | None = None) -> str:
    """Simula una ejecución tipo agente, pero solo usa herramientas locales."""
    command = context.get("tool") if context else "chat"

    if command in TOOLS:
        return TOOLS[command](content)
    return f"❌ Comando no reconocido: {command}"
