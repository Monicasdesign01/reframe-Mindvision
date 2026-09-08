# Design Notes

## (a) Pretrained-as-is components (no training, used exactly as published)

| Component | Model | License |
|---|---|---|
| Speech-to-text | faster-whisper `base` (CTranslate2 build of Whisper) | MIT |
| Emotion classification | `SamLowe/roberta-base-go_emotions-onnx` (int8 quantized) | MIT |
| Narrative generation | `google/flan-t5-base` (prompt-engineered, no fine-tuning) | Apache-2.0 |
| Image generation | `stabilityai/sd-turbo` | Stability AI Community/Research License (non-commercial) |
| Voice narration | Kokoro-82M | Apache-2.0 |

None of these five models were trained or fine-tuned. Each is loaded from its
publisher's published weights and used through standard inference calls.

## (b) Our own engineering (what gets defended in the viva)

1. **Safety gate** (`app/safety/safety_gate.py`) — rule-based crisis/self-harm
   screener that runs first on every request, fails safe (any internal error
   is treated as a positive match), and routes to a static helpline message.
   Deliberately not a learned classifier: auditability and predictable
   failure modes matter more here than precision/recall tuning.

2. **Distortion detection rules** (`app/nlp/distortions.py`) — hand-written
   regex rule set, layered on top of spaCy sentence splitting, covering five
   (Phase 1) to ~15 (Phase 2) CBT-style cognitive distortions. Not a
   pretrained classifier — chosen so every match is explainable sentence by
   sentence.

3. **Emotion-label mapping layer** (`app/emotion/classifier.py`,
   `EMOTION_MAP`) — our own collapsing of GoEmotions' 28 fine-grained labels
   down to 6 core emotions the rest of the pipeline reasons about. The
   underlying classifier is pretrained; this mapping is not.

4. **Context Engine / Case Frame** (`app/context_engine/case_frame.py`) — a
   single structured object that every downstream stage reads from, never
   from raw pipeline outputs directly. This is the seam that let
   distortion-detection and emotion-detection be built and tested
   independently of narrative generation.

5. **Knowledge base + Principle Selector**
   (`data/knowledge_base/techniques.json`,
   `app/principle_selector/selector.py`) — 8 (Phase 1, toward 15 in Phase 2)
   hand-curated technique cards, each with a real, checkable citation, and a
   transparent, explainable scoring function (not a learned ranker) that
   matches a Case Frame to 1-3 relevant cards.

6. **Narrative prompt engineering + output contract enforcement**
   (`app/narrative_gen/generator.py`) — the four-part prompt template, a
   banned-phrase sanitizer (no "you will definitely succeed" language), and
   a deterministic fallback template that guarantees the four-part
   structure even when the model's free-form output doesn't include all
   four headers.

7. **Overall system design** — the "load only what's needed, release
   immediately" RAM-discipline pattern; the synchronous-text /
   synchronous-audio / background-thread-image split with a polling
   endpoint; the SQLite session log and Phase 2 recurring-theme signal
   (`app/db/repository.find_recurring_themes`); and the exact-match response
   cache.

## Why no fine-tuning in the core build

The original brief for the pipeline build said "all pretrained, zero
training." A separate presentation deck referenced fine-tuning two models.
These contradict each other. Under CPU-only hardware and a real deadline,
LoRA fine-tuning FLAN-T5 is high-risk (LoRA training is normally done on
GPU, and building + quality-checking a ~500-example dataset is itself a
multi-day task) and is not attempted here. Fine-tuning DistilBERT on
GoEmotions is realistic on CPU in a few hours and is the one Phase 4
stretch goal worth attempting if time remains — it is optional and was not
started as part of the core, tested Phase 1-3 build.
