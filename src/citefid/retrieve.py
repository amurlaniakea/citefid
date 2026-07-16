"""F002 — Passage-retrieval híbrido (keyword + embeddings).

Localiza el párrafo del span donde el claim podría confirmarse/refutarse.
Híbrido: keyword primero (tokens no-stopword del claim), embeddings (MiniLM)
como tie-break. NUNCA devuelve span[:1500] como premise.
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

import re
from typing import List, Optional

import numpy as np

_STOP = set("el la los las de y a en con por para que se su una un es son "
            "the a an and or to of in with for that is are on as by from at it "
            "this these those que which who what when where how why not no".split())


def paragraphs(text: str) -> List[str]:
    # descartar frontmatter YAML (bloque ---...--- al inicio) y líneas key: value
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    raw = [p.strip() for p in re.split(r"\n\s*\n", text)]
    out = []
    for p in raw:
        # saltar párrafos que son solo metadatos (title:/source:/etc.)
        lines = [ln for ln in p.splitlines() if ln.strip()]
        if not lines:
            continue
        if all(re.match(r"^[A-Za-z_-]+:", ln) for ln in lines[:3]):
            continue  # bloque de metadatos, no contenido
        if len(p) > 40:
            out.append(p)
    return out


def _keywords(claim: str) -> List[str]:
    toks = re.findall(r"[a-zA-Z0-9_]+", claim.lower())
    return [t for t in toks if t not in _STOP and len(t) > 2]


def retrieve_keyword(claim: str, paras: List[str]) -> Optional[int]:
    """Devuelve el índice del párrafo que contiene TODOS los keywords, o None."""
    kws = _keywords(claim)
    if not kws:
        return None
    # score = suma de longitudes de keywords presentes (tokens largos = más
    # distintivos). Desempata por el keyword más largo presente.
    best, best_score, best_maxkw = None, -1, -1
    for i, p in enumerate(paras):
        pl = p.lower()
        present = [k for k in kws if k in pl]
        if not present:
            continue
        score = sum(len(k) for k in present)
        maxkw = max(len(k) for k in present)
        if score > best_score or (score == best_score and maxkw > best_maxkw):
            best, best_score, best_maxkw = i, score, maxkw
    return best if best_score > 0 else None


def retrieve_embeddings(claim: str, paras: List[str], model) -> int:
    ce = model.encode([claim], normalize_embeddings=True)[0]
    pe = model.encode(paras, normalize_embeddings=True)
    return int(np.argmax(pe @ ce))


def retrieve_passage(claim: str, span: str, model=None) -> str:
    """Recupera el párrafo relevante. keyword primero, embeddings como tie-break.

    NOTA (robustez, Fase 2): si `paragraphs(span)` queda vacío (span que es
    SOLO frontmatter YAML, el caso que causó el AUC falso de 0.92 en el
    spike), el fallback devuelve `span[:1500]`. Ese fallback es DEGRADADO:
    equivale al patrón peligroso que trunca y puede engañar a NLI. Un span
    resuelto de verdad rara vez es solo frontmatter, pero quien llame a esta
    función debe saber que NO se recuperó un párrafo real en ese caso.
    """
    paras = paragraphs(span)
    if not paras:
        # FALLBACK DEGRADADO: span sin párrafos útiles (p.ej. solo frontmatter).
        # No se recuperó pasaje real; NLI sobre esto puede dar score engañoso.
        return span[:1500]
    ki = retrieve_keyword(claim, paras)
    if ki is not None:
        return paras[ki]  # keyword desempató
    if model is not None:
        return paras[retrieve_embeddings(claim, paras, model)]
    # sin modelo ni keyword: primer párrafo (fallback explícito, no span[:1500] ciego)
    return paras[0]
