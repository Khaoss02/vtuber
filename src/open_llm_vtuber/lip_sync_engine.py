import io
import wave
import whisper
from phonemizer import phonemize
from phonemizer.separator import Separator
from typing import List

_PHONEME_TO_VISEME = {
    "AA": "A", "AE": "A", "AH": "A", "AO": "O",
    "AW": "O", "AY": "A", "EH": "E", "ER": "E",
    "EY": "E", "IH": "I", "IY": "I", "OW": "O",
    "OY": "O", "UH": "U", "UW": "U",
    "P": "P", "B": "P", "M": "M",
    "F": "F", "V": "F",
    "T": "T", "D": "T", "N": "N",
    "K": "K", "G": "K", "NG": "N",
    "CH": "CH", "JH": "CH", "SH": "SH",
    "ZH": "SH", "TH": "TH", "DH": "TH",
    "R": "R", "L": "L", "W": "W", "Y": "Y",
}

class LipSyncEngine:
    def __init__(self, whisper_model: str = "base"):
        self.whisper = whisper.load_model(whisper_model)

    def _transcribe(self, audio_bytes: bytes) -> str:
        buf = io.BytesIO(audio_bytes)
        with wave.open(buf, "rb") as _:
            tmp = "tmp_whisper.wav"
            with open(tmp, "wb") as f:
                f.write(audio_bytes)
        result = self.whisper.transcribe(tmp)
        return result["text"]

    def _text_to_phonemes(self, text: str) -> List[str]:
        phoneme_seq = phonemize(
            text,
            language='en-us',
            backend='espeak',
            separator=Separator(phone=' '),
            strip=True,
            preserve_punctuation=False,
            njobs=1,
        )
        return phoneme_seq.split()

    def predict_viseme(self, audio_bytes: bytes) -> str:
        try:
            text = self._transcribe(audio_bytes)
        except Exception:
            return "A"
        phonemes = self._text_to_phonemes(text)
        for ph in phonemes:
            p = ph.upper()
            if p in _PHONEME_TO_VISEME:
                return _PHONEME_TO_VISEME[p]
        return "A"
