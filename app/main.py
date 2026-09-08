"""
Flask orchestrator. Wires the pipeline stages together in order:

  input -> (ASR if audio) -> safety gate -> distortion detection ->
  emotion detection -> Case Frame -> principle selector ->
  narrative generation -> [text returned] -> TTS (sync) ->
  image generation (background thread) -> save to SQLite

RAM discipline: spaCy and the emotion classifier stay resident across
requests (small). Whisper, FLAN-T5, SD-Turbo, and Kokoro are loaded only
for the stage that needs them and released (`del model; gc.collect()`)
immediately after, since a typical student laptop can't hold all five in
memory at once.
"""

import gc
import os
import threading
import time
import uuid

from flask import Flask, request, jsonify, render_template, send_from_directory

from app.safety.safety_gate import screen_for_crisis, get_helpline_message
from app.nlp.distortions import detect_distortions
from app.emotion.classifier import EmotionClassifier
from app.context_engine.case_frame import CaseFrame
from app.principle_selector.selector import select_techniques
from app.narrative_gen.generator import NarrativeGenerator
from app.db.schema import init_db
from app.db import repository

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "data", "sessions")
os.makedirs(MEDIA_DIR, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
init_db()

# Emotion classifier + spaCy (via distortions module) stay resident.
_emotion_classifier = EmotionClassifier()

# Tracks in-flight background image generation per session id.
_image_status = {}  # session_id(str) -> {"status": "pending"|"done"|"error", "path": str|None}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/journey")
def journey():
    sessions = repository.list_sessions()
    recurring = repository.find_recurring_themes()
    return render_template("journey.html", sessions=sessions, recurring=recurring)


@app.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_DIR, filename)


@app.route("/process", methods=["POST"])
def process():
    text = request.form.get("text", "").strip()
    audio_file = request.files.get("audio")

    if audio_file and not text:
        text = _transcribe_audio(audio_file)

    if not text:
        return jsonify({"error": "No text or audio provided."}), 400

    # 1. Safety gate — ALWAYS FIRST, fail-safe.
    if screen_for_crisis(text):
        return jsonify({
            "crisis": True,
            "message": get_helpline_message(),
        })

    # 2. Cache check (Phase 2): identical repeated input skips full pipeline.
    cached = _check_cache(text)
    if cached:
        return jsonify(cached)

    # 3. Distortion detection.
    distortions = detect_distortions(text)

    # 4. Emotion detection (resident classifier).
    emotion_scores, core_emotion = _emotion_classifier.classify(text)

    # 5. Case Frame.
    case_frame = CaseFrame(raw_text=text, distortions=distortions,
                            emotion_scores=emotion_scores, core_emotion=core_emotion)
    case_frame.build_summary()

    # 6. Principle selection.
    techniques = select_techniques(case_frame)
    primary_technique = techniques[0]

    # 7. Narrative generation (load -> use -> release).
    generator = NarrativeGenerator()
    try:
        narrative = generator.generate(case_frame, primary_technique)
    finally:
        generator.unload()

    # 8. Save to DB now (audio/image paths filled in below/async).
    session_id = repository.save_session(case_frame, narrative)

    # 9. TTS synchronously (fast enough not to block the response).
    audio_path = _run_tts(session_id, narrative)

    # 10. Image generation in background thread; frontend polls /image_status.
    _image_status[str(session_id)] = {"status": "pending", "path": None}
    image_prompt = _build_image_prompt(case_frame, primary_technique)
    threading.Thread(
        target=_generate_image_background,
        args=(session_id, image_prompt),
        daemon=True,
    ).start()

    response = {
        "crisis": False,
        "session_id": session_id,
        "summary": case_frame.summary,
        "distortions": case_frame.distortions,
        "core_emotion": case_frame.core_emotion,
        "technique": {"name": primary_technique["name"], "citation": primary_technique["citation"]},
        "narrative": narrative,
        "audio_url": f"/media/{os.path.basename(audio_path)}" if audio_path else None,
        "image_status_url": f"/image_status/{session_id}",
    }
    _simple_cache[text.strip().lower()] = response
    return jsonify(response)


@app.route("/image_status/<int:session_id>")
def image_status(session_id):
    status = _image_status.get(str(session_id), {"status": "unknown", "path": None})
    resp = {"status": status["status"]}
    if status["status"] == "done" and status["path"]:
        resp["image_url"] = f"/media/{os.path.basename(status['path'])}"
    return jsonify(resp)


# ---- helpers ----

_simple_cache = {}  # exact text -> response dict (Phase 2 requirement)


def _check_cache(text: str):
    return _simple_cache.get(text.strip().lower())


def _transcribe_audio(audio_file) -> str:
    from app.asr.transcriber import Transcriber

    tmp_path = os.path.join(MEDIA_DIR, f"upload_{uuid.uuid4().hex}.wav")
    audio_file.save(tmp_path)
    transcriber = Transcriber()
    try:
        text = transcriber.transcribe(tmp_path)
    finally:
        transcriber.unload()
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    return text


def _run_tts(session_id: int, narrative: str) -> str:
    from app.tts.narrator import Narrator

    output_path = os.path.join(MEDIA_DIR, f"session_{session_id}.wav")
    narrator = Narrator()
    try:
        narrator.narrate(narrative, output_path)
    except Exception:
        return None
    finally:
        narrator.unload()
    return output_path


def _build_image_prompt(case_frame, technique) -> str:
    from app.image_gen.generator import build_image_prompt
    return build_image_prompt(case_frame, technique)


def _generate_image_background(session_id: int, prompt: str):
    from app.image_gen.generator import ImageGenerator

    output_path = os.path.join(MEDIA_DIR, f"session_{session_id}.png")
    try:
        generator = ImageGenerator()
        try:
            generator.generate(prompt, output_path)
        finally:
            generator.unload()
        repository.update_image_path(session_id, output_path)
        _image_status[str(session_id)] = {"status": "done", "path": output_path}
    except Exception as e:
        _image_status[str(session_id)] = {"status": "error", "path": None, "error": str(e)}


if __name__ == "__main__":
    app.run(debug=True, port=5000)
