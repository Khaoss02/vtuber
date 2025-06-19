import os, asyncio, time
from twitchio.ext import commands
from open_llm_vtuber.agent.agents.agent_runner import handle_message
from open_llm_vtuber.memory.memory_manager import MemoryManager
from open_llm_vtuber.connectors.filter_utils import is_interesting, last_reply

mem = MemoryManager()

class StreamBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.getenv("TWITCH_TOKEN"),
            prefix="!",           # still available for manual commands
            initial_channels=[
                os.getenv("TWITCH_CHANNEL"),
                os.getenv("KICK_CHANNEL"),
            ],
        )

    async def event_ready(self):
        print(f"StreamBot active as {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return
        user = str(message.author.name)
        text = message.content

        # store every line
        mem.save_episode(f"[{user}] {text}", "(no ai yet)")

        if is_interesting(text, user):
            reply = handle_message(text, {"platform": "kick", "user": user})
            await message.channel.send(reply)
            last_reply[user] = time.time()

def run_stream_bot():
    asyncio.run(StreamBot().start())
