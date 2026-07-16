# DESIGN NOTES — citefid

Decisiones de diseño explícitas del proyecto. No son coherencias técnicas
implícitas: cada punto es una elección consciente, con su justificación, para
que un auditor futuro no tenga que reconstruirla del código.

## p13 — verify_claim recorre N evidencias desde el inicio

No es afterthought. El claim puede tener varias citas; el veredicto debe
agregar sobre TODAS, no solo la primera. `support = max_i(entail_i − contra_i)`:
se queda con la MEJOR evidencia (criterio optimista). Un parche temprano que
usaba solo `evidences[0]` estaba equivocado y se corrigió.

## p14 — re-medición AUC con label por nombre

El bug de label NLI (índice hardcodeado: `pr[2]` como entail cuando el modelo
lo tenía en `pr[1]`) se cazó en implementación. `verify._label_indices()`
resuelve por nombre del `id2label`. Spike re-medido: AUC 0.7029 (span[:1500]),
0.7219 (pasaje recuperado). El spike usaba resolución por nombre desde el
principio, así que su 0.73 se sostiene.

## p15 — judge_claim agrega multi-evidencia de forma OPUESTA a verify_claim

Decisión deliberada, NO coherencia técnica (corregido tras auditoría en frío):

- `verify_claim` (NLI): `support = max_i(entail_i − contra_i)` → se queda con
  la MEJOR evidencia. Una que apoya fuerte hace `confirm` aunque otra contradiga
  poco. Criterio OPTIMISTA.
- `judge_claim` (LLM): si CUALQUIER evidencia dice `refute`, el veredicto es
  `refute`, aunque el resto confirme. Criterio PESIMISTA ("refute wins").

Justificación: el juez LLM se invoca SOLO en la zona gris / casos dudosos donde
NLI rinde mal (código/CRD, num_bump). En esos casos una sola contradicción
real merece más peso que confirmar por mayoría. No es `max(support)`; es
"una contradicción tira todo abajo". El comentario anterior ("coherente con
verify_claim") era FALSO y se eliminó.

Si en el futuro se quiere igualar el criterio a `max(support)` (optimista), es
una decisión legítima, pero debe ser consciente y anotada aquí, no heredada de
un comentario impreciso.

## p16 — retrieve_passage: fallback a span[:1500] es DEGRADADO

Si `paragraphs(span)` queda vacío (span que es SOLO frontmatter YAML — el caso
que causó el AUC falso de 0.92 en el spike), el fallback devuelve `span[:1500]`.
Ese fallback es degradado: equivale al patrón peligroso que trunca y puede
engañar a NLI. Un span resuelto de verdad rara vez es solo frontmatter; quien
llame debe saber que NO se recuperó un párrafo real. Anotado para Fase 2+.
