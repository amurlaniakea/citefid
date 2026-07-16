"""F002 — Passage-retrieval híbrido (keyword + embeddings).

Localiza el párrafo del span donde el claim podría confirmarse/refutarse.
Híbrido: keyword primero (tokens no-stopword del claim), embeddings (MiniLM)
como tie-break. NUNCA devuelve span[:1500] como premise.
"""
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
    """Recupera el párrafo relevante. keyword primero, embeddings como tie-break."""
    paras = paragraphs(span)
    if not paras:
        return span[:1500]  # doc muy corto: usa todo, marcado en caller
    ki = retrieve_keyword(claim, paras)
    if ki is not None:
        return paras[ki]  # keyword desempató
    if model is not None:
        return paras[retrieve_embeddings(claim, paras, model)]
    # sin modelo ni keyword: primer párrafo (fallback explícito, no span[:1500] ciego)
    return paras[0]
