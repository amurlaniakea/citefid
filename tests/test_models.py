"""T001 — models.py es la única fuente de verdad de Claim/Evidence/Verdict."""
from src.citefid.models import Claim, Evidence, Verdict


def test_import_desde_models():
    # las 3 dataclasses existen y son importables
    assert Claim is not None and Evidence is not None and Verdict is not None


def test_claim_acepta_n_evidencias():
    evs = [
        Evidence(raw="a", span="x"),
        Evidence(raw="b", span="y"),
        Evidence(raw="c", span="z"),
    ]
    c = Claim(text="el claim", evidences=evs)
    assert len(c.evidences) == 3  # no solo [0]


def test_verdict_campos():
    v = Verdict(claim="c", per_ev=[{"entail": 0.5}], best_ev=0, support=0.1, veredict="confirm")
    assert v.best_ev == 0 and v.support == 0.1 and v.veredict == "confirm"
