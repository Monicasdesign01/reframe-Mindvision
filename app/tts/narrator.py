"""
Voice narration using Kokoro-82M (Apache-2.0). Kokoro's misaki phonemizer
uses the espeak-ng library bundled by the `espeakng-loader` pip package
(a transitive dependency of kokoro/misaki) for out-of-dictionary words, so
no system-wide espeak-ng install is required.
"""

import gc

import soundfile as sf
from kokoro import KPipeline

_LANG_CODE = "a"  # American English
_VOICE = "af_heart"


class Narrator:
    def __init__(self):
        self._pipeline = KPipeline(lang_code=_LANG_CODE)

    def narrate(self, text: str, output_path: str) -> str:
        generator = self._pipeline(text, voice=_VOICE)
        audio_chunks = [audio for _, _, audio in generator]
        if not audio_chunks:
            raise RuntimeError("Kokoro produced no audio output")
        import numpy as np
        full_audio = np.concatenate(audio_chunks)
        sf.write(output_path, full_audio, 24000)
        return output_path

    def unload(self):
        del self._pipeline
        gc.collect()
