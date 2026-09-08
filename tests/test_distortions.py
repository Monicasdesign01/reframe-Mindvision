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


def test_no_distortion_on_neutral_text():
    assert detect_distortions("I had a sandwich for lunch today.") == []


def test_empty_text_returns_empty_list():
    assert detect_distortions("") == []
