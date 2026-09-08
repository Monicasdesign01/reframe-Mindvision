"""
Speech-to-text using faster-whisper (CTranslate2 build of Whisper, same
weights as openai-whisper, several times faster on CPU). Only invoked
when the user submitted audio instead of typed text.
"""

import gc

from faster_whisper import WhisperModel

_MODEL_SIZE = "base"


class Transcriber:
    def __init__(self):
        # int8 compute type keeps this fast and light on a CPU-only machine.
        self._model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str) -> str:
        segments, _info = self._model.transcribe(audio_path, beam_size=5)
        return " ".join(segment.text.strip() for segment in segments).strip()

    def unload(self):
        del self._model
        gc.collect()
