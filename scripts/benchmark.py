"""
Times one full request end-to-end, split per stage, so real demo latency
on this machine is known in advance rather than guessed.

Usage:
    python scripts/benchmark.py "some worry text"
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp.distortions import detect_distortions
from app.emotion.classifier import EmotionClassifier
from app.context_engine.case_frame import CaseFrame
from app.principle_selector.selector import select_techniques
from app.narrative_gen.generator import NarrativeGenerator


def timed(label, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"{label:20s} {elapsed:6.2f}s")
    return result


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else "I always mess everything up and nothing will ever get better."
    print(f"Input: {text}\n")

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

    print("\n--- TTS and image generation are skipped in this quick benchmark; ---")
    print("--- run scripts/benchmark_full.py for a full end-to-end timing including audio/image. ---\n")

    print("Summary:", case_frame.summary)
    print("Technique:", primary["name"])
    print("\nNarrative:\n", narrative)


if __name__ == "__main__":
    main()
