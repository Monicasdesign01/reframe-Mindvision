import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp.distortions import detect_distortions


def test_detects_all_or_nothing():
    assert "all_or_nothing" in detect_distortions("This is a total disaster and always happens.")


def test_detects_fortune_telling():
    assert "fortune_telling" in detect_distortions("I know it's going to fail no matter what I do.")


def test_detects_self_labeling():
    assert "self_labeling" in detect_distortions("I'm such a failure at everything.")


def test_detects_catastrophizing():
    assert "catastrophizing" in detect_distortions("Everything is falling apart, this is the end.")


def test_detects_overgeneralization():
    assert "overgeneralization" in detect_distortions("Nothing ever works out for me.")


def test_detects_mind_reading():
    assert "mind_reading" in detect_distortions("They must think I'm so incompetent.")


def test_detects_mental_filter():
    assert "mental_filter" in detect_distortions("All I can see is the bad in this whole situation.")


def test_detects_disqualifying_positive():
    assert "disqualifying_positive" in detect_distortions("It was just luck, that doesn't count.")


def test_detects_magnification_minimization():
    assert "magnification_minimization" in detect_distortions("This is way blown out of proportion.")


def test_detects_emotional_reasoning():
    assert "emotional_reasoning" in detect_distortions("I feel like a failure, so I must be one.")


def test_detects_should_statements():
    assert "should_statements" in detect_distortions("I should have been better prepared for this.")


def test_detects_personalization():
    assert "personalization" in detect_distortions("It's all my fault that this happened.")


def test_detects_blaming():
    assert "blaming" in detect_distortions("It's all his fault that I feel this way.")


def test_detects_comparison():
    assert "comparison" in detect_distortions("Everyone else is so much more successful than me.")


def test_detects_control_fallacy():
    assert "control_fallacy" in detect_distortions("I have no control over anything in my life.")


def test_no_distortion_on_neutral_text():
    assert detect_distortions("I had a sandwich for lunch today.") == []


def test_empty_text_returns_empty_list():
    assert detect_distortions("") == []
