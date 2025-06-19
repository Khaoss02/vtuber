"""
Detector ligero de emoción por audio basado en pyAudioAnalysis y características acústicas.
Mejora sobre heurística básica con energía, ZCR, pitch y spectral centroid.

Requiere:
pip install pyAudioAnalysis numpy scipy librosa
"""

from __future__ import annotations
import tempfile
import os
import numpy as np
from pyAudioAnalysis import audioBasicIO, ShortTermFeatures
import librosa

class EmotionEngine:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def _log(self, *args):
        if self.verbose:
            print("[EmotionEngine]", *args)

    def detect_from_audio(self, wav_bytes: bytes) -> str:
        # Guardar audio temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            filename = tmp.name

        try:
            # Leer audio
            [fs, signal] = audioBasicIO.read_audio_file(filename)
            signal = signal.astype(np.float32)

            # Normalizar audio para evitar dependencia de volumen absoluto
            signal /= np.max(np.abs(signal)) + 1e-9

            # Extraer features short term
            feats, _ = ShortTermFeatures.feature_extraction(signal, fs, 0.050*fs, 0.025*fs)
            energy = np.mean(feats[1])
            zcr = np.mean(feats[0])

            # Extraer pitch y spectral centroid con librosa (más robusto)
            y, sr = librosa.load(filename, sr=None)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_vals = pitches[magnitudes > np.median(magnitudes)]
            pitch = np.mean(pitch_vals) if pitch_vals.size > 0 else 0

            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

            self._log(f"Energía: {energy:.4f}, ZCR: {zcr:.4f}, Pitch: {pitch:.2f}, Centroid: {spectral_centroid:.2f}")

            # Clasificación heurística
            if energy > 0.06 and zcr < 0.1 and pitch > 200:
                return "angry"
            elif energy < 0.01 and pitch < 100:
                return "sad"
            elif zcr > 0.2 and pitch > 150:
                return "happy"
            elif spectral_centroid > 3000 and energy > 0.03:
                return "surprised"
            else:
                return "neutral"
        finally:
            # Limpieza archivo temporal
            os.unlink(filename)
