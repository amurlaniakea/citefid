"""T008/T009 — verify.py: NLI por evidencia + agregación multi-evidencia.

Usa el fixture de prosa resuelto. Para T008 (AUC 0.726 de crossplane) se
requiere el claim-ledger real; eso se confirma en test aparte con spans
cacheados. Aquí verificamos la dirección (fiel -> entail>contra) y la
agregación (T009).
"""
from pathlib import Path

from sentence_transformers import CrossEncoder

from src.citefid.models import Claim, Evidence
from src.citefid.verify import verify_claim

FIX = Path(__file__).parent / "fixtures"
REF_DIR = FIX / "references"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"


def _claim_prosa():
    span = (REF_DIR / "data-profiling-metric-tables-databricks-on-aws-8eea6c26.md").read_text()
    return Claim(
        text="the profile looks back and the first analysis might include a partial window due to this cutoff",
        evidences=[Evidence(raw="^[data-profiling-metric-tables-databricks-on-aws.md]", span=span, span_kind="doc")],
    )


def test_T008_direccion_nli():
    nli = CrossEncoder(NLI_MODEL, device="cpu")
    c = _claim_prosa()
    v = verify_claim(c, nli)
    assert v.per_ev[0]["entail"] > v.per_ev[0]["contra"], "claim fiel debe dar entail>contra"


def test_T008_corrupto_direccion():
    nli = CrossEncoder(NLI_MODEL, device="cpu")
    c = _claim_prosa()
    c.text = c.text.replace("partial window", "full window")  # corrupto (negación implícita)
    v = verify_claim(c, nli)
    assert v.per_ev[0]["contra"] >= v.per_ev[0]["entail"], "claim corrupto debe dar contra>=entail"


def test_T009_agregacion_multiev():
    nli = CrossEncoder(NLI_MODEL, device="cpu")
    span = (REF_DIR / "data-profiling-metric-tables-databricks-on-aws-8eea6c26.md").read_text()
    paras = [p for p in span.split("\n\n") if len(p.strip()) > 40]
    # ev[0] = TEMA AJENO (crossplane Composition) -> no apoya claim de profiling
    ev0 = (FIX / "crossplane_composition.txt").read_text()
    # ev[1] = párrafo que SÍ contiene "partial window" (apoya el claim)
    ev1 = next(p for p in paras if "partial window" in p)
    c = Claim(
        text="the profile looks back and the first analysis might include a partial window due to this cutoff",
        evidences=[
            Evidence(raw="ev0", span=ev0, span_kind="doc"),
            Evidence(raw="ev1", span=ev1, span_kind="doc"),
        ],
    )
    v = verify_claim(c, nli)
    assert v.best_ev == 1, f"debe elegir ev1 (favorable), eligió {v.best_ev} (per_ev={v.per_ev})"
    assert v.veredict == "confirm", f"veredicto debe ser confirm, fue {v.veredict}"
