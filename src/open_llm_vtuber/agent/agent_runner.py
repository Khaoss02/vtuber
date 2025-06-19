"""
LangChain‑based multi‑agent runner.
Exposes tools: chat, recent_memory, semantic_memory_search.
"""

from langchain import hub
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI

from open_llm_vtuber.agent.chat_agent import ChatAgent
from open_llm_vtuber.memory.memory_manager import MemoryManager

llm        = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
memory     = MemoryManager()
chat_agent = ChatAgent()

tools = [
    Tool(
        name        = "chat",
        func        = chat_agent.chat,
        description = "Answer user with RAG + long‑term memory"
    ),
    Tool(
        name        = "recent_memory",
        func        = lambda n=5: memory.get_last_n(int(n)),
        description = "Return the last N chat episodes"
    ),
    Tool(
        name        = "semantic_memory_search",
        func        = lambda q: memory.semantic_search(q, top_k=3),
        description = "Semantically search past conversations"
    ),
]

prompt = hub.pull("hwchase17/openai-functions-agent")

agent_executor = initialize_agent(
    agent  = AgentType.OPENAI_FUNCTIONS,
    tools  = tools,
    llm    = llm,
    prompt = prompt,
    verbose = False,
)

def handle_message(content: str, context: dict | None = None) -> str:
    """Single entry‑point for every connector."""
    return agent_executor.run({"input": content, "context": context or {}})
