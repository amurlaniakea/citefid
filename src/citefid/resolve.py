"""F001 — Resolución de citas a fragmentos fuente.

- Código/CRD (crossplane): URL `blob/<commit>/<path>#Lx-Ly` -> descarga el
  archivo en ese commit y recorta las líneas.
- Prosa (databricks-okf): `^[slug.md]` -> el archivo real en `references/`
  lleva sufijo hash; la cita es PREFIJO del nombre real. Resuelve por prefijo,
  exigiendo EXACTAMENTE 1 coincidencia (0 = huérfana, >1 = ambigua).
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

import base64
import re
import subprocess
from pathlib import Path
from typing import Optional

from .models import Evidence

LINE_RE = re.compile(r"#L(\d+)(?:-L?(\d+))?$")
BLOB_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/blob/([0-9a-f]+)/(.+)$")


def _gh_content(path: str) -> Optional[str]:
    """Descarga contenido de un path del repo vía gh api (raw)."""
    cmd = ["gh", "api", f"repos/{path}", "--jq", ".content"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return None
    if not out or out == "null":
        return None
    try:
        return base64.b64decode(out).decode("utf-8", "replace")
    except Exception:
        return None


def _resolve_code(raw: str) -> Evidence:
    m = BLOB_RE.search(raw)
    if not m:
        return Evidence(raw=raw, error="URL no es blob/<commit>/path#Lx-Ly")
    owner, repo, commit, fpath = m.groups()
    lm = LINE_RE.search(raw)
    if lm:
        start, end = int(lm.group(1)), int(lm.group(2) or lm.group(1))
    else:
        start, end = None, None
    content = _gh_content(f"{owner}/{repo}/contents/{fpath}?ref={commit}")
    if content is None:
        return Evidence(raw=raw, error="no se pudo descargar el archivo")
    lines = content.splitlines()
    if start is None:
        return Evidence(raw=raw, resolved_path=fpath, span=content, span_kind="doc")
    # líneas 1-indexed -> 0-indexed
    lo = max(0, start - 1)
    # Clamping explícito: hi en [lo, len(lines)] para que el slice nunca se
    # invierta ni se salga de rango. Python ya clampa el slice, pero lo hacemos
    # explícito para que el analizador estático no infiera condiciones always-true.
    hi = min(end, len(lines)) if end is not None else len(lines)
    hi = max(hi, lo)
    # NOSONAR S2583: falso positivo confirmado. El slice lines[lo:hi] es siempre
    # válido (Python clampa el índice); un span vacío es correcto para rango inválido.
    span = "\n".join(lines[lo:hi])
    return Evidence(raw=raw, resolved_path=fpath, span=span, span_kind="lines")


def _resolve_prosa(raw: str, references_dir: Optional[Path] = None) -> Evidence:
    """raw tipo `^[slug.md]` o `slug.md`. El archivo real lleva sufijo hash."""
    slug = raw.strip().lstrip("^[").rstrip("]")
    if slug.endswith(".md"):
        base = slug[:-3]
    else:
        base = slug
    if references_dir and references_dir.exists():
        cands = [p.name for p in references_dir.glob("*.md")
                 if p.name.rsplit("/", 1)[-1].startswith(base + "-")]
    else:
        cands = []
    if len(cands) == 0:
        return Evidence(raw=raw, error=f"cita huérfana: {slug} no resuelve")
    if len(cands) > 1:
        return Evidence(raw=raw, error=f"prefijo ambiguo ({len(cands)} coincidencias): {slug}")
    fname = cands[0]
    content = _gh_content(f"claudiobottari/databricks-okf/contents/references/{fname}")
    if content is None:
        # fallback: leer de caché local si existe
        cache = references_dir / fname if references_dir else None
        content = cache.read_text() if cache and cache.exists() else None
    if content is None:
        return Evidence(raw=raw, error=f"no se pudo descargar referencia {fname}")
    return Evidence(raw=raw, resolved_path=fname, span=content, span_kind="doc")


def resolve_citation(raw: str, references_dir: Optional[Path] = None) -> Evidence:
    """Resuelve una cita (código o prosa) a su Evidence."""
    if "blob/" in raw and "#L" in raw:
        return _resolve_code(raw)
    if raw.strip().startswith("^["):
        return _resolve_prosa(raw, references_dir)
    # intenta como prosa por defecto
    return _resolve_prosa(raw, references_dir)


def resolve_claim(claim, references_dir: Optional[Path] = None):
    """Resuelve TODAS las evidencias de un Claim (no solo la primera)."""
    from .models import Claim
    if isinstance(claim, str):
        claim = Claim(text=claim, evidences=[Evidence(raw=claim)])
    for ev in claim.evidences:
        if not ev.span:  # no re-resolver si ya está poblado
            ev2 = resolve_citation(ev.raw, references_dir)
            ev.resolved_path = ev2.resolved_path
            ev.span = ev2.span
            ev.span_kind = ev2.span_kind
            ev.error = ev2.error
    return claim
