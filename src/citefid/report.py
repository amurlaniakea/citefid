"""F005 — Reporte auditable por-evidencia (CSV + JSON).

Una fila por par claim+span individual, con per_ev y best_ev. Determinista.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from .models import Verdict


def verdicts_to_rows(verdicts: List[Verdict]) -> List[dict]:
    rows = []
    for v in verdicts:
        for pe in v.per_ev:
            rows.append({
                "claim": v.claim,
                "ev": pe.get("ev", -1),
                "error": pe.get("error", ""),
                "entail": pe.get("entail", 0.0),
                "contra": pe.get("contra", 0.0),
                "support": pe.get("support", 0.0),
                "best_ev": v.best_ev,
                "veredict": v.veredict,
            })
    return rows


def write_csv(verdicts: List[Verdict], path: str | Path):
    rows = verdicts_to_rows(verdicts)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["claim", "ev", "error", "entail",
                                          "contra", "support", "best_ev", "veredict"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return rows


def write_json(verdicts: List[Verdict], path: str | Path):
    out = [{"claim": v.claim, "best_ev": v.best_ev, "support": v.support,
            "veredict": v.veredict, "per_ev": v.per_ev} for v in verdicts]
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    return out
