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
"""F006 — LLM-as-judge (código/CRD y zona gris numérica).

Aplica un LLM como juez sobre el fragmento fuente recuperado cuando NLI-small
rinde mal (código/CRD) o en zona gris (cambios numéricos que la fuente no
contiene). Emite veredicto estructurado.

AC-6.4 (hard): si no hay API key configurada, degrada a "sin juez" y NO falla.
Los AC-6.2/6.3 (mejora sobre NLI, detección de num_bump) requieren API real y
se miden en tests acotados honestos UNA VEZ haya credencial de LLM; hasta
entonces quedan como skip explícito, sin números fabricados.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .models import Claim, Evidence
from .retrieve import retrieve_passage

# Credenciales: leer del credentials store, NUNCA hardcodeado.
_CRED_PATH = Path.home() / ".hermes" / "credentials" / "platforms.json"


def _load_llm_api_key() -> Optional[str]:
    """Devuelve la api_key de LLM si existe en el credentials store, si no None.

    No lanza nunca: si el archivo o la clave no existen, devuelve None y el
    juez degrada a 'sin juez' (AC-6.4). Las claves válidas conocidas son
    'cloudfence', 'openai', 'anthropic' — se prueban por orden.
    """
    if not _CRED_PATH.exists():
        return None
    try:
        creds = json.loads(_CRED_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    for provider in ("cloudfence", "openai", "anthropic"):
        if provider in creds and isinstance(creds[provider], dict):
            key = creds[provider].get("api_key")
            if key:
                return key
    return None


@dataclass
class JudgeResult:
    """Veredicto estructurado del juez (AC-6.1)."""

    verdict: str  # "confirm" | "refute" | "unknown"
    reason: str
    raw: Optional[str] = None  # respuesta cruda del modelo, si la hubo

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "reason": self.reason}


_PROMPT = """Eres un verificador de fidelidad de citas. Dado un claim y el \
fragmento fuente recuperado, decide si el fragmento CONFIRMA, CONTRADICE o es \
NEUTRAL respecto al claim. En zona gris numérica (el claim cambia una cifra que \
la fuente no contiene), responde refute. Responde SOLO JSON: \
{{"verdict": "confirm"|"refute"|"unknown", "reason": "..."}}.

CLAIM:
__CLAIM__

FRAGMENTO FUENTE:
__SPAN__
"""


def judge_claim(
    claim: Claim, evidences: List[Evidence], api_key: Optional[str] = None
) -> JudgeResult:
    """Aplica LLM-as-judge al claim sobre sus evidencias resueltas.

    Sin api_key (o sin credencial en el store) → degrada a 'sin juez'
    (AC-6.4): devuelve unknown con razón documentada, sin llamar a red.
    """
    key = api_key or _load_llm_api_key()
    if not key:
        return JudgeResult(
            verdict="unknown",
            reason="sin juez (sin API key de LLM configurada; NLI sigue vigente)",
        )

    # Recupera el pasaje relevante del primer span resuelto (mismo que verify).
    spans = [e.span for e in evidences if e.span]
    if not spans:
        return JudgeResult(verdict="unknown", reason="sin juez (ninguna evidencia resuelta)")
    passage = retrieve_passage(claim.text, spans[0])

    # NOTA: la llamada real al proveedor se hace aquí. Sin proveedor
    # instalado/hardcodeado, este punto es donde se invocaría la API. El
    # shape de salida es el JSON del _PROMPT; se parsea abajo.
    raw = _call_llm(_PROMPT.replace("__CLAIM__", claim.text).replace("__SPAN__", passage), key)
    return _parse_judge(raw)


def _call_llm(prompt: str, api_key: str) -> str:
    """Invoca el proveedor de LLM. NUNCA lanza: cualquier fallo degrada a unknown.

    Deja la integración concreta (openai/cloudfence/anthropic) para cuando
    haya credencial y cliente instalado. Cualquier excepción (sin cliente,
    auth inválido, red caída) se captura y devuelve el JSON de fallback
    'sin juez' (AC-6.4: el juez nunca falla, NLI sigue vigente).
    """
    try:
        import openai  # type: ignore
    except ImportError:
        return json.dumps(
            {"verdict": "unknown", "reason": "sin juez (cliente LLM no instalado)"}
        )
    try:
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("CITEFID_JUDGE_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:  # auth inválido, red, rate limit, etc.
        return json.dumps(
            {"verdict": "unknown", "reason": f"sin juez (fallo de API LLM: {type(exc).__name__})"}
        )


def _parse_judge(raw: str) -> JudgeResult:
    """Parsea la salida JSON del juez; tolerante a ruido alrededor del JSON."""
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        obj = json.loads(raw[start:end])
        v = str(obj.get("verdict", "unknown")).lower()
        if v not in ("confirm", "refute", "unknown"):
            v = "unknown"
        return JudgeResult(verdict=v, reason=str(obj.get("reason", "")), raw=raw)
    except (json.JSONDecodeError, ValueError):
        return JudgeResult(verdict="unknown", reason="sin juez (salida no parseable)", raw=raw)
