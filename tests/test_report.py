"""T010 — report.py: CSV/JSON por-evidencia, determinista."""
from pathlib import Path

from src.citefid.models import Verdict
from src.citefid.report import verdicts_to_rows, write_csv, write_json

OUT = Path(__file__).parent.parent / "out_test"
OUT.mkdir(exist_ok=True)


def _verdicts():
    return [
        Verdict(
            claim="claim A",
            per_ev=[{"ev": 0, "entail": 0.6, "contra": 0.1, "support": 0.5},
                    {"ev": 1, "entail": 0.2, "contra": 0.4, "support": -0.2}],
            best_ev=0, support=0.5, veredict="confirm",
        ),
        Verdict(
            claim="claim B",
            per_ev=[{"ev": 0, "error": "huérfana"}],
            best_ev=-1, support=0.0, veredict="neutral",
        ),
    ]


def test_T010_csv_filas_por_par():
    vs = _verdicts()
    rows = write_csv(vs, OUT / "r.csv")
    # claim A tiene 2 evidencias -> 2 filas; claim B tiene 1 -> 1 fila = 3 total
    assert len(rows) == 3, len(rows)


def test_T010_json_per_ev_best_ev():
    vs = _verdicts()
    out = write_json(vs, OUT / "r.json")
    assert "per_ev" in out[0] and "best_ev" in out[0]
    assert out[0]["best_ev"] == 0


def test_T010_determinista():
    vs = _verdicts()
    r1 = verdicts_to_rows(vs)
    r2 = verdicts_to_rows(vs)
    assert r1 == r2  # mismo input -> misma salida
