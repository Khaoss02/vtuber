import os
import asyncio
import time
from googleapiclient.discovery import build
from open_llm_vtuber.agent.agents.agent_runner import handle_message
from open_llm_vtuber.connectors.filter_utils import is_interesting, last_reply

yt      = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
CHAT_ID = os.getenv("YOUTUBE_LIVE_CHAT_ID")

async def poll_chat():
    token = None
    while True:
        res = yt.liveChatMessages().list(
            liveChatId = CHAT_ID,
            part       = "snippet,authorDetails",
            pageToken  = token,
        ).execute()

        for item in res["items"]:
            text = item["snippet"]["displayMessage"]
            user = item["authorDetails"]["displayName"]

            if is_interesting(text, user):
                handle_message(text, {"platform": "youtube", "user": user})
                last_reply[user] = time.time()

        token = res.get("nextPageToken")
        await asyncio.sleep(4)

def run_youtube():
    asyncio.run(poll_chat())
