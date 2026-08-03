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
