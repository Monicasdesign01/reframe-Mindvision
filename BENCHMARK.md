# Benchmark Results

Measured with `scripts/benchmark.py` on the development machine (Intel
Core i3-1005G1, 2 cores/4 threads, 3.77GB RAM total, CPU only, no GPU),
using the input: "I always mess everything up and nothing will ever get
better."

| Stage | Time |
|---|---|
| Distortion detection (spaCy + rules) | 2.05s |
| Emotion classification (GoEmotions ONNX) | 0.46s |
| Principle selection | 0.08s |
| Narrative generation (FLAN-T5-base, beam search) | 46.46s |

Narrative generation dominates total latency by a wide margin on this
CPU. Text output (the first thing shown to the user, per the "text
returns immediately" requirement) is available after roughly 49 seconds
end-to-end on this machine.

TTS and image generation are benchmarked separately via
`scripts/benchmark_full.py` since image generation needs more free RAM
than was available during this development session (see README's RAM
note) -- run it yourself with other applications closed for full
end-to-end numbers including audio and image stages.

## What this means for the demo

- ~49s to first text response on this hardware is noticeable but
  tolerable for a live demo; a faster or multi-core CPU will do
  meaningfully better, since narrative generation is the bottleneck and
  benefits directly from more cores.
- Given this latency, the pre-generated fallback sessions
  (`data/samples/`, made with `scripts/pregenerate_samples.py`) are worth
  having ready rather than relying on live generation if the demo room's
  time is tight.
- If a faster demo is needed and a smaller narrative model is acceptable,
  switching to `flan-t5-small` (already supported as a fallback in
  `NarrativeGenerator(use_small=True)`) would reduce this stage's latency
  at some cost to narrative quality.
