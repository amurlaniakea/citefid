"""F003/F004 — verify_claim: NLI por evidencia + agregación multi-evidencia.

Para cada evidencia resuelta: NLI(párrafo recuperado, claim) ->
[contradict, neutral, entail]. Agrega: support_i = entail_i - contra_i;
best_ev = argmax_i support_i; support = support[best_ev].
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np

from .models import Claim, Verdict
from .retrieve import retrieve_passage


def _label_indices(nli):
    """Resuelve (idx_entail, idx_contra) por NOMBRE de label, no hardcodeado.

    Robusto ante cualquier modelo NLI (lección Fase 5: hardcodear el índice
    causó leer 'neutral' como 'entailment').
    """
    id2label = getattr(getattr(nli, "model", nli), "config", None)
    id2label = getattr(id2label, "id2label", {0: "contradiction", 1: "entailment", 2: "neutral"})
    idx_ent = next(i for i, v in id2label.items() if "entail" in v.lower())
    idx_con = next(i for i, v in id2label.items() if "contrad" in v.lower())
    return idx_ent, idx_con


def _nli_pair(nli, premise: str, hypothesis: str) -> tuple[float, float]:
    """Devuelve (entail, contra) del cross-encoder NLI (índices por nombre)."""
    idx_ent, idx_con = _label_indices(nli)
    logits = nli.predict([(premise[:1500], hypothesis[:500])], show_progress_bar=False)
    pr = np.exp(logits[0] - np.max(logits[0]))
    pr = pr / pr.sum()
    return float(pr[idx_ent]), float(pr[idx_con])


def verify_claim(claim: Claim, nli, retrieve_model=None) -> Verdict:
    """Verifica un claim contra todas sus evidencias (no solo la primera)."""
    per_ev: List[dict] = []
    for i, ev in enumerate(claim.evidences):
        if not ev.span or ev.error:
            per_ev.append({"ev": i, "error": ev.error or "sin span",
                           "entail": 0.0, "contra": 0.0, "support": 0.0})
            continue
        premise = retrieve_passage(claim.text, ev.span, retrieve_model)
        entail, contra = _nli_pair(nli, premise, claim.text)
        support = entail - contra
        per_ev.append({"ev": i, "entail": round(entail, 4),
                       "contra": round(contra, 4), "support": round(support, 4)})
    # agregación: max support (la evidencia que más apoya)
    valid = [p for p in per_ev if "error" not in p]
    if valid:
        best = max(valid, key=lambda p: p["support"])
        best_ev = best["ev"]
        support = best["support"]
        veredict = "confirm" if support > 0 else ("refute" if support < 0 else "neutral")
    else:
        best_ev = -1
        support = 0.0
        veredict = "neutral"
    return Verdict(claim=claim.text, per_ev=per_ev, best_ev=best_ev,
                   support=round(support, 4), veredict=veredict)
