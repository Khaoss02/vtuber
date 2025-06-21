"""
Simple multi‑tool runner SIN LangChain.
--------------------------------------
Expone 3 utilidades:
  • chat
  • recent_memory
  • semantic_memory_search
"""

from __future__ import annotations
from typing import Callable

from open_llm_vtuber.agent.chat_agent import ChatAgent
from open_llm_vtuber.memory.memory_manager import MemoryManager

memory      = MemoryManager()
chat_agent  = ChatAgent()               # usa tu Qwen local
TOOLS: dict[str, Callable] = {
    "chat": chat_agent.chat,
    "recent_memory": lambda n=5: memory.get_last_n(int(n)),
    "semantic_memory_search": lambda q: memory.semantic_search(q, top_k=3),
}


def handle_message(content: str,
                   context: dict | None = None) -> str:
    """Enrutador muy simple de herramientas."""
    cmd = (context or {}).get("tool", "chat")
    if cmd in TOOLS:
        return TOOLS[cmd](content)
    return f"❌ Comando no reconocido: {cmd}"
