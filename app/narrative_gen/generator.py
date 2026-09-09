"""
Narrative generation using google/flan-t5-base (fallback: flan-t5-small),
prompt-engineered only. No training/fine-tuning (hard constraint for
Phases 1-3).

Produces a strict 4-part narrative: current reality -> reframe -> desired
future -> concrete next step. The prompt is engineered to (a) reliably hit
all 4 parts with clear headers we can parse/display, and (b) never promise
a guaranteed outcome ("you will definitely succeed") since that's both
clinically irresponsible and not something the model can know.
"""

import gc
import re

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_MODEL_NAME_PRIMARY = "google/flan-t5-base"
_MODEL_NAME_FALLBACK = "google/flan-t5-small"

_BANNED_PHRASES = [
    "you will definitely", "you'll definitely", "guaranteed to", "i promise you",
    "you will certainly", "100% certain", "will always work out",
]

# FLAN-T5-base's free-form output was observed during testing to
# occasionally hallucinate content unrelated to the prompt, including
# insulting language directed at the reader (e.g. calling them a "cynical
# idiot"). A missing section header isn't the only failure mode worth
# catching, so generated text is also rejected outright (falling back to
# the deterministic template) if it contains any of these.
_HARMFUL_PATTERNS = [
    "idiot", "stupid", "worthless", "pathetic", "loser", "moron", "cynical",
    "hopeless case", "give up", "your fault", "deserve this",
]

# Also observed during testing: the model sometimes just echoes the
# instruction text back verbatim instead of writing a narrative. Since the
# prompt's own instructions literally contain the four required header
# words, an echo passes the header check while containing no real content.
# These phrases are unique to the instructions themselves (never something
# an actual narrative would say), so their presence means the model echoed
# rather than generated.
_ECHO_MARKERS = [
    "describe their situation and feeling",
    "gently introduce the technique above",
    "describe a realistic, modest, positive future",
    "give one small, concrete, doable action",
    "write a short, warm, second-person narrative",
]

_PROMPT_TEMPLATE = """You are a supportive, evidence-informed narrative writer. Someone shared this worry:
"{raw_text}"

Their main emotion is {core_emotion}. A relevant psychological technique is: {technique_name} - {technique_description}
{recurring_theme_line}
Write a short, warm, second-person narrative in exactly four labeled parts. Do not skip any part. Do not promise a guaranteed outcome or use words like "definitely", "guaranteed", or "always". Keep each part to 1-3 sentences.

CURRENT REALITY: describe their situation and feeling with empathy, using their own words where natural.
REFRAME: gently introduce the technique above as one way to look at the thought differently, without dismissing the feeling.
DESIRED FUTURE: describe a realistic, modest, positive future a few days or weeks out if they try this.
NEXT STEP: give one small, concrete, doable action they could take today.

Now write the four parts:
"""


class NarrativeGenerator:
    def __init__(self, use_small: bool = False):
        model_name = _MODEL_NAME_FALLBACK if use_small else _MODEL_NAME_PRIMARY
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        except Exception:
            if use_small:
                raise
            # RAM-discipline fallback: base model failed to load, try small.
            self._tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME_FALLBACK)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME_FALLBACK)

    def generate(self, case_frame, technique: dict) -> str:
        recurring_theme_line = ""
        if getattr(case_frame, "recurring_theme_note", ""):
            recurring_theme_line = (
                f"\nNote: {case_frame.recurring_theme_note}. Gently acknowledge this pattern "
                f"in the CURRENT REALITY part, without being repetitive or discouraging.\n"
            )

        prompt = _PROMPT_TEMPLATE.format(
            raw_text=case_frame.raw_text,
            core_emotion=case_frame.core_emotion or "unclear",
            technique_name=technique["name"],
            technique_description=technique["description"],
            recurring_theme_line=recurring_theme_line,
        )
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=300,
            do_sample=False,
            num_beams=4,
            no_repeat_ngram_size=3,
        )
        text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        text = self._sanitize(text)
        text = self._validate_or_fallback(text, case_frame, technique)
        return text

    def _sanitize(self, text: str) -> str:
        lowered = text.lower()
        for phrase in _BANNED_PHRASES:
            if phrase in lowered:
                # Regenerate is expensive on CPU; instead soften in place.
                idx = lowered.find(phrase)
                text = text[:idx] + "this may help" + text[idx + len(phrase):]
                lowered = text.lower()
        return text

    def _validate_or_fallback(self, text: str, case_frame, technique: dict) -> str:
        """
        FLAN-T5-base's free-form output is not reliable enough to trust
        unconditionally: besides sometimes skipping a required section, it
        was observed during testing to occasionally hallucinate harmful or
        unrelated content, or simply echo the instructions back verbatim.
        Generated text is accepted only if it (a) contains all 4 required
        headers, (b) contains none of the harmful patterns, and (c) isn't
        just an echo of the prompt's own instructions; otherwise a
        deterministic template is used, which guarantees a safe, on-contract
        output regardless of generation quality.
        """
        required = ["CURRENT REALITY", "REFRAME", "DESIRED FUTURE", "NEXT STEP"]
        upper = text.upper()
        lowered = text.lower()
        has_all_headers = all(h in upper for h in required)
        has_harmful_content = any(p in lowered for p in _HARMFUL_PATTERNS)
        is_echo = any(p in lowered for p in _ECHO_MARKERS)

        if has_all_headers and not has_harmful_content and not is_echo:
            return text

        theme_sentence = ""
        if getattr(case_frame, "recurring_theme_note", ""):
            theme_sentence = f" You may notice that {case_frame.recurring_theme_note}."

        return (
            f"CURRENT REALITY: {case_frame.raw_text.strip()} It makes sense that this brings up "
            f"{case_frame.core_emotion or 'difficult feelings'}.{theme_sentence}\n\n"
            f"REFRAME: {technique['name']} suggests looking at this through a different lens: "
            f"{technique['description']}\n\n"
            f"DESIRED FUTURE: With some practice, it's realistic that this could feel a little more "
            f"manageable in the coming days or weeks.\n\n"
            f"NEXT STEP: Try one small action today related to this technique, even a two-minute version of it."
        )

    def unload(self):
        del self._model
        del self._tokenizer
        gc.collect()


_SECTION_HEADERS = ["CURRENT REALITY", "REFRAME", "DESIRED FUTURE", "NEXT STEP"]


def parse_narrative_parts(narrative: str) -> dict:
    """
    Splits a generated narrative into its four labeled parts, keyed
    "current_reality" / "reframe" / "desired_future" / "next_step". Used to
    build the storyboard image's per-panel captions (see
    app/image_gen/storyboard.py). Safe on both the FLAN-T5 output and the
    deterministic fallback template above, since both are guaranteed to
    contain all four headers by _validate_or_fallback.
    """
    pattern = r"(" + "|".join(_SECTION_HEADERS) + r"):\s*"
    pieces = re.split(pattern, narrative)
    parts = {}
    for i in range(1, len(pieces) - 1, 2):
        key = pieces[i].strip().lower().replace(" ", "_")
        parts[key] = pieces[i + 1].strip()
    for key in ("current_reality", "reframe", "desired_future", "next_step"):
        parts.setdefault(key, "")
    return parts
