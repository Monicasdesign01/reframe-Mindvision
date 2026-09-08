# Reframe — Personalized AI-Based Narrative Content Creation and Voice Generation

A user types or speaks a worry. The system runs a safety screen, detects
emotion and cognitive distortions, matches an evidence-based psychological
technique, generates a 4-part personalized narrative, and delivers it as
text, a generated image, and narrated voice. Sessions are saved so the
system can surface recurring themes over time.

See [DESIGN.md](DESIGN.md) for what is pretrained-as-is vs. our own
engineering.

## Requirements

- **Windows 11**, CPU only (no GPU needed/used)
- **Python 3.11** specifically (not 3.12/3.13/3.14 — some packages here
  don't reliably have Windows wheels yet on newer Python)
- **ffmpeg** on PATH (used by faster-whisper)
- A free **Hugging Face account** (needed once, for SD-Turbo — see below)

Note: espeak-ng (needed by Kokoro's phonemizer) does **not** need a separate
system install — the `kokoro`/`misaki` pip packages pull in
`espeakng-loader`, which bundles the espeak-ng library and data files and
wires them up automatically.
- ~3-5GB free disk space for model weights (downloaded on first run, not
  bundled in this repo)

## Setup (Windows, from scratch)

```powershell
# 1. Install Python 3.11 if you don't have it
winget install --id Python.Python.3.11 -e

# 2. Install ffmpeg (espeak-ng is bundled via the kokoro/misaki pip packages, no separate install needed)
winget install --id Gyan.FFmpeg -e
# Restart your terminal after this so PATH updates take effect.

# 3. Create and activate the venv (use the 3.11 launcher explicitly)
py -3.11 -m venv venv
venv\Scripts\activate

# 4. Install CPU-only PyTorch first, then the rest
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 5. Download the spaCy English model
python -m spacy download en_core_web_sm

# 6. Hugging Face login (required once, for SD-Turbo — it is gated)
#    - Create a free account at huggingface.co
#    - Visit https://huggingface.co/stabilityai/sd-turbo and click "Agree"
#    - Create an access token at huggingface.co/settings/tokens
huggingface-cli login

# 7. Run the app
python -m app.main
```

Then open http://127.0.0.1:5000 in a browser.

## What downloads on first run (approximate sizes)

| Model | Approx. size | When it downloads |
|---|---|---|
| faster-whisper `base` | ~150MB | first time you submit audio |
| RoBERTa GoEmotions ONNX (int8) | ~110MB | on app startup |
| FLAN-T5-base | ~950MB | first time you submit a (non-crisis) worry |
| SD-Turbo | ~2.5GB (fp32 on CPU) | first background image generation |
| Kokoro-82M | ~330MB | first narration |

Total: roughly 3.5-4GB. All are cached locally by Hugging Face after the
first download (default cache: `~/.cache/huggingface`).

## A note on RAM if image generation crashes

SD-Turbo's VAE-decode step needs real headroom (roughly 2-3GB free even at
the reduced 256x256 resolution this project uses by default, more at
512x512). If image generation segfaults, it is almost always a failed
native memory allocation under memory pressure, not a code bug -- this was
observed directly during development on a 3.77GB-RAM laptop, where the
crash disappeared once enough RAM was freed. If you hit this:

- Close other applications, especially browsers and IDEs, before running
  the app -- an IDE/editor session can itself hold several hundred MB.
- Run `python -m app.main` from a plain terminal rather than from inside
  an editor's integrated terminal or AI coding assistant, since those add
  their own memory overhead on top of Python's.
- If it still crashes, lower `IMAGE_SIZE` in `app/image_gen/generator.py`
  (e.g. to 128), or treat image generation as a "works when RAM allows"
  feature and rely on the pre-generated sample sessions
  (`scripts/pregenerate_samples.py`) for the demo.

## Running with Docker (optional; requires Docker Desktop + WSL2)

```powershell
docker build -t reframe .
docker run -p 5000:5000 -v %USERPROFILE%\.cache\huggingface:/root/.cache/huggingface reframe
```

The venv-based setup above is the primary, tested way to run this project.
Docker packaging is provided for submission but has a harder dependency
(WSL2 backend enabled) — verify it works on your machine well before
relying on it for the demo.

## Benchmarking

```powershell
python scripts/benchmark.py "I feel like nothing I do is ever good enough"
```

Prints per-stage latency (STT if applicable / emotion / narrative / TTS /
image) so real demo latency is known in advance.

## Project structure

```
app/
  asr/                speech-to-text (faster-whisper)
  nlp/                 distortion detection rules + spaCy
  emotion/             GoEmotions ONNX classifier + core-emotion mapping
  context_engine/      Case Frame
  principle_selector/  knowledge-base matching
  narrative_gen/       FLAN-T5 prompted narrative generation
  image_gen/           SD-Turbo
  tts/                 Kokoro narration
  db/                  SQLite schema + repository
  safety/              crisis/self-harm screening gate
  templates/, static/  Flask frontend
data/
  knowledge_base/techniques.json   the ~8-15 technique cards with citations
  sessions/                        SQLite DB + generated audio/image files
  samples/                         pre-generated example sessions for demo fallback
scripts/
  benchmark.py         per-stage latency benchmark
```
