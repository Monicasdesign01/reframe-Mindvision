"""
Adds images to the manifest produced by pregenerate_samples.py, one at a
time, each in its own subprocess. A subprocess crash (e.g. the SD-Turbo
VAE-decode segfault seen on low-RAM machines -- see README) only loses
that one image; the manifest and every other sample are unaffected.

Run after pregenerate_samples.py, ideally with other applications closed
to free RAM:
    python scripts/pregenerate_images.py
"""

import sys
import os
import json
import subprocess

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")
MANIFEST_PATH = os.path.join(OUT_DIR, "manifest.json")

_WORKER_CODE = """
import sys
sys.path.insert(0, {project_root!r})
from app.image_gen.generator import ImageGenerator

gen = ImageGenerator()
gen.generate({prompt!r}, {output_path!r})
gen.unload()
print("OK")
"""


def generate_one(prompt: str, output_path: str) -> bool:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = _WORKER_CODE.format(project_root=project_root, prompt=prompt, output_path=output_path)
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
        print(f"[{i}/{len(manifest)}] generating image...")
        success = generate_one(entry["image_prompt"], image_path)

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
