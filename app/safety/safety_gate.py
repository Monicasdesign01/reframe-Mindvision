"""
Crisis / self-harm safety gate.

This runs FIRST, on every single request, before any other processing
(before spaCy, before emotion detection, before narrative generation).

Design intent (explain this in the viva):
- It is deliberately simple: keyword/rule-based, not a learned classifier.
  A rule-based gate is auditable and its failure modes are predictable,
  which matters far more here than recall/precision tradeoffs of a model
  we can't fully explain.
- It is a coarse net on purpose: cheap false positives (routing a benign
  message to the helpline message) are an acceptable cost. False negatives
  (missing real crisis language) are not, so the keyword list favors
  recall over precision.
- FAIL SAFE, NEVER FAIL OPEN: if the screening step itself raises an
  exception for any reason, we treat that exactly like a positive match
  and show the helpline message instead of continuing the pipeline. We
  never let an internal error silently fall through to normal generation.
"""

import re

# Tele-MANAS (India, 24/7 mental health support) and KIRAN (India, national
# mental health rehabilitation helpline) â real, publicly listed numbers.
HELPLINE_MESSAGE = (
    "It sounds like you might be going through something really heavy right now. "
    "You deserve support from a real person, not an app.\n\n"
    "Please reach out right now to:\n"
    "  - Tele-MANAS: 14416 (24/7, India)\n"
    "  - KIRAN Mental Health Helpline: 1800-599-0019 (24/7, India, toll-free)\n\n"
    "If you are in immediate physical danger, please contact local emergency "
    "services right away. You are not alone, and help is available."
)

# Deliberately broad, favors recall. Grouped by theme for maintainability.
_CRISIS_PATTERNS = [
    # Direct suicidal ideation / intent
    r"\bkill(ing)?\s+myself\b",
    r"\bend(ing)?\s+(my\s+life|it\s+all)\b",
    r"\bsuicid(e|al)\b",
    r"\bwant\s+to\s+die\b",
    r"\bwish\s+i\s+(was|were)\s+dead\b",
    r"\bdon'?t\s+want\s+to\s+(be\s+alive|live)\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bbetter\s+off\s+(dead|without\s+me)\b",
    r"\btake\s+my\s+(own\s+)?life\b",
    # Self-harm
    r"\bself[\s-]?harm\b",
    r"\bcutting\s+myself\b",
    r"\bhurt(ing)?\s+myself\b",
    r"\bharm(ing)?\s+myself\b",
    # Method / planning language
    r"\boverdose\b",
    r"\ba\s+plan\s+to\s+(die|kill)\b",
    r"\bgoodbye\s+letter\b",
    r"\bsuicide\s+note\b",
    # Hopelessness combined with finality (context-sensitive but still coarse)
    r"\bcan'?t\s+go\s+on\s+(anymore|any\s*more)\b",
    r"\bno\s+point\s+in\s+(living|continuing)\b",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


def screen_for_crisis(text: str) -> bool:
    """
    Returns True if the text should be treated as a crisis / self-harm risk
    and routed to the static helpline message instead of the normal pipeline.

    Fail-safe: any exception during screening is treated as a positive
    match (returns True) rather than propagating or defaulting to False.
    """
    try:
        if not text or not isinstance(text, str):
            # Empty/invalid input carries no risk signal, but we still
            # want an explicit, intentional False here rather than
            # falling through logic below.
            return False

        for pattern in _COMPILED_PATTERNS:
            if pattern.search(text):
                return True

        return False
    except Exception:
        # Fail safe: never fail open. Any error in screening is treated
        # as if a crisis was detected.
        return True


def get_helpline_message() -> str:
    return HELPLINE_MESSAGE
