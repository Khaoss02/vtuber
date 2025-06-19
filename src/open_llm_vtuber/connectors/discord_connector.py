import os, discord
from dotenv import load_dotenv
from open_llm_vtuber.agent.agents.agent_runner import handle_message

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Discord bot logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    reply = handle_message(message.content, {"platform": "discord", "user": str(message.author)})
    if reply:
        await message.reply(reply)

def run_discord():
    bot.run(TOKEN)
