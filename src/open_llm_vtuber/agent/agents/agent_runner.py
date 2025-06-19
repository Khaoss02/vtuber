# src/open_llm_vtuber/agents/agent_runner.py
from langchain import hub
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI

from open_llm_vtuber.agent.chat_agent import ChatAgent
from open_llm_vtuber.memory.memory_manager import MemoryManager

llm        = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
memory     = MemoryManager()
chat_agent = ChatAgent()

# Tools exposed to the agent
tools = [
    Tool(
        name        = "chat",
        func        = chat_agent.chat,
        description = "Answer user queries with RAG + long‑term memory"
    ),
    Tool(
        name        = "recent_memory",
        func        = lambda n=5: memory.get_last_n(int(n)),
        description = "Fetch the last N chat episodes"
    ),
    Tool(
        name        = "semantic_memory_search",
        func        = lambda q: memory.semantic_search(q, top_k=3),
        description = "Search past conversations semantically"
    ),
]

prompt = hub.pull("hwchase17/openai-functions-agent")

agent_executor = initialize_agent(
    agent       = AgentType.OPENAI_FUNCTIONS,
    tools       = tools,
    llm         = llm,
    prompt      = prompt,
    verbose     = False,
)

def handle_message(content: str, context: dict | None = None) -> str:
    """Entry‑point for all connectors."""
    meta = context or {}
    return agent_executor.run({"input": content, "context": meta})
