"""
Emotion detection: SamLowe/roberta-base-go_emotions-onnx (int8 quantized),
run via ONNX Runtime for CPU speed, MIT licensed, pretrained as-is (no
fine-tuning).

The 28 GoEmotions labels -> our 6 core emotions mapping (EMOTION_MAP below,
and collapse_to_core_emotion) is OUR CODE, written because the rest of the
pipeline (principle selector, narrative prompts) needs a small, stable
vocabulary rather than 28 fine-grained labels.
"""

import gc

from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer, pipeline

_MODEL_NAME = "SamLowe/roberta-base-go_emotions-onnx"

# GoEmotions' 28 labels collapsed to 6 core emotions the rest of the
# pipeline reasons about. "neutral" is kept as its own bucket rather than
# folded into another emotion, since forcing a neutral utterance into e.g.
# "sadness" would corrupt downstream technique matching.
EMOTION_MAP = {
    "sadness": "sadness", "grief": "sadness", "remorse": "sadness",
    "disappointment": "sadness", "embarrassment": "sadness",

    # GoEmotions has no literal "anxiety" label; nervousness is the closest
    # match, so both nervousness and fear feed the "fear" bucket, and the
    # knowledge base's anxiety-oriented cards key off this bucket too.
    "fear": "fear", "nervousness": "fear",

    "anger": "anger", "annoyance": "anger", "disgust": "anger", "disapproval": "anger",

    "joy": "joy", "amusement": "joy", "excitement": "joy", "gratitude": "joy",
    "love": "joy", "optimism": "joy", "pride": "joy", "relief": "joy",
    "admiration": "joy", "approval": "joy", "caring": "joy", "desire": "joy",

    "surprise": "surprise", "realization": "surprise", "curiosity": "surprise", "confusion": "surprise",

    "neutral": "neutral",
}

CORE_EMOTIONS = ["sadness", "fear", "anger", "joy", "surprise", "neutral"]


class EmotionClassifier:
    """
    Load on demand, release after use, per the RAM-discipline requirement.
    Usage:
        clf = EmotionClassifier()
        scores, core = clf.classify("I feel like nothing ever works out")
        clf.unload()
    """

    def __init__(self):
        self._tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        # The repo hosts both a full-precision and an int8-quantized ONNX
        # file; explicitly select the quantized one for CPU speed.
        self._model = ORTModelForSequenceClassification.from_pretrained(
            _MODEL_NAME, file_name="onnx/model_quantized.onnx"
        )
        self._pipe = pipeline(
            "text-classification",
            model=self._model,
            tokenizer=self._tokenizer,
            top_k=None,
            function_to_apply="sigmoid",
        )

    def classify(self, text: str):
        """
        Returns (raw_scores: dict[label -> float], core_emotion: str).
        raw_scores contains all 28 GoEmotions labels with their scores.
        core_emotion is the collapsed label with the highest aggregated
        score across the 6 core buckets.
        """
        results = self._pipe(text)[0]  # list of {"label":.., "score":..}
        raw_scores = {r["label"]: float(r["score"]) for r in results}

        core_totals = {c: 0.0 for c in CORE_EMOTIONS}
        for label, score in raw_scores.items():
            core = EMOTION_MAP.get(label, "neutral")
            core_totals[core] += score

        core_emotion = max(core_totals, key=core_totals.get)
        return raw_scores, core_emotion

    def unload(self):
        del self._pipe
        del self._model
        del self._tokenizer
        gc.collect()
