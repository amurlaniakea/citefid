# RESEARCH — citefid

Registro honesto de la investigación que fundamenta citefid. Documenta lo que
funcionó, lo que **no**, y por qué. Los números vienen con su metodología; lo no
medido de forma fiable se dice como tal, no se rellena.

## Problema

Los generadores de wikis OKF (Open Knowledge Format) comprueban que el archivo
citado *existe*, pero **no** que su contenido respalde la afirmación. La
literatura documenta el hueco: citas que apuntan a fuentes que no confirman el
claim (CiteCheck; "Cited but Not Verified"; grounding engañoso). citefid cierra
esa brecha: verifica *fidelidad*, no *existencia*.

## Tesis

La verificación de fidelidad es un problema de **NLI sobre el pasaje correcto**,
no de similitud semántica. La parte difícil no es el modelo: es **recuperar el
fragmento fuente relevante** antes de verificar.

## Hallazgos (spike, auditado)

### 1. Embeddings solos NO discriminan fidelidad
Similitud por embeddings (all-MiniLM-L6-v2) entre claim y span dio AUC ~0.49–0.54
(fiel vs. infiel) — indistinguible del azar. Un claim corrupto sigue siendo
semánticamente parecido a su fuente. La similitud mide *tema*, no *veracidad*.

### 2. NLI SÍ discrimina, pero con techo
`cross-encoder/nli-deberta-v3-small` (CPU, sin API key) sobre pares claim+span de
código/CRD real: **AUC ~0.70–0.73**. Señal real, reproducible, pero lejos de un
clasificador fuerte. Es un techo del modelo pequeño, no un bug (ver §Metodología).

### 3. La recuperación de pasaje es requisito DURO, no opcional
El fallo más instructivo: NLI sobre el documento entero truncado a 1500 chars dio
un AUC engañoso de 0.92 en prosa — **artefacto**. El hecho real estaba más allá
del carácter 1500; el modelo solo veía el frontmatter y "confirmaba" por contexto
temático. Sin recuperar el pasaje correcto, cualquier número de prosa es humo.
De aquí sale el diseño: `retrieve` (keyword + embeddings, saltando frontmatter)
es un paso obligatorio ANTES de NLI.

### 4. Prosa larga: sin número fiable (y se dice así)
Tres intentos de medir AUC sobre prosa fueron invalidados por defectos de
construcción del dataset (fragmentos partidos por regex, spans truncados que
ocultaban el hecho, solapamiento de fuentes). **No se publica un AUC de prosa.**
La honestidad sobre lo no medido es parte del entregable.

### 5. Bug de label cazado en implementación
Al portar NLI de spike a librería, la primera versión de `verify.py` asumió el
orden `[contradiction, neutral, entailment]` y leyó `pr[2]` como entailment —
pero el `id2label` real del modelo es `{0: contradiction, 1: entailment,
2: neutral}`. Síntoma que lo delató: un span de tema TOTALMENTE ajeno daba
entail 0.9954 (imposible). Corregido a resolución de índice **por nombre de
label** (robusto ante cualquier modelo). El spike ya lo hacía por nombre, por eso
su AUC 0.7029 era correcto; se re-midió con el código nuevo y reprodujo 0.7029.

## Metodología

- **AUC** = P(soporte(par fiel) > soporte(par infiel)), soporte = entail − contra.
- **Labels** resueltos leyendo `model.config.id2label` por nombre, nunca por
  índice hardcodeado.
- **Pares infieles** generados por corrupción controlada de claims fieles
  (negación, cambio numérico, sustitución de entidad).
- **Terreno medido:** claim-ledger real de un repo OKF de código/CRD (crossplane),
  206 pares (128 fieles / 78 infieles), spans recortados a rango de líneas.
- **CPU-only**, sin API key: `all-MiniLM-L6-v2`, `cross-encoder/nli-deberta-v3-small`.
- Cada corrida emite CSV/JSON crudo por-evidencia (auditable por terceros).

## Límites conocidos

- NLI-small tiene techo ~0.73 en código/CRD; no distingue bien "documento trata
  del tema" de "este pasaje confirma este claim específico".
- Prosa larga sin AUC fiable (ver hallazgo 4).
- La mejora del retrieve (+0.019) está en el orden del ruido sin intervalo de
  confianza; se justifica cualitativamente, no como número.
- Fase 2 (LLM-as-judge) puede subir el techo, pero está **sin validar**.

## Trabajo futuro

- Fase 2: LLM-as-judge para código/CRD y zona gris numérica, con test acotado
  honesto (separando consistencia interna de validez externa) antes de activarla.
- Set de prosa con pasaje recuperado para obtener por fin un AUC de prosa fiable.
- Intervalos de confianza por bootstrap sobre el AUC.

## Referencias

- CiteCheck — verificación de citas en texto generado.
- "Cited but Not Verified" — fuentes citadas que no respaldan la afirmación.
- Deceptive / faulty grounding en generación aumentada por recuperación.
