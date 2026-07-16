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
"""F007 — Test acotado de LLM-as-judge (honesto, igual que el spike).

Principios del spike (sil-repo-standards 71): datos reales, corruptor de
claims, sin fabricar números. AC-6.2/6.3 requieren API key de LLM → se
dejan como skip explícito hasta que haya credencial, SIN números inventados.
"""
from pathlib import Path

import pytest

from src.citefid.judge import JudgeResult, _parse_judge, judge_claim
from src.citefid.models import Claim, Evidence

FIX = Path(__file__).parent / "fixtures"


def _claim_fixture():
    span = (FIX / "crossplane_composition.txt").read_text()
    ev = Evidence(raw="^[crossplane_composition.txt]", span=span)
    return Claim(text="Crossplane compone recursos mediante Compositions.", evidences=[ev])


def test_ac61_judge_schema(monkeypatch):
    """AC-6.1: el veredicto es estructurado (verdict en {confirm,refute,unknown}, reason str)."""
    jr = JudgeResult(verdict="confirm", reason="el fragmento lo dice")
    assert jr.verdict in ("confirm", "refute", "unknown")
    assert isinstance(jr.reason, str)
    assert jr.to_dict()["verdict"] == "confirm"


def test_ac61_parse_real_output():
    """AC-6.1: _parse_judge tolera ruido alrededor del JSON y normaliza el verdict."""
    raw = '```json\n{"verdict": "refute", "reason": "cifra distinta"}\n```'
    jr = _parse_judge(raw)
    assert jr.verdict == "refute"
    assert "cifra" in jr.reason


def test_ac64_no_api_key_fallback(monkeypatch):
    """AC-6.4: sin API key el juez degrada a 'sin juez' y NO falla."""
    monkeypatch.setattr("src.citefid.judge._load_llm_api_key", lambda: None)
    claim = _claim_fixture()
    jr = judge_claim(claim, claim.evidences)
    assert jr.verdict == "unknown"
    assert "sin juez" in jr.reason
    assert jr.raw is None


def test_ac64_no_llm_client_fallback(monkeypatch):
    """AC-6.4: con key pero sin cliente LLM instalado, degrada a unknown (no crash)."""
    monkeypatch.setattr("src.citefid.judge._load_llm_api_key", lambda: "dummy-key")
    # Simula que el cliente LLM no está disponible (sin llamar a red).
    monkeypatch.setattr(
        "src.citefid.judge._call_llm",
        lambda prompt, key: '{"verdict": "unknown", "reason": "sin juez (cliente LLM no instalado)"}',
    )
    claim = _claim_fixture()
    jr = judge_claim(claim, claim.evidences)
    assert jr.verdict == "unknown"
    assert "cliente LLM no instalado" in jr.reason


@pytest.mark.skip(
    reason="AC-6.2/6.3: requieren API key de LLM (no disponible en credentials store). "
    "Medición honesta pendiente de credencial — NO se afirma mejora sobre NLI sin esto."
)
def test_ac62_judge_beats_nli_on_code():
    """AC-6.2: sobre código/CRD, el juez mejora o iguala a NLI (misma muestra que F004)."""
    raise NotImplementedError("pendiente de API key de LLM")


@pytest.mark.skip(
    reason="AC-6.3: requiere API key de LLM para detectar num_bump en zona gris."
)
def test_ac63_numeric_gray_zone():
    """AC-6.3: detecta cambio de cifra cuando la fuente lo contiene."""
    raise NotImplementedError("pendiente de API key de LLM")
