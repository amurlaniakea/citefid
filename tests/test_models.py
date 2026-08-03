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
