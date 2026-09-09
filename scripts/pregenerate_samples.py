"""
Pre-generates 2-3 full example sessions (text + audio, image separate) as
a fallback for the live demo, in case real-time inference is too slow in
the room. Saved under data/samples/.

Image generation is deliberately NOT run here: on a low-RAM machine,
SD-Turbo's VAE-decode step can segfault (see README's RAM note), and a
segfault kills the whole Python process -- losing every sample already
generated in this same run, text and audio included. Text and audio
generation are stable, so they're generated together and written to
manifest.json immediately. Run scripts/pregenerate_images.py afterward
(with more free RAM) to add images to the same manifest one at a time,
each in its own subprocess, so one crash can't take down the others.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp.distortions import detect_distortions
from app.emotion.classifier import EmotionClassifier
from app.context_engine.case_frame import CaseFrame
from app.principle_selector.selector import select_techniques
from app.narrative_gen.generator import NarrativeGenerator
from app.narrative_gen.affirmations import build_affirmation
from app.tts.narrator import Narrator
from app.image_gen.generator import build_image_prompt

SAMPLE_INPUTS = [
    "I always mess everything up. My presentation tomorrow is going to be a total disaster and everyone will think I'm an idiot.",
    "I feel so alone lately, like nothing I do matters and no one would notice if I disappeared for a while.",
    "I got passed over for the promotion again. I guess I'm just not good enough and I never will be.",
]

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    clf = EmotionClassifier()
    generator = NarrativeGenerator()
    narrator = Narrator()

    manifest = []

    for i, text in enumerate(SAMPLE_INPUTS, start=1):
        print(f"[{i}/{len(SAMPLE_INPUTS)}] {text[:50]}...")

        distortions = detect_distortions(text)
        emotion_scores, core_emotion = clf.classify(text)
        case_frame = CaseFrame(raw_text=text, distortions=distortions,
                                emotion_scores=emotion_scores, core_emotion=core_emotion)
        case_frame.build_summary()

        techniques = select_techniques(case_frame)
        primary = techniques[0]

        narrative = generator.generate(case_frame, primary)

        # Affirmation, not the narrative text itself -- matches app/main.py's
        # live TTS behavior, which reads a short affirmation aloud instead
        # of repeating what's already shown (and, since Phase 4, drawn) on
        # screen.
        audio_path = os.path.join(OUT_DIR, f"sample_{i}.wav")
        affirmation = build_affirmation(core_emotion, primary["name"])
        narrator.narrate(affirmation, audio_path)

        image_prompt = build_image_prompt(case_frame, primary)

        manifest.append({
            "input_text": text,
            "summary": case_frame.summary,
            "technique": primary["name"],
            "narrative": narrative,
            "audio": f"sample_{i}.wav",
            "image": None,  # filled in by pregenerate_images.py
            "image_prompt": image_prompt,
        })

        # Write after every sample, not just at the end, so a crash never
        # loses more than the one sample in progress.
        with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    clf.unload()
    generator.unload()
    narrator.unload()

    print(f"\nDone. {len(manifest)} sample sessions (text + audio) saved to {OUT_DIR}")
    print("Run scripts/pregenerate_images.py next to add images.")


if __name__ == "__main__":
    main()
