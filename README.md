# citefid

[![License: AGPL v3 or later](https://img.shields.io/badge/License-AGPL%20v3--or--later-blue.svg)](LICENSE)

Verificador de **fidelidad de citas** para wikis de conocimiento generados por LLM
que siguen el estándar **OKF (Open Knowledge Format)**. Dado un *claim* y su cita
(rango de líneas pineado a commit, o referencia `^[archivo.md]`), `citefid`
responde si el fragmento fuente **confirma**, **contradice** o es **neutral**
respecto a la afirmación.

## Estado del proyecto

**Fase 1 de 3 — MVP funcional y verificado.** Esto NO es un producto completo:
es la primera fase de un desarrollo por etapas, publicada con sus límites
documentados abiertamente.

- ✅ **Fase 1 (esta):** pipeline determinista `resolve → retrieve → verify` con
  NLI (CPU-only), verificación multi-evidencia y reporte auditable. 17 tests.
- 🔲 **Fase 2:** capa LLM-as-judge para código/CRD y zona gris numérica. **Sin
  validar todavía** — su viabilidad se probará con test honesto antes de activarla.
- 🔲 **Fase 3:** empaquetado completo y CI (en curso).

## Qué hace

- Resuelve una cita a su fragmento fuente:
  - **Código/CRD:** URL `blob/<commit>/<path>#Lx-Ly` → descarga el archivo en ese
    commit y recorta las líneas exactas.
  - **Prosa:** referencia `^[slug.md]` → resuelve por prefijo-hash (el archivo real
    lleva sufijo de hash) exigiendo coincidencia única.
- Recupera el pasaje relevante antes de verificar (keyword + embeddings), saltando
  frontmatter YAML. **Este paso es obligatorio**, no opcional (ver metodología).
- Verifica con NLI (`cross-encoder/nli-deberta-v3-small`) sobre el pasaje
  recuperado, agregando sobre N evidencias (soporte = máx. entail − contra).
- Emite un reporte CSV/JSON **por evidencia**, auditable y determinista.

## Qué NO hace

- **No genera** wikis OKF (eso lo hacen otras herramientas; citefid verifica
  después del build).
- **No resuelve** fuentes externas fuera del bundle citado (web/PDF ajenos).
- **No hace** verificación multi-hop ni razonamiento profundo (MVP: un pasaje por
  cita).

## Resultado medido (con su metodología, sin redondear)

Sobre el terreno **único auditado sin fallos** — código/CRD de un claim-ledger
real (crossplane), con spans recortados a rango de líneas curado:

| Configuración | AUC (fiel vs. infiel) |
|---|---|
| NLI sobre `span[:1500]` | **0.7029** (206 pares: 128 fieles / 78 infieles) |
| NLI sobre pasaje recuperado | 0.7219 (+0.019, dentro del margen de ruido) |

- El AUC se mide como P(soporte de par fiel > soporte de par infiel), scoring por
  nombre de label (contradiction/entailment/neutral resueltos del `id2label` del
  modelo, no por índice hardcodeado).
- **Prosa larga: sin número fiable.** Tres intentos de medición fueron
  invalidados (fragmentos rotos por regex, spans truncados que ocultaban el
  hecho). No se cita un AUC de prosa hasta tener un set con pasaje recuperado.
- El +0.019 del retrieve **no** se vende como mejora demostrada (sin intervalo de
  confianza está en el orden del ruido). Su valor real es cualitativo: no truncar,
  saltar frontmatter, no coger texto irrelevante.

Detalles completos de la investigación en [RESEARCH.md](RESEARCH.md).

## LLM-as-judge (Fase 2, parcial)

`judge.py` aplica un LLM como juez sobre el pasaje recuperado cuando NLI-small
rinde mal (código/CRD) o en zona gris numérica (cambios de cifra que la fuente
no contiene). Emite veredicto estructurado `confirm/refute/unknown + razón`.

- **Sin API key:** degrada a `unknown` ("sin juez") y NO falla (AC-6.4). NLI
  sigue siendo la regla vigente. La key se lee del credentials store
  (`~/.hermes/credentials/platforms.json`, proveedores `cloudfence`/`openai`/
  `anthropic`), nunca hardcodeada.
- **Pendiente de API key:** los AC-6.2 (mejora sobre NLI en código/CRD) y
  AC-6.3 (detección de num_bump en zona gris) requieren una credencial de LLM
  real para medirse. Hasta tenerla, quedan como `skip` explícito en los tests
  — **no se afirma mejora sobre NLI sin haberla medido**.

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requiere Python ≥ 3.12. Modelos CPU-only, sin API key
(`all-MiniLM-L6-v2`, `cross-encoder/nli-deberta-v3-small`).

## Uso (librería)

```python
from citefid.models import Claim, Evidence
from citefid.resolve import resolve_claim
from citefid.verify import verify_claim
from sentence_transformers import CrossEncoder

claim = Claim(text="...", evidences=[Evidence(raw="^[slug.md]")])
resolve_claim(claim, references_dir=...)
nli = CrossEncoder("cross-encoder/nli-deberta-v3-small", device="cpu")
verdict = verify_claim(claim, nli)
print(verdict.veredict, verdict.support, verdict.best_ev)
```

## Tests

```bash
pytest            # 17 tests
```

## Reproducibilidad del AUC

El AUC citado arriba (0.7029 sobre `span[:1500]`, 0.7219 sobre pasaje
recuperado) es **reproducible por cualquiera** — no es un número que haya que
creerse. El dataset de evaluación (206 pares de un claim-ledger real de
crossplane) y el script viven en `evaluation/`:

```bash
pip install -e ".[dev]"
python evaluation/evaluate.py
# AUC (NLI sobre pasaje recuperado) = 0.7219
```

El script usa el mismo pipeline que la librería (label NLI por nombre,
retrieve híbrido) y el mismo dataset que originó el número.

## Licencia

[AGPL-3.0-or-later](LICENSE) — Copyright (C) 2026 Pedro Sordo Martínez
(amurlaniakea@gmail.com).

**Nota AGPL (servicio de red):** la AGPL exige que si este software se ofrece
como servicio de red (no solo como librería/CLI local), los usuarios remotos
puedan acceder al código fuente correspondiente. Hoy citefid es CLI/librería
(y el fuente ya es público en este repo), así que no aplica de forma práctica;
pero si en el futuro se expone como servicio, el README/endpoint debe enlazar
explícitamente a este repositorio como fuente.
