"""
Full end-to-end benchmark including TTS and image generation, split per
stage: STT (optional, if an audio file is given) / distortion / emotion /
narrative / TTS / image.

Usage:
    python scripts/benchmark_full.py "some worry text"
    python scripts/benchmark_full.py --audio path/to/file.wav
"""

import sys
import os

# Must be set before torch/CTranslate2 are imported: faster-whisper and
# PyTorch's bundled MKL both link their own OpenMP runtime, which aborts
# the process the first time both are loaded together (see app/main.py).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp.distortions import detect_distortions
from app.emotion.classifier import EmotionClassifier
from app.context_engine.case_frame import CaseFrame
from app.principle_selector.selector import select_techniques
from app.narrative_gen.generator import NarrativeGenerator
from app.tts.narrator import Narrator
from app.image_gen.generator import ImageGenerator, build_image_prompt

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")
os.makedirs(OUT_DIR, exist_ok=True)


def timed(label, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"{label:20s} {elapsed:6.2f}s")
    return result


def main():
    args = sys.argv[1:]
    text = None

    if args and args[0] == "--audio":
        from app.asr.transcriber import Transcriber
        transcriber = Transcriber()
        text = timed("stt", lambda: transcriber.transcribe(args[1]))
        transcriber.unload()
    else:
        text = args[0] if args else "I always mess everything up and nothing will ever get better."

    print(f"Input text: {text}\n")

    distortions = timed("distortion_detection", lambda: detect_distortions(text))

    clf = EmotionClassifier()
    emotion_scores, core_emotion = timed("emotion_classification", lambda: clf.classify(text))
    clf.unload()

    case_frame = CaseFrame(raw_text=text, distortions=distortions,
                            emotion_scores=emotion_scores, core_emotion=core_emotion)
    case_frame.build_summary()

    techniques = timed("principle_selection", lambda: select_techniques(case_frame))
    primary = techniques[0]

    generator = NarrativeGenerator()
    narrative = timed("narrative_generation", lambda: generator.generate(case_frame, primary))
    generator.unload()

    narrator = Narrator()
    audio_path = os.path.join(OUT_DIR, "benchmark_audio.wav")
    timed("tts", lambda: narrator.narrate(narrative, audio_path))
    narrator.unload()

    img_gen = ImageGenerator()
    image_path = os.path.join(OUT_DIR, "benchmark_image.png")
    prompt = build_image_prompt(case_frame, primary)
    timed("image_generation", lambda: img_gen.generate(prompt, image_path))
    img_gen.unload()

    print("\nSummary:", case_frame.summary)
    print("Technique:", primary["name"])
    print("Audio saved to:", audio_path)
    print("Image saved to:", image_path)


if __name__ == "__main__":
    main()
