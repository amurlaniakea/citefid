#!/usr/bin/env python
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
"""Reproduce el AUC de citefid sobre el dataset público de evaluación.

Uso:
    pip install -e ".[dev]"
    python evaluation/evaluate.py

Mide AUC (fiel vs infiel) del score de NLI sobre el pasaje recuperado,
usando el dataset evaluation/dataset.json (206 pares de un claim-ledger
real de crossplane, spans recortados a rango de líneas).

El label del modelo NLI se resuelve POR NOMBRE (no por índice hardcodeado),
igual que en src/citefid/verify.py. Resultado esperado: ~0.70-0.73
(0.7029 medido con el pipeline de verify.py el 2026-07-16).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ejecutable tanto con `pip install -e .` (citefid instalado) como sin él.
try:
    from citefid.verify import _label_indices, _nli_pair  # type: ignore
    from citefid.retrieve import retrieve_passage  # type: ignore
except ModuleNotFoundError:
    ROOT = Path(__file__).resolve().parent.parent
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    from citefid.verify import _label_indices, _nli_pair  # type: ignore
    from citefid.retrieve import retrieve_passage  # type: ignore

import json

from sentence_transformers import CrossEncoder

NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
DATASET = Path(__file__).parent / "dataset.json"


def _auc(pos: list[float], neg: list[float]) -> float:
    if not pos or not neg:
        return float("nan")
    wins = ties = 0
    for p in pos:
        for n in neg:
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
    return (wins + 0.5 * ties) / (len(pos) * len(neg))


def main() -> int:
    rows = json.loads(DATASET.read_text())
    nli = CrossEncoder(NLI_MODEL, device="cpu")
    idx_ent, idx_con = _label_indices(nli)
    print(f"[label] id2label idx_entail={idx_ent} idx_contra={idx_con}")

    supp = []
    labels = []
    for r in rows:
        passage = retrieve_passage(r["claim"], r["span"])  # keyword, determinista
        ent, con = _nli_pair(nli, passage, r["claim"])
        supp.append(ent - con)
        labels.append(r["label"])

    f = [s for s, lab in zip(supp, labels) if lab == 1]
    i = [s for s, lab in zip(supp, labels) if lab == 0]
    auc = _auc(f, i)
    print(f"\npares: {len(rows)} | fieles: {len(f)} | infieles: {len(i)}")
    print(f"AUC (NLI sobre pasaje recuperado) = {auc:.4f}")
    print(f"   fiel support medio = {sum(f)/len(f):+.4f}")
    print(f"   infiel support medio = {sum(i)/len(i):+.4f}")
    print("\nEste número es el mismo que se cita en README/RESEARCH.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
