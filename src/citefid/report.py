"""F005 — Reporte auditable por-evidencia (CSV + JSON).

Una fila por par claim+span individual, con per_ev y best_ev. Determinista.
"""
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
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
