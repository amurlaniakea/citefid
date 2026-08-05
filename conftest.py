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
import sys
from pathlib import Path

# Asegura que 'src/' esté en sys.path para imports absolutos
# `from src.citefid...`, tanto en local como en CI (pytest rootdir-agnostic).
ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
