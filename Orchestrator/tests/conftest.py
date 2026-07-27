import sys
from pathlib import Path

_ORCH = Path(__file__).parent.parent
sys.path.insert(0, str(_ORCH))
sys.path.insert(0, str(_ORCH / 'analysis'))
