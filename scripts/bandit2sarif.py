#!/usr/bin/env python
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
"""Convierte bandit JSON -> SARIF 2.1.0 (dependency-free).

Uso: python scripts/bandit2sarif.py bandit.json bandit.sarif

bandit -f sarif NO existe en bandit 1.9.x, así que emitimos JSON y convertimos.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("uso: bandit2sarif.py <in.json> <out.sarif>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    data = json.loads(src.read_text())

    results = []
    for issue in data.get("results", []):
        sev = issue.get("issue_severity", "LOW").upper()
        level = {"LOW": "note", "MEDIUM": "warning", "HIGH": "error"}.get(sev, "note")
        fname = issue.get("filename", "")
        line = issue.get("line_number", 1)
        results.append({
            "ruleId": issue.get("test_id", "B000"),
            "level": level,
            "message": {
                "text": f"{issue.get('issue_text', '')} "
                        f"({issue.get('test_name', '')})",
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": fname},
                    "region": {
                        "startLine": line,
                        "endLine": line,
                    },
                },
            }],
        })

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "bandit",
                    "informationUri": "https://bandit.readthedocs.io/",
                    "rules": [{"id": r["ruleId"]} for r in results],
                },
            },
            "results": results,
        }],
    }
    dst.write_text(json.dumps(sarif, indent=1))
    print(f"[bandit2sarif] {len(results)} hallazgos -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
