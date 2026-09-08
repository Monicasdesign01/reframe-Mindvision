# Team Brief — Personalized AI Narrative & Voice Generation

## What it does
User types/speaks a worry → we detect the emotion + the distorted thinking
pattern in it → match it to a real psychological technique → generate a
4-part narrative (reality → reframe → desired future → next step) → deliver
as text + image + voice → save it so recurring themes show up over time.

## The pipeline, step by step
1. **Input** — type or record voice (web page, Flask backend)
2. **Speech-to-text** — only runs if they spoke
3. **Safety check** — runs first, always; if crisis language is detected, we
   stop and show helpline numbers instead of generating anything
4. **Language + distortion detection** — spaCy + our own rules
5. **Emotion detection** — pretrained classifier
6. **Case Frame** — one structured object packing steps 4–5 together; every
   later stage only reads this, which is what lets us build modules in
   parallel
7. **Principle Selector** — matches the Case Frame against our knowledge
   base of ~15 evidence-backed technique cards, each with a real citation
8. **Narrative generation** — writes the 4-part story
9. **Delivery** — text shown immediately, then voice, then image (image runs
   in the background so it never blocks the response)
10. **Saved** — everything goes to SQLite; "My Journey" page lets the user
    revisit past sessions

## Models — what we use and why
| Stage | Model | Why this one |
|---|---|---|
| Speech-to-text | faster-whisper (base) | Same Whisper weights, several times faster than plain Whisper on CPU-only laptops |
| Emotion | SamLowe/roberta-base-go_emotions (ONNX, quantized) | Free, MIT-licensed, already trained on GoEmotions (28 emotion labels) — no training needed, ONNX version is fast on CPU |
| Narrative | FLAN-T5-base, prompt-engineered | Free, Apache-licensed, good instruction-following at a size that still runs on CPU. We are **not** fine-tuning this — see "what changed" below |
| Image | Stable Diffusion Turbo | Only mainstream model that can produce a usable image in 1–4 steps, which is what makes CPU image generation possible at all in a demo timeframe |
| Voice | Kokoro-82M | Apache-licensed, 82M params, currently rated highest quality-for-size of the free TTS options; the originally-planned Coqui TTS is from a company that shut down in Jan 2024 and its repo is no longer maintained |

## What changed from the original plan, and why
- **Coqui TTS → Kokoro-82M.** Coqui's company shut down; the toolkit isn't
  actively maintained anymore. Kokoro is newer, Apache-licensed, and faster.
- **Plain Whisper → faster-whisper.** Same model, much faster on CPU —
  matters since we have no GPU.
- **RoBERTa ONNX instead of the raw PyTorch model.** Meaningfully faster on
  CPU with no accuracy loss, same free/MIT license.
- **No fine-tuning of DistilBERT or FLAN-T5+LoRA in the core build.** The
  original brief for the build (zero training, all pretrained) and the
  presentation deck (claims we fine-tune two models) contradicted each
  other. Fine-tuning FLAN-T5 with LoRA on a CPU-only laptop, under a
  deadline, with a hand-built 500-example dataset, is a real risk to
  finishing on time. **Recommendation: skip it.** Our actual contribution —
  the distortion rules, the Case Frame, the Principle Selector + knowledge
  base with real citations, and the safety gate — is a legitimate, defensible
  answer to "did you actually build anything, or just call APIs?" without
  needing to claim training we didn't reliably do. If there's spare time
  after the core build works, fine-tuning DistilBERT on GoEmotions alone is
  realistic on CPU (small model, a few hours) — that's the one stretch goal
  worth attempting, and it's optional.
- **SD-Turbo license note.** It's free but non-commercial-only and
  "gated" on Hugging Face — whoever runs the download needs a free HF
  account and to click "accept" on the model page once. Worth knowing
  before the demo, and worth being able to explain if asked in the viva.

## Before anyone starts building (Windows 11 checklist)
- Python **3.11** in a venv (not the newest Python — some packages don't
  have Windows wheels for it yet)
- Install **ffmpeg** and **espeak-ng** as system binaries, add both to PATH
  (needed by Whisper and Kokoro respectively)
- Create a free Hugging Face account, accept the SD-Turbo license, run
  `huggingface-cli login` once
- Check available RAM (Settings → System → About). Under 8GB free: stick to
  the smallest model variants and expect image generation to take up to a
  minute per image — always have the pre-generated fallback images ready
  for the live demo
- Docker is optional for local dev; only needed for the final submission
  packaging, and requires WSL2 enabled if you want to try it

## Pre-generate before the demo
2–3 full example sessions (text + image + audio) saved as a fallback, in
case live inference is too slow in the room.
