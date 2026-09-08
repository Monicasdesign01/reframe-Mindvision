"""
Pre-generates 2-3 full example sessions (text + image + audio) as a
fallback for the live demo, in case real-time inference is too slow in
the room. Saved under data/samples/.
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
from app.tts.narrator import Narrator
from app.image_gen.generator import ImageGenerator, build_image_prompt

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
    img_gen = ImageGenerator()

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

        audio_path = os.path.join(OUT_DIR, f"sample_{i}.wav")
        narrator.narrate(narrative, audio_path)

        image_path = os.path.join(OUT_DIR, f"sample_{i}.png")
        prompt = build_image_prompt(case_frame, primary)
        img_gen.generate(prompt, image_path)

        manifest.append({
            "input_text": text,
            "summary": case_frame.summary,
            "technique": primary["name"],
            "narrative": narrative,
            "audio": f"sample_{i}.wav",
            "image": f"sample_{i}.png",
        })

    clf.unload()
    generator.unload()
    narrator.unload()
    img_gen.unload()

    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. {len(manifest)} sample sessions saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
