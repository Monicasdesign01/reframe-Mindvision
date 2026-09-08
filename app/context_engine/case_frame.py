"""
Case Frame: the single structured object that every downstream stage reads.

Design intent: NLP parsing and emotion detection both write into this frame,
independently of each other. Every later stage (principle selection,
narrative generation) reads ONLY this object, never the raw pipeline
outputs directly. This is what lets the distortion-detection and
emotion-detection modules be developed/tested in isolation, and it gives
us one clean object to log to SQLite per session.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class CaseFrame:
    raw_text: str

    # Filled in by app.nlp.distortions
    distortions: list = field(default_factory=list)          # e.g. ["catastrophizing", "all_or_nothing"]

    # Filled in by app.emotion.classifier
    emotion_scores: dict = field(default_factory=dict)       # {"sadness": 0.62, "fear": 0.21, ...}
    core_emotion: str = ""                                    # top collapsed emotion, e.g. "sadness"

    # Filled in by app.context_engine (this module)
    summary: str = ""

    # Filled in by app.principle_selector
    selected_techniques: list = field(default_factory=list)   # list of technique card ids

    # Filled in by app.context_engine when loading prior sessions
    recurring_theme_note: str = ""

    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def build_summary(self) -> str:
        """One-line human-readable summary of this case frame."""
        emotion_part = f"feeling {self.core_emotion}" if self.core_emotion else "unclear emotion"
        distortion_part = (
            f"showing {', '.join(self.distortions)}" if self.distortions else "no strong distortion pattern"
        )
        self.summary = f"{emotion_part}; {distortion_part}"
        return self.summary

    def to_dict(self) -> dict:
        return asdict(self)
