import argparse
import atexit
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from loguru import logger
import tomli
import uvicorn

from open_llm_vtuber.agent.chat_agent import ChatAgent

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# VTuber WebSocket Server
# - Audio in  → emoción + visema
# - Texto out → respuesta IA con memoria avanzada
# - Static folders: /live2d-models  /models
# ──────────────────────────────────────────────────────────────────────────────

# ── Dependencias básicas ------------------------------------------------------

# ── Emoción (audio) -----------------------------------------------------------
try:
    from open_llm_vtuber.emotion_engine import EmotionEngine  # type: ignore

    emotion_engine = EmotionEngine()
except ImportError:
    class _DummyEmotion:
        def detect_from_audio(self, *_):
            return "neutral"

    emotion_engine = _DummyEmotion()

# ── Lip‑Sync ------------------------------------------------------------------
try:
    from open_llm_vtuber.lip_sync_engine import LipSyncEngine  # type: ignore

    lip = LipSyncEngine("base")  # Whisper‑based
except ImportError:
    import numpy as np
    import wave

    class _VisemeGen:
        TH = [1000, 2000, 3000, 4000, 5000]
        VS = ["A", "E", "I", "O", "U"]

        def predict_viseme(self, audio: bytes):  # noqa: D401
            try:
                with wave.open(io.BytesIO(audio), "rb") as wf:
                    data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    energy = abs(data).mean()
            except wave.Error:
                return "A"
            for v, t in zip(self.VS, self.TH):
                if energy < t:
                    return v
            return "U"

    lip = _VisemeGen()


# ── Logger --------------------------------------------------------------------
def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        return tomli.load(f)["project"]["version"]


def init_logger(level: str):
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | {message}",
        colorize=True,
    )
    Path("logs").mkdir(exist_ok=True)
    logger.add(
        "logs/debug_{time:YYYY-MM-DD}.log", rotation="10 MB", retention="30 days", level="DEBUG"
    )


# ── CLI args ------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser("VTuber server")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", default=8000, type=int)
    return p.parse_args()


# ── FastAPI app ---------------------------------------------------------------



def create_app(static_live2d: str, static_models: str) -> FastAPI:
    app = FastAPI()
    app.mount("/live2d-models", StaticFiles(directory=static_live2d), name="live2d-models")
    app.mount("/models", StaticFiles(directory=static_models), name="models")
    return app


# ── Main ----------------------------------------------------------------------
def main():
    args = parse_args()
    init_logger("DEBUG" if args.verbose else "INFO")
    logger.info(f"VTuber Server v{get_version()}")

    app = create_app("C:/vtuber/live2d-models", "C:/vtuber/models")
    agent = ChatAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):  # noqa: D401
        await ws.accept()
        mode = "2d"
        while True:
            audio = await ws.receive_bytes()
            emotion = emotion_engine.detect_from_audio(audio)
            viseme = lip.predict_viseme(audio)

            # TODO: integra Whisper real
            user_text = "Texto transcrito (stub)"
            response = agent.chat(user_text, context={"emotion": emotion})

            await ws.send_json(
                {
                    "text": response,
                    "viseme": viseme,
                    "emotion": emotion,
                    "mode": mode,
                }
            )

    atexit.register(lambda: logger.info("Shutdown – cache cleaned"))

    uvicorn.run(
        app, host=args.host, port=args.port, log_level="debug" if args.verbose else "info"
    )


if __name__ == "__main__":
    import threading
    import time

    threading.Thread(target=main, daemon=True).start()

    from open_llm_vtuber.connectors.discord_connector import run_discord
    from open_llm_vtuber.connectors.slack_connector import run_slack
    from open_llm_vtuber.connectors.stream_bot import run_stream_bot
    from open_llm_vtuber.connectors.youtube_connector import run_youtube

    threading.Thread(target=run_discord, daemon=True).start()
    threading.Thread(target=run_slack, daemon=True).start()
    threading.Thread(target=run_stream_bot, daemon=True).start()
    threading.Thread(target=run_youtube, daemon=True).start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping all connectors …")
