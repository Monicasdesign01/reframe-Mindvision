# Build Prompt for Claude Code — Paste this in as-is

Build a complete, working final-year ML project end to end. Work straight
through Phase 1 → 2 → 3 without checking in with me, except for the explicit
STOP conditions listed below. Commit to git at each meaningful milestone.

## PROJECT
"Personalized AI-Based Narrative Content Creation and Voice Generation Using
Generative AI." A user types or speaks a worry. The system detects the
emotion and cognitive distortion in it, matches it against a small
evidence-based library of psychological techniques, generates a 4-part
personalized narrative (current reality → reframe → desired future →
concrete next step), and delivers it as text, a generated image, and
narrated voice. Sessions are saved so the system can notice recurring
themes over time.

## ENVIRONMENT
Windows 11, CPU only, no GPU. Pin **Python 3.11** (not 3.13 — some of the
packages below don't reliably have Windows wheels yet on the newest
Python). Zero paid APIs, zero paid compute.

## HARD CONSTRAINT: no training in Phases 1–3
Every model below is used exactly as pretrained/pre-fine-tuned by its
publisher. Do not train or fine-tune anything in Phase 1, 2, or 3. (There
is an optional, clearly-separated Phase 4 stretch goal at the end — do not
start it until 1–3 are done, tested, and committed.)

## CORRECTED TECH STACK — use this table, not any older version of it
| Stage | Model / library | Notes |
|---|---|---|
| Backend | Python + Flask | orchestrator only |
| Speech-to-text | **faster-whisper**, `base` model (CTranslate2 build of Whisper) | drop-in replacement for the original `openai-whisper` package — same weights, several times faster on CPU. Use `openai-whisper` only if `faster-whisper` fails to install. |
| NLP parsing | spaCy `en_core_web_sm` + hand-written distortion rules | as originally specced |
| Emotion detection | `SamLowe/roberta-base-go_emotions` — **use the `-onnx` int8 quantized variant** (`SamLowe/roberta-base-go_emotions-onnx`) for CPU speed | MIT license, 28 GoEmotions labels. Write a mapping layer (OUR CODE) that collapses the 28 labels down to the 5–6 core emotions the rest of the pipeline needs. |
| Narrative generation | `google/flan-t5-base` (fall back to `-small` if RAM is tight), prompt-engineered only | no LoRA training — see Phase 4 note |
| Image generation | `stabilityai/sd-turbo`, 512×512, 1 step by default (raise to 2–4 only if quality demands it and latency allows) | **Non-commercial research license** (Stability AI Community License) — fine for an academic project, but say so if asked in the viva. Also **gated on Hugging Face**: you must create a free HF account, accept the license on the model page, and run `huggingface-cli login` with an access token before the first download. If this blocks you, STOP and tell me — don't substitute a different image model silently. |
| Voice narration | **Kokoro-82M** (not Coqui TTS) | Apache-2.0, ~82M params, noticeably faster and better-maintained than Coqui on CPU. `pip install kokoro` + also install the **espeak-ng** Windows binary and add it to PATH (required dependency). Coqui TTS's original company shut down in Jan 2024 and the upstream repo is unmaintained — only use it if Kokoro genuinely fails on this machine, and prefer the community-maintained fork (`idiap/coqui-ai-TTS`, pip name `coqui-tts`) over the dead original package. |
| Storage | SQLite | as originally specced |
| Packaging | Docker | needs **Docker Desktop with the WSL2 backend** enabled on Windows 11 — check this works before relying on it for submission; keep a non-Docker "run with venv" path as the primary, tested way to run the project |
| Version control | Git | commit at each milestone |

## HARD SAFETY REQUIREMENT (unchanged, non-negotiable)
Before any other processing, run a crisis/self-harm screening step
(keyword/rule-based, checked first, on every single request). If triggered,
skip generation entirely and show a static message with real helpline
numbers (Tele-MANAS 14416, KIRAN 1800-599-0019). If the screening step
itself errors, treat that as a trigger — fail safe, never fail open.
Comment this code clearly; it needs to be explained in the viva.

## RAM DISCIPLINE (Windows laptop, unknown exact spec — design defensively)
Do not assume all five models can sit in memory at once on a typical
student laptop. Load a model only for the stage that needs it, run
inference, then release it (`del model; gc.collect()`) before loading the
next one — except spaCy and the emotion classifier, which are small enough
to stay resident for the whole request. Default to the smaller model
variant (`flan-t5-small`, Whisper `base` not `large`) and only suggest
upsizing if I confirm I have 16GB+ RAM.

