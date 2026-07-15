"""Modelos de datos de citefid — ÚNICA fuente de verdad.

verify.py y report.py importan desde aquí; NO se redefine Claim/Evidence/
Verdict en otro módulo (lección Centinela: dataclass duplicado = bug silencioso).
"""
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
