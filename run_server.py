#!/usr/bin/env python3
import argparse
import atexit
import io
import os
import sys
import asyncio
from pathlib import Path
import threading
import time
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from loguru import logger
import tomli
import uvicorn

from open_llm_vtuber.agent.chat_agent import ChatAgent
from open_llm_vtuber.agent.hf_multimodal import HFScreenAgent  # Wrapper multimodal

load_dotenv()

DEFAULT_LIVE2D_MODELS_PATH = os.getenv("LIVE2D_MODELS_PATH", "C:/vtuber/live2d-models")
DEFAULT_MODELS_PATH = os.getenv("MODELS_PATH", "C:/vtuber/models")

try:
    from open_llm_vtuber.emotion_engine import EmotionEngine
    emotion_engine = EmotionEngine()
except ImportError:
    class _DummyEmotion:
        def detect_from_audio(self, *_): return "neutral"
    emotion_engine = _DummyEmotion()

try:
    from open_llm_vtuber.lip_sync_engine import LipSyncEngine
    lip = LipSyncEngine("base")
except ImportError:
    import numpy as np, wave
    class _VisemeGen:
        TH = [1000, 2000, 3000, 4000, 5000]; VS = ["A", "E", "I", "O", "U"]
        def predict_viseme(self, audio):
            try:
                with wave.open(io.BytesIO(audio), "rb") as wf:
                    data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    e = abs(data).mean()
            except wave.Error:
                return "A"
            for v, t in zip(self.VS, self.TH):
                if e < t: return v
            return "U"
    lip = _VisemeGen()

async def transcribe_audio_stream(audio_chunks: list[bytes]) -> str:
    await asyncio.sleep(0.01)
    return "Texto transcrito (simulado)"

async def process_audio_chunk(
    text_agent: ChatAgent,
    screen_agent: HFScreenAgent,
    audio_chunk: bytes,
    audio_buffer: list[bytes]
) -> dict:
    audio_buffer.append(audio_chunk)
    emotion = emotion_engine.detect_from_audio(audio_chunk)
    viseme = lip.predict_viseme(audio_chunk)
    user_text = await transcribe_audio_stream(audio_buffer)

    text_resp = text_agent.chat(user_text, context={"emotion": emotion})
    screen_resp = screen_agent.chat(user_text)

    return {
        "text": screen_resp,
        "alternative_text": text_resp,
        "viseme": viseme,
        "emotion": emotion,
        "mode": "2d",
    }

def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        return tomli.load(f)["project"]["version"]

def init_logger(level: str):
    logger.remove()
    logger.add(sys.stderr, level=level,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                      "<level>{level: <8}</level> | {message}",
               colorize=True)
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/debug_{time:YYYY-MM-DD}.log",
               rotation="10 MB", retention="30 days", level="DEBUG")

def parse_args():
    p = argparse.ArgumentParser("VTuber server")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", default=8000, type=int)
    p.add_argument("--live2d", default=DEFAULT_LIVE2D_MODELS_PATH)
    p.add_argument("--models", default=DEFAULT_MODELS_PATH)
    return p.parse_args()

def create_app(static_live2d: str, static_models: str) -> FastAPI:
    app = FastAPI()
    app.mount("/live2d-models", StaticFiles(directory=static_live2d), name="live2d-models")
    app.mount("/models", StaticFiles(directory=static_models), name="models")
    return app

def main():
    args = parse_args()
    init_logger("DEBUG" if args.verbose else "INFO")
    logger.info(f"VTuber Server v{get_version()}")

    app = create_app(args.live2d, args.models)
    text_agent = ChatAgent()
    screen_agent = HFScreenAgent()  # Qwen2.5-VL-3B-Instruct multimodal

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        audio_buffer = []
        try:
            while True:
                chunk = await ws.receive_bytes()
                result = await process_audio_chunk(text_agent, screen_agent, chunk, audio_buffer)
                await ws.send_json(result)
        except WebSocketDisconnect:
            logger.info("WebSocket desconectado")
        except Exception as e:
            logger.error(f"Error WS: {e}")
            await ws.close()

    atexit.register(lambda: logger.info("Shutdown – cache cleaned"))
    uvicorn.run(app, host=args.host, port=args.port, log_level="debug" if args.verbose else "info")

def safe_thread(target, name):
    def wrapper():
        try:
            target()
        except Exception as e:
            logger.error(f"Error en {name} Connector: {e}\n{traceback.format_exc()}")
    return wrapper

def safe_async_thread(coro_func, name):
    def wrapper():
        try:
            asyncio.run(coro_func())
        except Exception as e:
            logger.error(f"Error en {name} Connector: {e}\n{traceback.format_exc()}")
    return wrapper

if __name__ == "__main__":
    threading.Thread(target=main, daemon=True).start()

    # Comentado bloque de conectores para evitar errores por API inválidas
    """
    try:
        from open_llm_vtuber.connectors.discord_connector import run_discord
        threading.Thread(target=safe_thread(run_discord, "Discord"), daemon=True).start()
    except Exception as e:
        logger.error(f"Error iniciando Discord Connector: {e}")

    try:
        from open_llm_vtuber.connectors.slack_connector import run_slack
        threading.Thread(target=safe_thread(run_slack, "Slack"), daemon=True).start()
    except Exception as e:
        logger.error(f"Error iniciando Slack Connector: {e}")

    try:
        from open_llm_vtuber.connectors.stream_bot import run_stream_bot
        threading.Thread(target=safe_async_thread(run_stream_bot, "Stream Bot"), daemon=True).start()
    except Exception as e:
        logger.error(f"Error iniciando Stream Bot Connector: {e}")

    try:
        from open_llm_vtuber.connectors.youtube_connector import run_youtube
        threading.Thread(target=safe_async_thread(run_youtube, "YouTube"), daemon=True).start()
    except Exception as e:
        logger.error(f"Error iniciando YouTube Connector: {e}")
    """

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping all connectors …")