## PHASE 1 — End-to-end pipeline, all pretrained models
- Flask app: text box, mic upload, output display
- faster-whisper for speech-to-text (skip entirely if the user typed instead)
- Safety gate (see above)
- spaCy parsing + the distortion rule set (all-or-nothing thinking, fortune
  telling, self-labeling, catastrophizing, overgeneralization)
- GoEmotions ONNX classifier + the 28→core-emotion mapping layer
- Context Engine: a plain Python "Case Frame" object bundling raw text,
  emotion scores, distortions, one-line summary — every later stage reads
  only this object
- Knowledge base: 6–8 concept cards (technique name, what it is, one real
  citation, when it applies, limitations). Flag any card if you're not
  fully confident the citation is real — never invent one.
- Matching logic: Case Frame → 1–3 relevant technique cards
- FLAN-T5 prompted for the strict 4-part narrative. Iterate on the prompt
  yourself until it reliably hits all 4 parts and never makes empty
  promises like "you'll definitely succeed."
- Text response returns to the user **immediately** — don't block on audio
  or image. Run TTS synchronously right after (it's fast), and run
  SD-Turbo image generation in a background thread; have the frontend poll
  a simple `/image_status/<session_id>` endpoint every couple of seconds
  and swap the image in when ready.
- SQLite table: input text, emotion scores, distortions, technique(s)
  chosen, narrative, image path, audio path, timestamp
- Done = I can run this locally and go from typing a worry to seeing
  text + image + hearing narration

## PHASE 2 — Expand and integrate
- Grow the distortion rules and knowledge-base cards toward ~15 techniques
- "My Journey" page: list past sessions, reopen any of them, surface a
  simple recurring-theme signal (e.g. "career confidence has come up 3
  times") that gets included in future narrative prompts
- Cache identical repeated inputs so they don't re-run the full pipeline

## PHASE 3 — Polish for submission
- `requirements.txt` and a README with exact Windows setup/run
  instructions, including: Python 3.11 venv setup, the HF token/login step
  for SD-Turbo, the espeak-ng install step for Kokoro, and which model
  files download on first run (and their approximate sizes)
- Dockerfile, with a note that it needs WSL2 on Windows
- `DESIGN.md` explicitly separating (a) pretrained-as-is components vs.
  (b) our own engineering — distortion rules, Context Engine, Principle
  Selector + knowledge base, the emotion-label mapping layer, the safety
  gate, and overall system design. This is what gets defended in the viva.
- Pre-generate 2–3 example sessions (text + image + audio) as a fallback
  to show live if real-time inference is too slow during the demo
- A benchmark script that times one full request end-to-end on this
  machine, split out per stage (STT / emotion / narrative / TTS / image),
  so real demo latency is known in advance, not guessed

## PHASE 4 — Optional stretch, only after 1–3 are fully working
Only attempt this if there's real time left before the deadline. Ask me
before starting either sub-part:
- **DistilBERT fine-tuning on GoEmotions** (swap in for the pretrained
  RoBERTa classifier): realistic on CPU with a subset of GoEmotions and a
  handful of epochs — this is the one that can genuinely be finished in a
  few hours. Evaluate with macro-F1.
- **FLAN-T5 + LoRA fine-tuning on a custom ~500-example dataset**: this is
  **not recommended** on CPU-only hardware under deadline pressure — LoRA
  training is normally done on a GPU, and building + quality-checking 500
  examples is itself a multi-day task. If we don't do this, the narrative
  generator stays prompt-engineered-only, and that's a legitimate design
  choice, not a weaker one — say so plainly rather than pretending it's
  been fine-tuned.

## CONSTRAINTS
- Modular code: separate modules per stage (`asr`, `nlp`, `emotion`,
  `context_engine`, `principle_selector`, `narrative_gen`, `image_gen`,
  `tts`, `db`) — not one big script
- Install the CPU-only PyTorch build, not a CUDA build
- Confirm with me before downloading anything unusually large (multi-GB)

## STOP AND ASK ME IF:
- A chosen pretrained model turns out to be gated behind payment (not just
  a free HF license-click — actual payment) or otherwise inaccessible
- A package genuinely won't install after reasonable troubleshooting
- Free disk space looks too low for the model files (Whisper base + RoBERTa
  ONNX + FLAN-T5-base + SD-Turbo + Kokoro is roughly 3–5GB combined —
  confirm there's headroom before Phase 1 downloads start)

Otherwise, work straight through. Give me progress notes at the end of
each phase, and a final "how to run it" walkthrough when Phase 3 is done.
