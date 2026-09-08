"""
Cognitive distortion detection: spaCy for linguistic parsing (negation,
lemmatization, sentence splitting) + our own hand-written rule set on top.

This is OUR engineering, not a pretrained model. It is intentionally a
simple, explainable rule set rather than a classifier: it needs to be
defensible sentence-by-sentence in the viva, and the space of clearly
worded distortion cues is small enough that rules generalize reasonably
well for a first version.

Five distortions covered (Phase 1): all-or-nothing thinking, fortune
telling, self-labeling, catastrophizing, overgeneralization.
Phase 2 grows this list toward ~15.
"""

import re
import spacy

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# Each rule: (distortion_name, list of regex patterns, human explanation)
_RULES = [
    (
        "all_or_nothing",
        [
            r"\balways\b", r"\bnever\b", r"\bevery\s+(single\s+)?time\b",
            r"\bcompletely\s+(fail|failed|failing|ruined|useless)\b",
            r"\btotal(ly)?\s+(disaster|failure)\b",
            r"\beither\b.*\bor\b",
        ],
        "Seeing a situation in only two extreme categories, with no middle ground.",
    ),
    (
        "fortune_telling",
        [
            r"\bit'?s\s+going\s+to\s+(fail|go\s+wrong|be\s+a\s+disaster)\b",
            r"\bi\s+(know|just\s+know)\s+.*\s+(will|won'?t)\b",
            r"\bthere'?s\s+no\s+way\s+(this|it|i)\s+(will|can|could)\b",
            r"\bi'?m\s+going\s+to\s+(fail|lose|screw\s+up)\b",
            r"\bwill\s+never\s+work\b",
        ],
        "Predicting a negative future as if it were already a fact.",
    ),
    (
        "self_labeling",
        [
            r"\bi'?m\s+(such\s+a\s+|a\s+|an\s+)?(failure|loser|idiot|stupid|worthless|useless|fraud|impostor)\b",
            r"\bi'?m\s+not\s+(good|smart|talented)\s+enough\b",
            r"\bi'?m\s+broken\b",
        ],
        "Attaching a harsh, global label to yourself based on one event or trait.",
    ),
    (
        "catastrophizing",
        [
            r"\bthis\s+is\s+(a\s+)?(catastrophe|disaster|the\s+end)\b",
            r"\beverything\s+is\s+(ruined|falling\s+apart|over)\b",
            r"\bi\s+can'?t\s+(handle|cope\s+with|survive)\s+this\b",
            r"\bworst\s+(thing|case|possible)\b",
            r"\bit'?s\s+all\s+over\b",
        ],
        "Assuming the worst possible outcome and treating it as unbearable.",
    ),
    (
        "overgeneralization",
        [
            r"\bthis\s+always\s+happens\b",
            r"\bnothing\s+ever\s+(works|goes\s+right)\b",
            r"\beveryone\s+(always|thinks|hates)\b",
            r"\bi\s+can'?t\s+do\s+anything\s+right\b",
            r"\bno\s+one\s+(ever|will)\b",
        ],
        "Drawing a broad, permanent conclusion from a single event.",
    ),
]

_COMPILED_RULES = [
    (name, [re.compile(p, re.IGNORECASE) for p in patterns], explanation)
    for name, patterns, explanation in _RULES
]

DISTORTION_EXPLANATIONS = {name: explanation for name, _, explanation in _RULES}


def detect_distortions(text: str) -> list:
    """
    Returns a list of distortion names detected in the text (deduplicated,
    order of first occurrence preserved). Uses spaCy to split into
    sentences first so multi-sentence inputs are checked sentence by
    sentence, then falls back to whole-text matching if spaCy fails.
    """
    if not text or not isinstance(text, str):
        return []

    found = []
    try:
        doc = _get_nlp()(text)
        sentences = [sent.text for sent in doc.sents] or [text]
    except Exception:
        sentences = [text]

    for sentence in sentences:
        for name, patterns, _ in _COMPILED_RULES:
            if name in found:
                continue
            for pattern in patterns:
                if pattern.search(sentence):
                    found.append(name)
                    break

    return found
