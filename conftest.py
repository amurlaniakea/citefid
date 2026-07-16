import sys
from pathlib import Path

# Asegura que 'src/' esté en sys.path para imports absolutos
# `from src.citefid...`, tanto en local como en CI (pytest rootdir-agnostic).
ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
