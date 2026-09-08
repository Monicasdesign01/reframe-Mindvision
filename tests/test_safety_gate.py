import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.safety.safety_gate import screen_for_crisis


def test_flags_direct_suicidal_ideation():
    assert screen_for_crisis("I want to kill myself") is True


def test_flags_self_harm():
    assert screen_for_crisis("I've been cutting myself again") is True


def test_does_not_flag_benign_text():
    assert screen_for_crisis("I'm worried about my presentation tomorrow") is False


def test_empty_text_is_safe():
    assert screen_for_crisis("") is False


def test_none_input_does_not_crash():
    assert screen_for_crisis(None) is False


def test_fails_safe_on_internal_error(monkeypatch):
    import app.safety.safety_gate as gate

    def broken_search(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(gate, "_COMPILED_PATTERNS", [type("P", (), {"search": broken_search})()])
    assert screen_for_crisis("anything") is True
