import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.context_engine.case_frame import CaseFrame
from app.principle_selector.selector import select_techniques


def test_selects_technique_matching_distortion_and_emotion():
    cf = CaseFrame(raw_text="test", distortions=["catastrophizing"], core_emotion="fear")
    results = select_techniques(cf)
    assert len(results) > 0
    ids = [c["id"] for c in results]
    assert "decatastrophizing" in ids or "behavioral_experiment" in ids
    assert cf.selected_techniques == ids


def test_falls_back_when_nothing_matches():
    cf = CaseFrame(raw_text="test", distortions=[], core_emotion="joy")
    results = select_techniques(cf)
    assert len(results) == 1


def test_top_n_respected():
    cf = CaseFrame(raw_text="test", distortions=["catastrophizing", "all_or_nothing", "fortune_telling"], core_emotion="fear")
    results = select_techniques(cf, top_n=2)
    assert len(results) <= 2
