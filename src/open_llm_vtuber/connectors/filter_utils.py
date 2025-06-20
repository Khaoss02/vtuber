"""
Shared heuristics to decide if a chat line is interesting enough
to forward to the LLM.
"""

import re
import time
from collections import defaultdict

QUESTION = re.compile(r"\?")
MENTION  = re.compile(r"\b(khaoss|vtuber|k‑bot|bot)\b", re.I)
KEYWORDS = (
    "how","why","when","where","what","which",
    "help","idea","explain","could","should","would",
    "cómo","por qué","cuando","dónde","cuál","ayuda",
)

last_reply: dict[str, float] = defaultdict(lambda: 0.0)
COOLDOWN = 60     # seconds

def is_interesting(text: str, user: str) -> bool:
    txt = text.lower()
    if QUESTION.search(txt) or MENTION.search(txt) or any(k in txt for k in KEYWORDS):
        return True
    # fallback: reply again after 5× cooldown silence
    return time.time() - last_reply[user] > COOLDOWN * 5
