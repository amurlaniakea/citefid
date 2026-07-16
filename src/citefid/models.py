"""Modelos de datos de citefid — ÚNICA fuente de verdad.

verify.py y report.py importan desde aquí; NO se redefine Claim/Evidence/
Verdict en otro módulo (lección Centinela: dataclass duplicado = bug silencioso).
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

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Evidence:
    """Una cita resuelta a su fragmento fuente."""

    raw: str
    resolved_path: Optional[str] = None
    span: str = ""
    span_kind: str = "doc"  # "lines" | "doc" | "paragraph"
    error: Optional[str] = None  # mensaje si no se pudo resolver


@dataclass
class Claim:
    """Un claim con N evidencias (no solo la primera)."""

    text: str
    evidences: list[Evidence] = field(default_factory=list)


@dataclass
class Verdict:
    """Veredicto de verify_claim sobre un Claim."""

    claim: str
    per_ev: list[dict] = field(default_factory=list)  # score NLI por evidencia
    best_ev: int = -1  # índice de la evidencia que más apoya al claim
    support: float = 0.0  # max_i (entail_i - contra_i)
    veredict: str = "neutral"  # confirm | refute | neutral
