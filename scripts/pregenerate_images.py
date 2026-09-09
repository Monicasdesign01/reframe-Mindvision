"""
Adds storyboard images to the manifest produced by pregenerate_samples.py,
one at a time, each in its own subprocess. A subprocess crash (e.g. the
SD-Turbo VAE-decode segfault seen on low-RAM machines -- see README) only
loses that one image; the manifest and every other sample are unaffected.

Each image is a 3-panel CURRENT REALITY / REFRAME / DESIRED FUTURE
storyboard (see app/image_gen/storyboard.py), built from that sample's own
narrative and technique -- same generation path the live app uses in
app/main.py's _generate_image_background.

Run after pregenerate_samples.py, ideally with other applications closed
to free RAM:
    python scripts/pregenerate_images.py
"""

import sys
import os
import re
import json
import subprocess

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")
MANIFEST_PATH = os.path.join(OUT_DIR, "manifest.json")

_WORKER_CODE = """
import os
import sys
sys.path.insert(0, {project_root!r})
from app.image_gen.generator import ImageGenerator, build_panel_prompts, build_panel_subtitles
from app.image_gen.storyboard import compose_storyboard
from app.narrative_gen.generator import parse_narrative_parts

core_emotion = {core_emotion!r}
technique_name = {technique_name!r}
narrative_parts = parse_narrative_parts({narrative!r})

prompts = build_panel_prompts(core_emotion, technique_name)
subtitles = build_panel_subtitles(core_emotion, technique_name)
panel_paths = {panel_paths!r}

gen = ImageGenerator()
for prompt, path in zip(prompts, panel_paths):
    gen.generate(prompt, path, seed={seed!r}, num_inference_steps=2)
gen.unload()

compose_storyboard(panel_paths, subtitles, narrative_parts, {output_path!r})

for p in panel_paths:
    try:
        os.remove(p)
    except OSError:
        pass
print("OK")
"""


def _extract_core_emotion(summary: str) -> str:
    match = re.search(r"feeling (\w+)", summary or "")
    return match.group(1) if match else "worry"


def generate_one(entry: dict, output_path: str, seed: int) -> bool:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_paths = [output_path.replace(".png", f"_panel{i + 1}.png") for i in range(3)]
    code = _WORKER_CODE.format(
        project_root=project_root,
        core_emotion=_extract_core_emotion(entry.get("summary", "")),
        technique_name=entry.get("technique", "Cognitive Restructuring"),
        narrative=entry.get("narrative", ""),
        panel_paths=panel_paths,
        output_path=output_path,
        seed=seed,
    )
    python_exe = sys.executable
    result = subprocess.run([python_exe, "-c", code], capture_output=True, text=True)
    return result.returncode == 0 and os.path.exists(output_path)


def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"No manifest found at {MANIFEST_PATH}. Run pregenerate_samples.py first.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for i, entry in enumerate(manifest, start=1):
        if entry.get("image"):
            print(f"[{i}/{len(manifest)}] already has an image, skipping.")
            continue

        image_path = os.path.join(OUT_DIR, f"sample_{i}.png")
        print(f"[{i}/{len(manifest)}] generating storyboard...")
        # A distinct seed per sample, not a shared constant, so multiple
        # demo sessions shown together (e.g. on the Journey page) don't all
        # render the same illustrated figure and scene.
        success = generate_one(entry, image_path, seed=42 + i)

        if success:
            entry["image"] = f"sample_{i}.png"
            print(f"  -> saved {image_path}")
        else:
            print(f"  -> failed (likely a memory-related crash; see README). Skipping this one.")

        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    done = sum(1 for e in manifest if e.get("image"))
    print(f"\n{done}/{len(manifest)} samples now have images.")


if __name__ == "__main__":
    main()
