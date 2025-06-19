import os
from slack_bolt import App
from dotenv import load_dotenv
from open_llm_vtuber.agent.agents.agent_runner import handle_message

load_dotenv()
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

@app.message("")
def everything(message, say):
    user = message["user"]
    text = message["text"]
    reply = handle_message(text, {"platform": "slack", "user": user})
    say(reply)

def run_slack():
    port = int(os.getenv("SLACK_PORT", 3000))
    app.start(port=port)
